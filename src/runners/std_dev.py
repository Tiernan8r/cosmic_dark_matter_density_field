import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from typing import List

import numpy as np
from src.calc import std_dev
from src.plotting import Plotter
from src.util import enum, orchestrator


class StdDevRunner(orchestrator.Orchestrator):

    def __init__(self, args: List[str]):
        super().__init__(args)
        self.fig = None

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." + StdDevRunner.__name__ + "." + self.tasks.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        sd = std_dev.StandardDeviation(
            self, self.type, self.sim_name)
        masses, sigmas = sd.masses_sigmas(
            hf, from_fit=self.config.sampling.std_dev_from_fit)
        radii = self.config.radii

        r = []
        m = []
        y = []
        for i in range(len(masses)):
            s = sigmas[i]

            if s is None:
                continue

            m.append(masses[i])
            r.append(radii[i])
            y.append(s*s)

        logger.debug(f"Plotting std devs...")

        plotter = Plotter(self, self.type, self.sim_name)

        # Plot the standalone std dev
        plotter.std_dev_func_R(
            z, r, y, self.sim_name, logscale=True)
        # Add it to the composite plot

        if self.fig is None:
            self.fig = {}
        if self.type not in self.fig:
            self.fig[self.type] = None

        self.fig[self.type] = plotter.std_dev_func_R(
            z, r, y, self.sim_name, logscale=True, fig=self.fig[self.type])

        # self.fig = plotter.std_dev_func_M(
        #     z, m, y, self.sim_name, logscale=True, fig=self.fig)

        self.fig_save_dir = plotter.std_dev_dir(self.sim_name)

    def run(self):
        super().run()
        logger = logging.getLogger(__name__ + "." + self.run.__name__)

        if self.fig is None:
            logger.info("No figs to extrapolated onto!")
            return

        for tp in enum.DataType:

            if not self.config.datatypes.__getattribute__(tp.value):
                logger.info(f"Skipping running on {tp.value}...")
                continue

            self.type = tp

            if self.fig.get(tp) is not None:
                logger.info("Showing extrapolated std dev on plot...")

                # Extraplote the z=10 to z=0 for all radii
                sd = std_dev.StandardDeviation(self, self.type, self.sim_name)

                from_z = self.config.from_z
                to_z = self.config.to_z

                stds = sd.extrapolated(from_z, to_z)

                R = np.array(self.config.radii)

                # rb0 = sd.rho_bar_0()
                # Vs = 4/3 * np.pi * R**3
                # Ms = Vs * rb0

                fig = self.fig.get(tp)
                ax = fig.gca()

                # ax.plot(Ms, extrap_stds**2, linestyle="dashed",
                #         label="extrapolated z=10 to z=0")
                ax.plot(R, stds**2, linestyle="dashed",
                        label=f"extrapolated z={from_z} to z={to_z}")

                ax.legend()

                plot_fname = os.path.join(
                    self.fig_save_dir, self.config.plotting.pattern.std_dev_compared)
                logger.debug(f"Saving compared std devs plot to: {plot_fname}")

                fig.savefig(plot_fname)

            logger.info("DONE")


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
