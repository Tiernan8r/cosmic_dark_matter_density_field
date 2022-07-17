import logging
import math
import os
import re
from typing import Dict, List

import yt
from src import enum
from src.cache import caching
from src.const.constants import DIR_KEY, REDSHIFTS_KEY, sim_regex


class HalosFinder(caching.Cache):

    def __init__(self, halo_type: enum.DataType, root: str, sim_name: str):
        self._type = halo_type
        self._root = root
        self._sim_name = sim_name

        cache_dir = f"../data/{sim_name}/{halo_type.value}/"
        super().__init__(caches_dir=cache_dir)

    def _find_directory(self) -> str:
        logger = logging.getLogger(
            __name__ + "." + self._find_directory.__name__)

        if not sim_regex.match(self._sim_name):
            logger.warning(
                f"'{self._sim_name}' did not match the expected pattern, defaulting to '/tmp'")  # noqa: E501
            return "/tmp"

        logger.debug(
            f"Compiling paths using the provided '{self._sim_name}' simulation data set name.")  # noqa: E501

        dir_root = os.path.join(self._root, self._sim_name, self._type.data())

        return dir_root

    def _find_data_files(self) -> List[str]:
        logger = logging.getLogger(
            __name__ + "." + self._find_data_files.__name__)

        def find(dirname: str, file_reg: re.Pattern, root_reg: re.Pattern = None):
            lg = logging.getLogger(logger.name + "." + find.__name__)
            halo_files = []

            for root, dirs, files in os.walk(dirname):
                for file in files:
                    if file_reg.match(file):
                        if root_reg is not None:
                            if not root_reg.match(root):
                                continue
                        lg.debug(
                            f"File '{file}' matched the provided regex, allocating to the paths")  # noqa: E501
                        pth = os.path.join(root, file)

                        halo_files.append(pth)

            return halo_files

        halo_dirs = self[(DIR_KEY,)].val
        if halo_dirs is None:
            logger.debug(
                f"'{DIR_KEY}' key not found in cache, compiling new entry...")

            dir_root = self._find_directory()

            files = find(dir_root, self._type.get_regex(),
                         self._type.get_root_regex())

            halo_dirs = sorted(files)

            self[(DIR_KEY,)] = halo_dirs

        return halo_dirs

    def _determine_redshifts(self) -> Dict[float, str]:
        logger = logging.getLogger(
            __name__ + "." + self._determine_redshifts.__name__)

        map = self[(REDSHIFTS_KEY,)].val
        # If the map is an empty dictionary
        if map is None:
            logger.warn(
                f"'{REDSHIFTS_KEY}' key not found in cache, creating entry...")

            halo_files = self._find_data_files()
            fname_regex = self._type.get_regex()

            map = {}

            for hf in halo_files:
                ds = yt.load(hf)
                z = ds.current_redshift

                hf_num = fname_regex.match(hf).group(2)

                logger.debug(f"Read a redshift of z={z} from '{hf}'")

                map[z] = hf_num

            self[(REDSHIFTS_KEY,)] = map

        return map

    def _filter_redshifts(self,
                          desired: List[float],
                          tolerance: float) -> Dict[float, str]:
        logger = logging.getLogger(
            __name__ + "." + self._filter_redshifts.__name__)

        all_redshifts = self._determine_redshifts()

        redshifts = {}

        for k in all_redshifts.keys():
            for z in desired:
                if math.isclose(k, z, rel_tol=tolerance) and k not in redshifts:
                    logger.debug(
                        f"Redshift of '{k}' is close to '{z}', storing path '{all_redshifts[k]}' in dict.")  # noqa: E501
                    redshifts[k] = all_redshifts[k]
        return redshifts

    def filter_data_files(self,
                          desired: List[float],
                          tolerance=1e-3) -> List[str]:
        logger = logging.getLogger(
            __name__ + "." + self.filter_data_files.__name__)

        redshifts = self._filter_redshifts(desired, tolerance)
        halo_dirs = self._find_data_files()

        logger.debug(f"Filtering data files around redshifts '{desired}'")

        file_idxs = redshifts.values()

        def filter(vals): return [
            v for v in vals if any([i in v for i in file_idxs])]

        filtered_dirs = filter(halo_dirs)

        return filtered_dirs
