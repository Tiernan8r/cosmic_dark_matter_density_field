#!/usr/bin/env python3
import logging
import logging.config

import yt
from src.actions.base import BaseAction
from src.calc import overdensity, std_dev
from src.fitting import fits
from src.plotting import Plotter


class OverdensityActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(
            __name__ + "." + self.actions.__name__)

        od = overdensity.Overdensity(self, self.type, self.sim_name)
        sd = std_dev.StandardDeviation(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type, self.sim_name)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # Get the number of samples needed
        num_sphere_samples = self.config.sampling.num_sp_samples

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(self.config.radii):

            # Use the number of samples required to converge in new calculation
            # if we don't want to override the old values
            num = od.get_num_samples(hf, radius, z)
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

                deltas = od.calc_overdensities(hf, radius)

                # Truncate the lists to the desired number of values
                # if there are too many
                deltas = deltas[:num_sphere_samples]

            else:
                logger.info("Skipping calculating overdensities...")

            # =========================================================
            # STANDALONE OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                logger.debug("Plotting standalone overdensity...")

                # Standalone overdensity plot
                plotter.overdensities(
                    z,
                    radius,
                    deltas,
                    self.sim_name,
                    self.config.sampling.num_hist_bins)

            else:
                logger.info("Skipping plotting overdensities...")

            # =========================================================
            # FITTED GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
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
                # Gaussian fit
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

            else:
                logger.info(
                    "Skipping plotting fitted gaussian to overdensities...")

            # =========================================================
            # FITTED GAUSSIAN + EXTRAPOLATED OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
                logger.debug(
                    "Plotting extrapolated Gaussian to overdensity...")

                # Fitted with Gaussian:
                fig = plotter.new_figure()
                fig = plotter.overdensities(
                    z,
                    radius,
                    deltas,
                    self.sim_name,
                    self.config.sampling.num_hist_bins,
                    fig=fig)

                # Extrapolated
                A, mu, sigma = gauss_popt
                extrapolated_sigma = sd.extrapolate(10, z, radius)

                fig = plotter.gaussian(
                    A, mu, extrapolated_sigma, self.config.sampling.num_hist_bins, fig=fig)

                # Gaussian fit
                fig, gauss_popt = plotter.gaussian_fit(
                    z,
                    radius,
                    deltas,
                    self.sim_name,
                    self.config.sampling.num_hist_bins,
                    fig=fig)

                extrapolated_fit_fname = fitter.extrapolated_gaussian_fit_fname(
                    self.sim_name, radius, z)
                fig.savefig(extrapolated_fit_fname)

            else:
                logger.info(
                    "Skipping plotting fitted gaussian to overdensities...")

            # =========================================================
            # SKEWED GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
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

            else:
                logger.info(
                    "Skipping plotting skewed gaussian to overdensities...")

            # =========================================================
            # N GAUSSIAN OVERDENSITY PLOT:
            # =========================================================
            if self.config.tasks.overdensity:
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

            else:
                logger.info("Skipping plotting n gaussian to overdensities...")
