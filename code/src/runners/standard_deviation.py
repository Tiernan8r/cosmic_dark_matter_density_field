import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import yt
from src import runner
from src.calc.standard_deviation import StandardDeviation
from src.plot import plotting


class StdDevRunner(runner.Runner):

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

        plotter.std_dev(z, self._conf.radii, std_devs, self._data.sim_name)


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
