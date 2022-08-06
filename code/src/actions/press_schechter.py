#!/usr/bin/env python3
import logging
import logging.config

import src.util.units as u
from src.actions.base import BaseAction
from src.calc import mass_function, press_schechter
from src.plotting import Plotter


class PressSchechterActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(__name__ + "." + self.actions.__name__)

        mf = mass_function.MassFunction(self, self.type, self.sim_name)
        ps = press_schechter.PressSchechter(self, self.type, self.sim_name)
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
