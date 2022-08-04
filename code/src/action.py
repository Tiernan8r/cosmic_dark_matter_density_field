import logging
from typing import List

import yt

from src import enum, interface
from src.init import setup
from src.util import halo_finder


class Orchestrator(interface.Interface):

    def __init__(self, args: List[str]):
        d = setup.setup(args)
        super().__init__(d)

    def run(self):
        yt.enable_parallelism()
        if not yt.is_root():
            return

        logger = logging.getLogger(self.run.__name__)

        # Iterate over the simulations
        for sim_name in yt.parallel_objects(self.config.sim_data.simulation_names):

            # Save the current sim name into the data object
            self.sim_name = sim_name

            logger.info(f"Working on simulation: {self.sim_name}")

            # Find halos for data set
            zs = self.config.redshifts
            logger.debug(
                f"Filtering halo files to look for redshifts: {zs}")

            for tp in yt.parallel_objects(enum.DataType):
                self.type = tp

                logger.info(f"Working on {tp} datasets:")

                # Skip dataset type calculation if not set to run in the config
                type_name = tp.value
                if not self.config.datatypes.__getattribute__(type_name):
                    logger.info("Skipping...")
                    continue

                halos_finder = halo_finder.HalosFinder(
                    halo_type=tp, root=self.config.sim_data.root, sim_name=sim_name)
                halo_files = halos_finder.filter_data_files(zs)

                n_hfs = len(halo_files)
                logger.debug(
                    f"Found {n_hfs} halo files that match these redshifts")

                # Run halo file calculations...
                for hf in yt.parallel_objects(halo_files):
                    self.tasks(hf)

                    # Clear the data set cache between iterations as the
                    # data isn't persistent anyway, and this saves memory
                    logger.debug("Clearing dataset cache for new iteration")
                    self.dataset_cache.clear()

                # Reset the cache between simulations to save memory
                self._cache.reset()

            logger.info("DONE calculations\n")

    def tasks(self, hf: str):
        pass
