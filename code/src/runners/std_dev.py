import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import yt
from src import enum, action
from src.calc.standard_deviation import StandardDeviation
from src.plot import plotting
from src.util import halo_finder
from src.calc import rho_bar
import src.units as u

class StdDevRunner(action.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." + StdDevRunner.__name__ + "." + self.tasks.__name__)

        ds = self._ds_cache.load(hf)
        z = ds.current_redshift

        std_dev = StandardDeviation(self._data, type=self._type)

        std_devs = []

        logger.debug(f"Creating std devs for radii '{self._conf.radii}'")

        for radius in yt.parallel_objects(self._conf.radii):
            sdev = std_dev.std_dev(hf, radius)

            std_devs.append(sdev)

        logger.debug(f"Plotting std devs...")

        plotter = plotting.Plotter(self._data, self._type)

        radii = self._conf.radii

        rb = rho_bar.RhoBar(self._data, self._type)
        av_den = rb.rho_bar(hf)

        masses = []
        for r in radii:
            R = ds.quan(r, u.length_cm(ds))

            V = 4 /3 * np.pi * R**3
            m = av_den * V

            masses.append(m)

        x = []
        y = []
        for i in range(len(radii)):
            s = std_devs[i]

            if s is None:
                continue

            x.append(masses[i])
            y.append(s*s)

        plotter.std_dev_func_M(z, x, y, self._data.sim_name, logscale=True)


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
