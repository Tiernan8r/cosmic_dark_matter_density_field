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

from src.actions import (mass_function, overdensity, press_schechter, rho_bar,
                         std_dev)
from src.util import orchestrator


class MainRunner(orchestrator.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(self.tasks.__name__)
        logger.info("Running tasks...")

        rb_actions = rho_bar.RhoBarActions(self, self.type, self.sim_name)
        std_dev_actions = std_dev.StdDevActions(
            self, self.type, self.sim_name)
        od_actions = overdensity.OverdensityActions(
            self, self.type, self.sim_name)
        mass_fn_actions = mass_function.MassFunctionActions(
            self, self.type, self.sim_name)
        ps_actions = press_schechter.PressSchechterActions(
            self, self.type, self.sim_name)

        rb_actions.actions(hf)
        std_dev_actions.actions(hf)
        od_actions.actions(hf)
        mass_fn_actions.actions(hf)
        ps_actions.actions(hf)


def main(args):
    action = MainRunner(args)
    action.run()


if __name__ == "__main__":
    if yt.is_root():
        # Drop the program name from the sys.args
        main(sys.argv[1:])
