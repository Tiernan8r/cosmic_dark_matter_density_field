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
from src.util import units as u


class PressSchechterRunner(orchestrator.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." +
            PressSchechterRunner.__name__ + "." +
            self.tasks.__name__)

        if self.type.value == enum.DataType.H5.value:
            logger.info("Skipping running on HALOS_H5...")
            return

        self._task_press_schechter_mass_function(hf)
        self._task_numerical_mass_function(hf)

        self.dataset_cache.clear()
        self.cache.reset()

    def _task_press_schechter_mass_function(self, hf):
        logger = logging.getLogger(
            __name__ + "." + self._task_press_schechter_mass_function.__name__)

        # =================================================================
        # PRESS SCHECHTER MASS FUNCTION
        # =================================================================
        ps = press_schechter.PressSchechter(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)

        if self.config.tasks.press_schechter_mass_function:
            logger.info("Calculating press schechter mass function...")

            ds = self.dataset_cache.load(hf)
            z = ds.current_redshift

            masses, ps_fit = ps.mass_function(hf)
            ps_fit = ps_fit.to(1 / u.volume(ds))
            if ps_fit is not None and masses is not None:
                plotter.press_schechter(
                    z, ps_fit, masses, self.sim_name)

        else:
            logger.info(
                "Skipping calculating press schechter mass function...")

    def _task_numerical_mass_function(self, hf):
        logger = logging.getLogger(
            __name__ + "." + self._task_numerical_mass_function.__name__)

        # ===========================================================
        # NUMERICAL MASS FUNCTIONS
        # =============================================================
        rb = rho_bar.RhoBar(self, self.type, self.sim_name)
        sd = std_dev.StandardDeviation(self, self.type, self.sim_name)
        ps = press_schechter.PressSchechter(self, self.type, self.sim_name)
        ods = overdensity.Overdensity(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)

        if self.config.tasks.numerical_mass_function:
            logger.info("Plotting numerical mass function...")

            ds = self.dataset_cache.load(hf)
            z = ds.current_redshift

            avg_den = rb.rho_bar(hf)
            num_bins = self.config.sampling.num_hist_bins

            masses, _ = sd.masses_sigmas(hf)

            for func_name, fitting_func in fitter.fit_functions().items():
                logger.info(f"Plotting '{func_name}'")

                # Set the fitting function to use
                plotter.func = fitting_func
                # Track the fitting parameters across radii
                func_params = []

                # Iterate over the radii
                radii = self.config.radii
                for radius in radii:

                    # Calculate the overdensities at this sampling radius
                    od = ods.calc_overdensities(hf, radius)

                    # Get the fitting parameters to this overdensity
                    fitter.setup_parameters(func_name)
                    _, _, _, popt = fitter.calc_fit(
                        z, radius, od, num_bins)

                    # Track the fitting parameters
                    func_params.append(popt)

                # Calculate the numerical mass function for this fit model
                numerical_mass_function = ps.numerical_mass_function(
                    avg_den, radii, masses, fitting_func, func_params)
                # Plot the mass function
                plotter.numerical_mass_function(
                    z, numerical_mass_function, masses, self.sim_name, func_name)
        else:
            logger.info("Skipping calculating numerical mass functions...")

    def run(self):
        super().run()

        logger = logging.getLogger(__name__ + "." + self.run.__name__)

        self._run_press_schechter_total_comparison()
        self._run_press_schechter_analytic()
        self._run_press_schechter_numeric()
        self._run_total_numeric()

        self.dataset_cache.clear()

        logger.info("DONE")

    def _run_press_schechter_total_comparison(self):
        logger = logging.getLogger(
            __name__ + "." + self._run_press_schechter_total_comparison.__name__)

        # =============================================================
        # PRESS SCHECHTER - TOTAL COMPARISON
        # =============================================================
        if self.config.tasks.total_mass_function and self.config.tasks.press_schechter_mass_function:
            logger.info("Calculating comparison total mass functions to PS:")

            for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

                # Save the current sim name into the data object
                self.sim_name = sim_name

                logger.info(f"Working on simulation: {self.sim_name}")
                # =============================================================
                # COMPARE PS MASS FN TO TOTAL MASS FN
                # =============================================================

                mf = mass_function.MassFunction(
                    self, enum.DataType.H5, self.sim_name)
                sd = std_dev.StandardDeviation(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                ps = press_schechter.PressSchechter(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                rb = rho_bar.RhoBar(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                plotter = Plotter(self, enum.DataType.H5, self.sim_name)

                zs = self.config.redshifts

                halos_finder = halo_finder.HalosFinder(
                    enum.DataType.H5, self.config.sim_data.root, self.sim_name)
                halo_files = halos_finder.filter_data_files(zs)
                snapshots_finder = halo_finder.HalosFinder(
                    enum.DataType.SNAPSHOT, self.config.sim_data.root, self.sim_name)
                snapshot_files = snapshots_finder.filter_data_files(zs)

                for hf, sf in zip(halo_files, snapshot_files):
                    ds = self.dataset_cache.load(sf)

                    z = ds.current_redshift
                    avg_den = rb.rho_bar(sf)

                    total_mass_hist, total_mass_bins = mf.total_mass_function(
                        hf)
                    masses, sigmas = sd.masses_sigmas(sf)

                    ps_mass_function = ps.analytic_press_schechter(
                        avg_den, masses, sigmas)

                    plotter.press_schechter_total_comparison(
                        z, total_mass_bins, total_mass_hist, masses, ps_mass_function, self.sim_name)

        else:
            logger.info(
                "Skipping comparing total mass function plots...")

    def _run_press_schechter_analytic(self):
        logger = logging.getLogger(
            __name__ + "." + self._run_press_schechter_analytic.__name__)
        # =============================================================
        # PRESS SCHECHTER - ANALYTIC
        # =============================================================
        if self.config.tasks.mass_function and self.config.tasks.press_schechter_mass_function:
            logger.info("Calculating comparison mass functions to PS:")

            for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

                # Save the current sim name into the data object
                self.sim_name = sim_name

                logger.info(f"Working on simulation: {self.sim_name}")
                # =============================================================
                # COMPARE PS MASS FN TO ANALYTIC MASS FN
                # =============================================================
                mf = mass_function.MassFunction(
                    self, enum.DataType.H5, self.sim_name)
                rb = rho_bar.RhoBar(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                sd = std_dev.StandardDeviation(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                ps = press_schechter.PressSchechter(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                plotter = Plotter(self, enum.DataType.H5, self.sim_name)

                zs = self.config.redshifts

                halos_finder = halo_finder.HalosFinder(
                    enum.DataType.H5, self.config.sim_data.root, self.sim_name)
                halo_files = halos_finder.filter_data_files(zs)
                snapshots_finder = halo_finder.HalosFinder(
                    enum.DataType.SNAPSHOT, self.config.sim_data.root, self.sim_name)
                snapshot_files = snapshots_finder.filter_data_files(zs)

                for hf, sf in zip(halo_files, snapshot_files):
                    ds = self.dataset_cache.load(sf)
                    z = ds.current_redshift

                    masses, sigmas = sd.masses_sigmas(sf)
                    avg_den = rb.rho_bar(sf)

                    ps_mass_function = ps.analytic_press_schechter(
                        avg_den, masses, sigmas)

                    for radius in self.config.radii:
                        logger.info(
                            f"Working on mass function: r={radius}")

                        mass_hist, bin_edges = mf.mass_function(hf, radius)

                        plotter.press_schechter_analytic_comparison(
                            z, radius, bin_edges, mass_hist, masses, ps_mass_function, self.sim_name)

        else:
            logger.info("Skipping comparing analytic mass function plots...")

    def _run_press_schechter_numeric(self):
        logger = logging.getLogger(
            __name__ + "." + self._run_press_schechter_numeric.__name__)
        # =============================================================
        # PRESS SCHECHTER - NUMERIC
        # =============================================================
        if self.config.tasks.numerical_mass_function and self.config.tasks.press_schechter_mass_function:
            logger.info(
                "Calculating comparison numerical mass functions to PS:")

            for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

                # Save the current sim name into the data object
                self.sim_name = sim_name

                # =============================================================
                # COMPARE PS MASS FN TO NUMERICAL MASS FN
                # =============================================================
                ods = overdensity.Overdensity(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                sd = std_dev.StandardDeviation(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                ps = press_schechter.PressSchechter(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                rb = rho_bar.RhoBar(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                plotter = Plotter(self, enum.DataType.SNAPSHOT, self.sim_name)
                fitter = fits.Fits(self, enum.DataType.SNAPSHOT, self.sim_name)

                zs = self.config.redshifts

                snapshots_finder = halo_finder.HalosFinder(
                    enum.DataType.SNAPSHOT, self.config.sim_data.root, self.sim_name)
                snapshot_files = snapshots_finder.filter_data_files(zs)

                for sf in snapshot_files:
                    ds = self.dataset_cache.load(sf)
                    z = ds.current_redshift

                    # ===========================================================
                    # NUMERICAL MASS FUNCTIONS
                    # =============================================================
                    logger.info("Plotting numerical mass function...")

                    avg_den = rb.rho_bar(sf)
                    num_bins = self.config.sampling.num_hist_bins

                    # Get the PS mass function
                    masses, sigmas = sd.masses_sigmas(sf)

                    ps_mass_function = ps.analytic_press_schechter(
                        avg_den, masses, sigmas)

                    for func_name, fitting_func in fitter.fit_functions().items():
                        logger.info(f"Plotting '{func_name}'")

                        # Set the fitting function to use
                        plotter.func = fitting_func
                        # Track the fitting parameters across radii
                        func_params = []

                        # Iterate over the radii
                        radii = self.config.radii
                        for radius in radii:

                            # Calculate the overdensities at this sampling radius
                            od = ods.calc_overdensities(sf, radius)

                            # Get the fitting parameters to this overdensity
                            fitter.setup_parameters(func_name)
                            _, _, _, popt = fitter.calc_fit(
                                z, radius, od, num_bins)

                            # Track the fitting parameters
                            func_params.append(popt)

                        # Calculate the numerical mass function for this fit model
                        numerical_mass_function = ps.numerical_mass_function(
                            avg_den, radii, masses, fitting_func, func_params)
                        # Plot the mass function
                        plotter.press_schechter_numerical_comparison(
                            z, masses, numerical_mass_function, ps_mass_function, self.sim_name, fitting_func.__name__)

        else:
            logger.info("Skipping comparing numerical mass function plots...")

    def _run_total_numeric(self):
        logger = logging.getLogger(
            __name__ + "." + self._run_total_numeric.__name__)
        # =============================================================
        # TOTAL - NUMERIC
        # =============================================================
        if self.config.tasks.numerical_mass_function and self.config.tasks.total_mass_function:
            logger.info(
                "Calculating comparison numerical mass functions to total:")

            for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

                # Save the current sim name into the data object
                self.sim_name = sim_name

                logger.info(f"Working on simulation: {self.sim_name}")
                # =============================================================
                # COMPARE TOTAL MASS FN TO NUMERICAL MASS FN
                # =============================================================
                mf = mass_function.MassFunction(
                    self, enum.DataType.H5, self.sim_name)
                ods = overdensity.Overdensity(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                sd = std_dev.StandardDeviation(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                ps = press_schechter.PressSchechter(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                rb = rho_bar.RhoBar(
                    self, enum.DataType.SNAPSHOT, self.sim_name)
                plotter = Plotter(self, enum.DataType.SNAPSHOT, self.sim_name)
                fitter = fits.Fits(self, enum.DataType.SNAPSHOT, self.sim_name)

                zs = self.config.redshifts

                halos_finder = halo_finder.HalosFinder(
                    enum.DataType.H5, self.config.sim_data.root, self.sim_name)
                halo_files = halos_finder.filter_data_files(zs)
                snapshots_finder = halo_finder.HalosFinder(
                    enum.DataType.SNAPSHOT, self.config.sim_data.root, self.sim_name)
                snapshot_files = snapshots_finder.filter_data_files(zs)

                for hf, sf in zip(halo_files, snapshot_files):
                    ds = self.dataset_cache.load(sf)
                    z = ds.current_redshift

                    # ===========================================================
                    # NUMERICAL MASS FUNCTIONS
                    # =============================================================
                    logger.info("Plotting numerical mass function...")

                    avg_den = rb.rho_bar(sf)
                    num_bins = self.config.sampling.num_hist_bins

                    # Total mass
                    total_hist, total_bins = mf.total_mass_function(hf)

                    # Get the PS mass function
                    masses, _ = sd.masses_sigmas(sf)

                    for func_name, fitting_func in fitter.fit_functions().items():
                        logger.info(f"Plotting '{func_name}'")

                        # Set the fitting function to use
                        plotter.func = fitting_func
                        # Track the fitting parameters across radii
                        func_params = []

                        # Iterate over the radii
                        radii = self.config.radii
                        for radius in radii:

                            # Calculate the overdensities at this sampling radius
                            od = ods.calc_overdensities(sf, radius)

                            # Get the fitting parameters to this overdensity
                            fitter.setup_parameters(func_name)
                            _, _, _, popt = fitter.calc_fit(
                                z, radius, od, num_bins)

                            # Track the fitting parameters
                            func_params.append(popt)

                        # Calculate the numerical mass function for this fit model
                        numerical_mass_function = ps.numerical_mass_function(
                            avg_den, radii, masses, fitting_func, func_params)
                        # Compare to total mass function
                        plotter.total_to_numerical_comparison(
                            z, total_bins, total_hist, masses, numerical_mass_function, self.sim_name, fitting_func.__name__)

        else:
            logger.info(
                "Skipping comparing numerical mass function to total plots...")


def main(args):
    ps_runner = PressSchechterRunner(args)
    ps_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
