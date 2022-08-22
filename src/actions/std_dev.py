#!/usr/bin/env python3
import logging
import logging.config

import yt
from src.actions.base import BaseAction
from src.calc import std_dev


class StdDevActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(
            __name__ + "." + self.actions.__name__)

        sd = std_dev.StandardDeviation(
            self, self.type, self.sim_name)

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(self.config.radii):

            # =================================================================
            # STANDARD DEVIATION
            # =================================================================
            if self.config.tasks.std_dev:
                logger.info("Working on standard deviation")

                sd.std_dev(hf, radius)

            else:
                logger.info("Skipping calculating standard deviations...")
