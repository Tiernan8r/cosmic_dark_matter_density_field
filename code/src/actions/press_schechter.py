#!/usr/bin/env python3
import logging
import logging.config

import yt
from src.actions.base import BaseAction


class PressSchechterActions(BaseAction):

    def actions(self, hf: str):
        super().actions(hf)
        logger = logging.getLogger(__name__ + "." + self.actions.__name__)

        # Iterate over the radii to sample for
        for radius in yt.parallel_objects(self.config.radii):

            # =================================================
            # PRESS SCHECHTER FITS
            # =================================================
            continue
