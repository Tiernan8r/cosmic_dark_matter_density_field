#!/usr/bin/env python3
import logging
import logging.config

import src.util.units as u
from src.actions.base import BaseAction
from src.calc import mass_function, overdensity, press_schechter, rho_bar
from src.fitting import fits
from src.plotting import Plotter


class PressSchechterActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(__name__ + "." + self.actions.__name__)

        mf = mass_function.MassFunction(self, self.type, self.sim_name)
        ods = overdensity.Overdensity(self, self.type, self.sim_name)
        ps = press_schechter.PressSchechter(self, self.type, self.sim_name)
        rb = rho_bar.RhoBar(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        logger.debug("Calculating total halo mass function")
        # =================================================================
        # TOTAL MASS FUNCTION
        # =================================================================
        if self.config.tasks.total_mass_function:
            logger.info("Calculating total mass function...")

            total_hist, total_bins = mf.total_mass_function(hf)
            if total_hist is not None and total_bins is not None:
                plotter.total_mass_function(
                    z, total_hist, total_bins, self.sim_name)

        else:
            logger.info("Skipping calculating total mass function...")

        logger.debug("Calculating press schechter mass function")
        # =================================================================
        # PRESS SCHECHTER MASS FUNCTION
        # =================================================================
        if self.config.tasks.press_schechter_mass_function:
            logger.info("Calculating press schechter mass function...")

            masses, ps_fit = ps.mass_function(hf)
            ps_fit = ps_fit.to(1 / u.volume(ds))
            if ps_fit is not None and masses is not None:
                plotter.press_schechter(
                    z, ps_fit, masses, self.sim_name)

        else:
            logger.info(
                "Skipping calculating press schechter mass function...")

        # =============================================================
        # PRESS SCHECHTER - TOTAL COMPARISON
        # =============================================================
        if self.config.tasks.total_mass_function and self.config.tasks.press_schechter_mass_function:
            logger.info("Plotting PS - total mass function comparison...")

            all_mass = mf.cache_total_mass_function(hf)

            plotter.press_schechter_comparison(
                z, masses, all_mass, ps_fit, self.sim_name)

        else:
            logger.info("Skipping comparing mass function plots...")

        # # =============================================================
        # # NUMERICAL MASS FUNCTIONS
        # # =============================================================
        # if self.config.tasks.numerical_mass_function:
        #     logger.info("Plotting numerical mass function...")

        #     avg_den = rb.rho_bar(hf)
        #     num_bins = self.config.sampling.num_hist_bins

        #     for func_name, fitting_func in fitter.fit_functions().items():
        #         logger.info(f"Plotting '{func_name}'")

        #         # Track all the fitted functions over radii
        #         all_fits = []
        #         # Track the histogram bins used over radii (may be the same??)
        #         all_bins = []
        #         # Track the overdensities histograms across radii
        #         all_deltas = []

        #         # Set the fitting function to use
        #         plotter.func = fitting_func
        #         # Track the fitting parameters across radii
        #         func_params = []

        #         # Iterate over the radii
        #         radii = self.config.radii
        #         for radius in radii:

        #             # Calculate the overdensities at this sampling radius
        #             od = ods.calc_overdensities(hf, radius)

        #             # Get the fitting parameters to this overdensity
        #             fitter.setup_parameters(func_name)
        #             bin_centres, f, r2, popt = fitter.calc_fit(
        #                 z, radius, od, num_bins)

        #             # Track the values
        #             all_fits.append(f)
        #             all_bins.append(bin_centres)
        #             # Track the fitting parameters
        #             func_params.append(popt)

        #             # Convert the overdensities to a histogram
        #             hist, bin_edges = mass_function.create_histogram(
        #                 od, bins=num_bins)
        #             # Track the hist
        #             all_deltas.append(hist)

        #         # Calculate the numerical mass function for this fit model
        #         numerical_mass_function = ps.numerical_mass_function(
        #             avg_den, radii, masses, fitting_func, func_params)
        #         # Plot the mass function
        #         plotter.numerical_mass_function(
        #             z, numerical_mass_function, masses, self.sim_name, func_name)
        # else:
        #     logger.info("Skipping calculating numerical mass functions...")
