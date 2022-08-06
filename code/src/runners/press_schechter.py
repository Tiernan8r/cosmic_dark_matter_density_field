#!/usr/bin/env python3
import logging
import logging.config
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import yt
from src.calc import (mass_function, overdensity, press_schechter, rho_bar,
                      std_dev)
from src.fitting import fits
from src.plotting import Plotter
from src.util import enum, orchestrator
from src.util.halos import halo_finder


class PressSchechterRunner(orchestrator.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." +
            PressSchechterRunner.__name__ + "." +
            self.tasks.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift
        logger.info(f"Redshift is: {z}")

        radii = self.config.radii

        rb = rho_bar.RhoBar(self, self.type, self.sim_name)
        ps = press_schechter.PressSchechter(self, self.type, self.sim_name)
        ods = overdensity.Overdensity(self, self.type, self.sim_name)
        sd = std_dev.StandardDeviation(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)

        num_bins = self.config.sampling.num_hist_bins

        z = ds.current_redshift
        avg_den = rb.rho_bar(hf)

        # =============================================================
        # PRESS SCHECHTER STANDALONE
        # =============================================================
        masses, sigmas = sd.masses_sigmas(hf)
        ps_mass_function = ps.analytic_press_schechter(avg_den, masses, sigmas)
        plotter.press_schechter(z, ps_mass_function,
                                masses, self.sim_name)

        for func_name, fitting_func in fitter.fit_functions().items():
            # Track all the fitted functions over radii
            all_fits = []
            # Track the histogram bins used over radii (may be the same??)
            all_bins = []
            # Track the overdensities histograms across radii
            all_deltas = []

            # Set the fitting function to use
            plotter.func = fitting_func
            # Track the fitting parameters across radii
            func_params = []

            # Iterate over the radii
            for radius in radii:

                # Calculate the overdensities at this sampling radius
                od = ods.calc_overdensities(hf, radius)

                # Get the fitting parameters to this overdensity
                fitter.setup_parameters(func_name)
                bin_centres, f, r2, popt = fitter.calc_fit(
                    z, radius, od, num_bins)

                # Track the values
                all_fits.append(f)
                all_bins.append(bin_centres)
                # Track the fitting parameters
                func_params.append(popt)

                # Convert the overdensities to a histogram
                hist, bin_edges = mass_function.create_histogram(
                    od, bins=num_bins)
                # Track the hist
                all_deltas.append(hist)

            # Calculate the numerical mass function for this fit model
            numerical_mass_function = ps.numerical_mass_function(
                avg_den, radii, masses, fitting_func, func_params)
            # Plot the mass function
            plotter.numerical_mass_function(
                z, numerical_mass_function, masses, self.sim_name, func_name)

        self.dataset_cache.clear()
        self.cache.reset()

    def run(self):
        # super().run()

        logger = logging.getLogger(__name__ + "." + self.run.__name__)

        logger.info("Calculating comparison mass functions to PS:")

        for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

            # Save the current sim name into the data object
            self.sim_name = sim_name

            logger.info(f"Working on simulation: {self.sim_name}")
            for tp in yt.parallel_objects(enum.DataType):
                self.type = tp

                logger.info(f"Working on {tp.value} datasets:")

                # Skip dataset type calculation if not set to run in the config
                type_name = tp.value
                if not self.config.datatypes.__getattribute__(type_name):
                    logger.info("Skipping...")
                    continue

                if type_name == enum.DataType.SNAPSHOT.value:
                    logger.info("Skipping running on SNAPSHOTS...")
                    continue
                self.type = tp

                # =============================================================
                # COMPARE PS MASS FN TO TOTAL MASS FN
                # =============================================================

                mf = mass_function.MassFunction(self, self.type, self.sim_name)
                sd = std_dev.StandardDeviation(self, self.type, self.sim_name)
                ps = press_schechter.PressSchechter(
                    self, self.type, self.sim_name)
                rb = rho_bar.RhoBar(self, self.type, self.sim_name)
                plotter = Plotter(self, self.type, self.sim_name)

                zs = self.config.redshifts

                halos_finder = halo_finder.HalosFinder(
                    tp, self.config.sim_data.root, self.sim_name)
                halo_files = halos_finder.filter_data_files(zs)
                snapshots_finder = halo_finder.HalosFinder(
                    enum.DataType.SNAPSHOT, self.config.sim_data.root, self.sim_name)
                snapshot_files = snapshots_finder.filter_data_files(zs)

                for hf, sf in zip(halo_files, snapshot_files):
                    ds = self.dataset_cache.load(hf)

                    z = ds.current_redshift
                    avg_den = rb.rho_bar(hf)

                    all_mass = mf.cache_total_mass_function(hf)
                    masses, sigmas = sd.masses_sigmas(sf)

                    ps_mass_function = ps.analytic_press_schechter(
                        avg_den, masses, sigmas)

                    plotter.press_schechter_comparison(
                        z, masses, all_mass, ps_mass_function, self.sim_name)

                    self.dataset_cache.clear()


def main(args):
    ps_runner = PressSchechterRunner(args)
    ps_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
