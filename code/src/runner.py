import logging
from typing import List

import yt

import src.enum as enum
from src.init import setup
from src.util import helpers


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
            snapshots, groups, rockstars = helpers.filter_data_files(
                self._data.sim_name, self._conf.sim_data.root, zs, tolerance=1e-9)

            n_rcks = len(rockstars)
            logger.debug(
                f"Found {n_rcks} rockstar files that match these redshifts")

            # Run snapshot calculations...
            for snap in snapshots:
                self._type = enum.DataType.SNAPSHOT
                self.snapshot_tasks(snap)

            # Run group calculations...
            for group in groups:
                self._type = enum.DataType.GROUP
                self.group_tasks(group)

            # Run the calculations over all the rockstar files found
            for rck in rockstars:
                self._type = enum.DataType.ROCKSTAR

                # Run the tasks of this object
                self.rockstar_tasks(rck)

                # Clear the data set cache between iterations as the
                # data isn't persistent anyway, and this saves memory
                logger.debug("Clearing dataset cache for new iteration")
                self._ds_cache.clear()

            # Reset the cache between simulations to save memory
            self._cache.reset()

            logger.info("DONE calculations\n")

    def rockstar_tasks(self, rck: str):
        pass

    def snapshot_tasks(self, snap: str):
        pass

    def group_tasks(self, group: str):
        pass
