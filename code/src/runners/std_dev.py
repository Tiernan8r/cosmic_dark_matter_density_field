import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import src.units as u
import yt
from src import action
from src.calc import rho_bar
from src.calc.standard_deviation import StandardDeviation
from src.plotting import master


class StdDevRunner(action.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." + StdDevRunner.__name__ + "." + self.tasks.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        masses, sigmas = self.masses_sigmas(hf)

        x = []
        y = []
        for i in range(len(masses)):
            s = sigmas[i]

            if s is None:
                continue

            x.append(masses[i])
            y.append(s*s)

        logger.debug(f"Plotting std devs...")

        plotter = master.Plotter(self, self.type)

        plotter.std_dev_func_M(z, x, y, self.sim_name, logscale=True)

    def masses_sigmas(self, hf):
        logger = logging.getLogger(
            __name__ + "." + StdDevRunner.__name__ + "." + self.masses_sigmas.__name__)

        ds = self.dataset_cache.load(hf)

        std_dev = StandardDeviation(self, type=self.type)

        sigmas = []

        radii = self.config.radii
        logger.debug(f"Creating std devs for radii '{radii}'")

        for radius in yt.parallel_objects(radii):
            sdev = std_dev.std_dev(hf, radius)

            sigmas.append(sdev)

        rb = rho_bar.RhoBar(self, self.type)
        av_den = rb.rho_bar(hf)

        masses = []
        for r in radii:
            R = ds.quan(r, u.length_cm(ds))

            V = 4 / 3 * np.pi * R**3
            m = av_den * V

            masses.append(m)

        return ds.arr(masses, u.mass(ds)), np.abs(sigmas)


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
