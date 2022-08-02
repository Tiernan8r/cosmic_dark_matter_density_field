import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import yt
from src import data, enum, runner
from src.calc.standard_deviation import StandardDeviation
from src.plot import plotting
from src.util import halo_finder


class StdDevRunner(runner.Runner):

    def run(self):
        yt.enable_parallelism()
        if not yt.is_root():
            return

        logger = logging.getLogger(self.run.__name__)

        # Iterate over the simulations
        for sim_name in yt.parallel_objects(self._conf.sim_data.simulation_names):

            # Save the current sim name into the data object
            self._data.sim_name = sim_name

            logger.info(f"Working on simulation: {self._data.sim_name}")

            # Find halos for data set
            zs = self._conf.redshifts
            logger.debug(
                f"Filtering halo files to look for redshifts: {zs}")

            for tp in yt.parallel_objects(enum.DataType):
                self._type = tp

                logger.info(f"Working on {tp} datasets:")

                # Skip dataset type calculation if not set to run in the config
                type_name = tp.value
                if not self._conf.datatypes.__getattribute__(type_name):
                    logger.info("Skipping...")
                    continue

                halos_finder = halo_finder.HalosFinder(
                    halo_type=tp, root=self._conf.sim_data.root, sim_name=sim_name)
                halo_files = halos_finder.filter_data_files(zs)

                n_hfs = len(halo_files)
                logger.debug(
                    f"Found {n_hfs} halo files that match these redshifts")

                for r in self._conf.radii:
                    logger.debug(
                        f"Calculating standard deviation across redshift for radius = {r}")
                    self.std_dev_work(r, zs, halo_files)

        super().run()

    def std_dev_work(self, radius: float, redshifts, hfs):
        logger = logging.getLogger(
            __name__ + "." + StdDevRunner.__name__ + "." + self.tasks.__name__)

        std_devs = []
        std_dev = StandardDeviation(self._data, type=self._type)

        for hf in hfs:
            ds = self._ds_cache.load(hf)
            z = ds.current_redshift

            logger.debug(f"Calculating std dev at redshift '{z}'")

            sdev = std_dev.std_dev(hf, radius)

            std_devs.append(sdev)

        logger.debug(f"Plotting std devs...")

        plotter = plotting.Plotter(self._data, self._type)

        plotter.std_dev_func_z(
            radius, redshifts, std_devs, self._data.sim_name)

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

        x = []
        y = []
        for i in range(len(radii)):
            s = std_devs[i]

            if s is None:
                continue

            x.append(radii[i])
            y.append(s*s)

        plotter.std_dev_func_R(z, x, y, self._data.sim_name, logscale=True)


def main(args):
    std_dev_runner = StdDevRunner(args)
    std_dev_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
