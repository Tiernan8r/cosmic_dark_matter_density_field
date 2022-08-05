#!/usr/bin/env python3
import logging
import logging.config

import yt
from src.actions.base import BaseAction
from src.calc import mass_function
from src.fitting import fits
from src.plotting import Plotter


class MassFunctionActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(
            __name__ + "." + self.actions.__name__)

        mf = mass_function.MassFunction(self, self.type, self.sim_name)
        plotter = Plotter(self, self.type, self.sim_name)
        fitter = fits.Fits(self, self.type, self.sim_name)

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

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(self.config.radii):

            # =================================================================
            # MASS FUNCTION:
            # =================================================================
            if self.config.tasks.mass_function:
                logger.info("Working on mass function:")

                mass_hist, bin_edges = mf.mass_function(hf, radius)

                plotter.mass_function(
                    z, radius, mass_hist, bin_edges, self.sim_name)

            else:
                logger.info("Skipping calculating mass function...")
