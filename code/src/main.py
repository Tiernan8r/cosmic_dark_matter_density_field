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

from src import action
from src.calc import mass_function, overdensity, rho_bar, standard_deviation
from src.fitting import fits
from src.plotting import Plotter


class MainRunner(action.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(self.tasks.__name__)

        logger.debug(f"Working on halo file '{hf}'")

        logger.debug("Calculating total halo mass function")

        mf = mass_function.MassFunction(self, type=self.type)
        rb = rho_bar.RhoBar(self, type=self.type)
        od = overdensity.Overdensity(self, type=self.type)
        sd = standard_deviation.StandardDeviation(self, type=self.type)
        plotter = Plotter(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift
        # =================================================================
        # TOTAL MASS FUNCTION
        # =================================================================
        if self.config.tasks.total_mass_function:
            logger.info("Calculating total mass function...")

            try:
                total_hist, total_bins = mf.total_mass_function(hf)
                if total_hist is not None and total_bins is not None:
                    fitter.total_mass_function(
                        z, total_hist, total_bins, self.sim_name)
            except Exception as e:
                logger.error(e)
        else:
            logger.info("Skipping calculating total mass function...")

        # =================================================================
        # RHO BAR
        # =================================================================
        if self.config.tasks.rho_bar:
            logger.info("Calculating rho bar...")
            try:
                rb.rho_bar(hf)
            except Exception as e:
                logger.error(e)
        else:
            logger.info("Skipping calculating rho bar...")

        # Get the number of samples needed
        num_sphere_samples = self.config.sampling.num_sp_samples

        radii = self.config.radii
        self.config.min_radius = min(radii)
        self.config.max_radius = max(radii)
        logger.debug(f"Maximum radius is: {self.config.max_radius}")

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(radii):

            # Use the number of samples required to converge in new calculation
            # if we don't want to override the old values
            num = mf.get_num_samples(hf, radius, z)
            logger.debug(
                f"Overdensity calculation scheduled? {self.config.tasks.overdensity}")
            if num is not None and not self.config.tasks.overdensity:
                logger.debug(
                    f"Setting sample size from convergence cache to {num} instead of {num_sphere_samples}")
                self.config.sampling.num_sp_samples = num
                num_sphere_samples = num

            logger.debug(
                f"Calculating overdensities and halo mass functions at a radius of '{radius}'")  # noqa: E501
            logger.debug(
                f"Initially sampling with {num_sphere_samples} sphere samples")

            # =================================================================
            # OVERDENSITIES:
            # =================================================================
            if self.config.tasks.overdensity:
                logger.info("Working on overdensities:")

                try:
                    deltas = od.calc_overdensities(hf, radius)

                    # Truncate the lists to the desired number of values
                    # if there are too many
                    deltas = deltas[:num_sphere_samples]

                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping calculating overdensities...")

            # =========================================================
            # STANDALONE OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                try:
                    logger.debug("Plotting standalone overdensity...")
                    # Standalone overdensity plot
                    plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins)

                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping plotting overdensities...")

            # =========================================================
            # FITTED GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                try:
                    logger.debug("Plotting fitted Gaussian to overdensity...")
                    # Fitted with Gaussian:
                    fig = plotter.new_figure()
                    fig = plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig)
                    fig, gauss_popt = plotter.gaussian_fit(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig)

                    gaussian_fit_fname = fitter.gaussian_fit_fname(
                        self.sim_name, radius, z)
                    fig.savefig(gaussian_fit_fname)

                except Exception as e:
                    logger.error(e)
            else:
                logger.info(
                    "Skipping plotting fitted gaussian to overdensities...")

            # =========================================================
            # SKEWED GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                try:
                    logger.debug("Plotting skewed Gaussian to overdensity...")
                    # Fitted with Skewed Gaussian:
                    fig = plotter.new_figure()
                    fig = plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig)
                    fig, sk_gauss_popt = plotter.skewed_gaussian_fit(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig)

                    skewed_gaussian_fit_fname = fitter.skewed_gaussian_fit_fname(
                        self.sim_name, radius, z)
                    fig.savefig(skewed_gaussian_fit_fname)

                except Exception as e:
                    logger.error(e)
            else:
                logger.info(
                    "Skipping plotting skewed gaussian to overdensities...")

            # =========================================================
            # N GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                try:
                    logger.debug("Plotting N-Gaussian to overdensity...")
                    # Fitted with N Gaussian:
                    fig = plotter.new_figure()
                    fig = plotter.overdensities(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig)
                    fig, n_popt = plotter.n_gaussian_fit(
                        z,
                        radius,
                        deltas,
                        self.sim_name,
                        self.config.sampling.num_hist_bins,
                        fig=fig,
                        num_fits=self.config.plotting.fitting.num_n_gaussian_fits)

                    n_gaussian_fit_fname = fitter.n_gaussian_fit_fname(
                        self.sim_name, radius, z)
                    fig.savefig(n_gaussian_fit_fname)

                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping plotting n gaussian to overdensities...")

            # =================================================
            # PRESS SCHECHTER FITS
            # =================================================

            # =================================================================
            # STANDARD DEVIATION
            # =================================================================
            if self.config.tasks.std_dev:
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
            if self.config.tasks.mass_function:
                logger.info("Working on mass function:")
                try:
                    mass_hist, bin_edges = mf.mass_function(hf, radius)

                    plotter.mass_function(
                        z, radius, mass_hist, bin_edges, self.sim_name)
                except Exception as e:
                    logger.error(e)
            else:
                logger.info("Skipping calculating mass function...")


def main(args):
    action = MainRunner(args)
    action.run()


if __name__ == "__main__":
    if yt.is_root():
        # Drop the program name from the sys.args
        main(sys.argv[1:])
