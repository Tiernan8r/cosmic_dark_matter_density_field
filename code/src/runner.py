import logging
from typing import List

import yt

from src import enum
from src.init import setup
from src.util import halo_finder


class Runner:

    def __init__(self, args: List[str]):
        self._data = setup.setup(args)
        self._conf = self._data.config
        self._cache = self._data.cache
        self._ds_cache = self._data.dataset_cache
        self._type = enum.DataType.ROCKSTAR

    def run(self):
        if not yt.is_root():
            return

        logger = logging.getLogger(self.run.__name__)

        # Iterate over the simulations
        for sim_name in self._conf.sim_data.simulation_names:

            # Save the current sim name into the data object
            self._data.sim_name = sim_name

            logger.info(f"Working on simulation: {self._data.sim_name}")

            # Find halos for data set
            zs = self._conf.redshifts
            logger.debug(
                f"Filtering halo files to look for redshifts: {zs}")

            for tp in enum.DataType:
                self._type = tp

                halos_finder = halo_finder.HalosFinder(
                    halo_type=tp, root=self._conf.sim_data.root, sim_name=sim_name)
                halo_files = halos_finder.filter_data_files(zs, tolerance=1e-1)

                n_hfs = len(halo_files)
                logger.debug(
                    f"Found {n_hfs} halo files that match these redshifts")

                # Run halo file calculations...
                for hf in halo_files:
                    self.tasks(hf)

                    # Clear the data set cache between iterations as the
                    # data isn't persistent anyway, and this saves memory
                    logger.debug("Clearing dataset cache for new iteration")
                    self._ds_cache.clear()

            # Reset the cache between simulations to save memory
            self._cache.reset()

            logger.info("DONE calculations\n")

    def tasks(self, hf: str):
        pass
