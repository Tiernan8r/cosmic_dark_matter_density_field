#!/usr/bin/env python3
import logging
import logging.config

from src.actions.base import BaseAction
from src.calc import rho_bar


class RhoBarActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(
            __name__ + "." + self.actions.__name__)

        rb = rho_bar.RhoBar(self, self.type, self.sim_name)

        # =================================================================
        # RHO BAR
        # =================================================================
        if self.config.tasks.rho_bar:
            logger.info("Calculating rho bar...")

            rb.rho_bar(hf)

        else:
            logger.info("Skipping calculating rho bar...")
