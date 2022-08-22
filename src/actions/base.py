#!/usr/bin/env python3
import logging
import logging.config

from src.util import interface


class BaseAction(interface.Interface):

    def actions(self, hf: str):
        logger = logging.getLogger(__name__ + "." + self.actions.__name__)

        logger.debug(f"Working on halo file '{hf}'")

