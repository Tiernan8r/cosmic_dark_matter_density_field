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

from src import runner
from src import units as u
from src.calc import mass_function, overdensity, rho_bar, standard_deviation
from src.plot import fits


class MainRunner(runner.Runner):

    def tasks(self, hf: str):
        logger = logging.getLogger(self.tasks.__name__)

        logger.debug(f"Working on halo file '{hf}'")

        logger.debug("Calculating total halo mass function")

        mf = mass_function.MassFunction(self._data, type=self._type)
        rb = rho_bar.RhoBar(self._data, type=self._type)
        od = overdensity.Overdensity(self._data, type=self._type)
        sd = standard_deviation.StandardDeviation(self._data, type=self._type)
        plotter = fits.Fits(self._data, self._type)

        ds = self._ds_cache.load(hf)
        z = ds.current_redshift
        # =================================================================
        # TOTAL MASS FUNCTION
        # =================================================================
        if self._conf.tasks.total_mass_function:
            logger.info("Calculating total mass function...")

            min_particle_mass = self._ds_cache.min_mass(
                hf, mass_units=u.mass(ds))

            try:
                total_hist, total_bins = mf.total_mass_function(hf)
                if total_hist is not None and total_bins is not None:
                    plotter.total_mass_function(
                        z, total_hist, total_bins, self._data.sim_name, min_particle_mass)
            except Exception as e:
                logger.error(e)
        else:
            logger.info("Skipping calculating total mass function...")

        # =================================================================
        # RHO BAR
        # =================================================================
        if self._conf.tasks.rho_bar:
            logger.info("Calculating rho bar...")
            try:
                rb.rho_bar(hf)
            except Exception as e:
                logger.error(e)
        else:
            logger.info("Skipping calculating rho bar...")

        # Get the number of samples needed
        num_sphere_samples = self._conf.sampling.num_sp_samples

        radii = self._conf.radii
        self._conf.min_radius = min(radii)
        self._conf.max_radius = max(radii)
        logger.debug(f"Maximum radius is: {self._conf.max_radius}")

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(radii):

            # Use the number of samples required to converge in new calculation
            # if we don't want to override the old values
            num = mf.get_num_samples(hf, radius, z)
            logger.debug(
                f"Overdensity calculation scheduled? {self._conf.tasks.overdensity}")
            if num is not None and not self._conf.tasks.overdensity:
                logger.debug(
                    f"Setting sample size from convergence cache to {num} instead of {num_sphere_samples}")
                self._conf.sampling.num_sp_samples = num
                num_sphere_samples = num

            logger.debug(
                f"Calculating overdensities and halo mass functions at a radius of '{radius}'")  # noqa: E501
            logger.debug(
                f"Initially sampling with {num_sphere_samples} sphere samples")

            # =================================================================
            # OVERDENSITIES:
            # =================================================================
            if self._conf.tasks.overdensity:
                logger.info("Working on overdensities:")

                try:
                    deltas = od.calc_overdensities(hf, radius)

                    # Truncate the lists to the desired number of values
                    # if there are too many
                    deltas = deltas[:num_sphere_samples]

                    logger.debug("Generating plots for this data...")

                    # Standalone overdensity plot
                    plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self._data.sim_name,
                        self._conf.sampling.num_od_hist_bins)

                    # Fitted with Gaussian:
                    fig = plotter.new_figure()
                    fig = plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self._data.sim_name,
                        self._conf.sampling.num_od_hist_bins,
                        fig=fig)
                    fig = plotter.gaussian_fit(
                        z,
                        radius,
                        deltas,
                        self._data.sim_name,
                        self._conf.sampling.num_od_hist_bins,
                        fig=fig)

                    gaussian_fit_fname = plotter.gaussian_fit_fname(
                        self._data.sim_name, radius, z)
                    fig.savefig(gaussian_fit_fname)

                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping calculating overdensities...")

            # =================================================================
            # STANDARD DEVIATION
            # =================================================================
            if self._conf.tasks.std_dev:
                logger.info("Working on standard deviation")
                try:
                    sd.std_dev(hf, radius)
                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping calculating standard deviations...")

            # =================================================================
            # MASS FUNCTION:
            # =================================================================
            if self._conf.tasks.mass_function:
                logger.info("Working on mass function:")
                try:
                    mass_hist, bin_edges = mf.mass_function(hf, radius)
                    min_particle_mass = self._ds_cache.min_mass(
                        hf, mass_units=u.mass(ds))

                    plotter.mass_function(
                        z, radius, mass_hist, bin_edges, self._data.sim_name, min_particle_mass)
                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping calculating mass function...")


def main(args):
    runner = MainRunner(args)
    runner.run()


if __name__ == "__main__":
    if yt.is_root():
        # Drop the program name from the sys.args
        main(sys.argv[1:])
