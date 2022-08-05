import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src.calc import std_dev
from src.plotting import Plotter
from src.util import orchestrator
from typing import List
import numpy as np


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

        x = []
        y = []
        for i in range(len(masses)):
            s = sigmas[i]

            if s is None:
                continue

            x.append(masses[i])
            y.append(s*s)

        logger.debug(f"Plotting std devs...")

        plotter = Plotter(self, self.type, self.sim_name)

        plotter.std_dev_func_M(z, x, y, self.sim_name, logscale=True)

        self.fig = plotter.std_dev_func_M(
            z, x, y, self.sim_name, logscale=True, fig=self.fig)

        self.fig_save_dir = plotter.std_dev_dir(self.sim_name)

    def run(self):
        super().run()

        if self.fig is not None:

            # Extraplote the z=10 to z=0 for all radii
            sd = std_dev.StandardDeviation(self, self.type, self.sim_name)

            stds = []

            R = np.array(self.config.radii)
            for r in R:
                extrap_std = sd.extrapolate(10, 0, r)
                stds.append(extrap_std)

            rb0 = sd.rho_bar_0()
            Vs = 4/3 * np.pi * R**3
            Ms = Vs * rb0

            extrap_stds = np.array(stds)

            ax = self.fig.gca()

            ax.plot(Ms, extrap_stds**2, linestyle="dashed",
                    label="extrapolated z=10 to z=0")

            ax.legend()

            plot_fname = os.path.join(
                self.fig_save_dir, self.config.plotting.pattern.std_dev_compared)

            self.fig.savefig(plot_fname)


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
