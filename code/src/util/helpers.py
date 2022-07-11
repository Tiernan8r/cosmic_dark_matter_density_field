import logging
import math
import os
import re
from typing import Dict, List, Tuple

from src.cache import caching
from src.const.constants import (DATA, DIR_KEY, GROUPS_KEY, REDSHIFTS_KEY,
                                 ROCKSTAR, ROCKSTARS_KEY, SNAPSHOTS_KEY,
                                 groups_regex, rockstar_a_factor,
                                 rockstar_ascii_reg, rockstar_regex,
                                 rockstar_root_regex, sim_regex,
                                 snapshots_regex)

CACHE = caching.Cache()


def _find_directories(sim_name: str, root) -> Tuple[str, str, str]:
    logger = logging.getLogger(__name__ + "." + _find_directories.__name__)

    if not sim_regex.match(sim_name):
        logger.warning(
            f"'{sim_name}' did not match the expected pattern, defaulting to '/tmp'")  # noqa: E501
        return "/tmp", "/tmp", "/tmp"

    logger.debug(
        f"Compiling paths using the provided '{sim_name}' simulation data set name.")  # noqa: E501

    snapshots_root = root + sim_name + "/" + DATA
    groups_root = snapshots_root
    rockstar_root = root + sim_name + "/" + ROCKSTAR

    return snapshots_root, groups_root, rockstar_root


def _find_data_files(sim_name: str, root: str) -> Tuple[
        List[str],
        List[str],
        List[str]]:
    logger = logging.getLogger(__name__ + "." + _find_data_files.__name__)

    def find(dirname: str, file_reg: re.Pattern, root_reg: re.Pattern = None):
        lg = logging.getLogger(logger.name + "." + find.__name__)
        files = []

        for root, dirs, files in os.walk(dirname):
            for file in files:
                if file_reg.match(file):
                    if root_reg is not None:
                        if not root_reg.match(root):
                            continue
                    lg.debug(
                        f"File '{file}' matched the provided regex, allocating to the paths")  # noqa: E501
                    pth = os.path.join(root, file)
                    files.append(pth)

        return files

    global CACHE

    halo_dirs = CACHE[sim_name, DIR_KEY].val
    if halo_dirs is None:
        logger.debug(
            f"'{DIR_KEY}' key not found in cache, compiling new entry...")

        snap, group, rock = _find_directories(sim_name, root)

        groups = find(group, groups_regex)
        rockstars = find(rock, rockstar_regex, rockstar_root_regex)
        snapshots = find(snap, snapshots_regex)

        halo_dirs = {
            SNAPSHOTS_KEY: sorted(snapshots),
            GROUPS_KEY: sorted(groups),
            ROCKSTARS_KEY: sorted(rockstars),
        }

        CACHE[sim_name, DIR_KEY] = halo_dirs

    return (halo_dirs[SNAPSHOTS_KEY],
            halo_dirs[GROUPS_KEY],
            halo_dirs[ROCKSTARS_KEY])


def _determine_redshifts(sim_name: str, root: str) -> Dict[float, str]:
    logger = logging.getLogger(__name__ + "." + _determine_redshifts.__name__)

    global CACHE

    map = CACHE[sim_name, REDSHIFTS_KEY].val
    # If the map is an empty dictionary
    if map is None:
        logger.warn(
            f"'{REDSHIFTS_KEY}' key not found in cache, creating entry...")

        _, _, rock = _find_directories(sim_name, root)

        map = {}

        for dirname, subdirs, files in os.walk(rock):
            for file in files:
                if rockstar_ascii_reg.match(file):
                    logger.debug(f"'{file}' matches ascii file regex")

                    with open(dirname + file) as f:
                        # Read the second line in the vals file, which says
                        # the expansion factor
                        a = f.readlines()[1]
                        a_val = float(rockstar_a_factor.match(a).group(1))
                        # convert from comoving to redshift
                        z = (1 / a_val) - 1

                        logger.debug(
                            f"Read a redshift of z={z} from '{file}'")

                        map[z] = rockstar_ascii_reg.match(file).group(2)

        CACHE[sim_name, REDSHIFTS_KEY] = map

    return map


def _filter_redshifts(sim_name: str,
                      root: str,
                      desired: List[float],
                      tolerance=0.02) -> Dict[float, str]:
    logger = logging.getLogger(__name__ + "." + _filter_redshifts.__name__)

    all_redshifts = _determine_redshifts(sim_name, root)

    redshifts = {}

    for k in all_redshifts.keys():
        for z in desired:
            if math.isclose(k, z, rel_tol=tolerance) and k not in redshifts:
                logger.debug(
                    f"Redshift of '{k}' is close to '{z}', storing path '{all_redshifts[k]}' in dict.")  # noqa: E501
                redshifts[k] = all_redshifts[k]
    return redshifts


def filter_data_files(sim_name: str,
                      root: str,
                      desired: List[float],
                      tolerance=0.02) -> Tuple[
        List[str],
        List[str],
        List[str]]:
    logger = logging.getLogger(__name__ + "." + filter_data_files.__name__)

    redshifts = _filter_redshifts(sim_name, root, desired, tolerance)
    snaps, groups, rocks = _find_data_files(sim_name, root)

    logger.debug(f"Filtering data files around redshifts '{desired}'")

    file_idxs = redshifts.values()

    def filter(vals): return [
        v for v in vals if any([i in v for i in file_idxs])]

    filter_snaps = filter(snaps)
    filter_groups = filter(groups)
    filter_rocks = filter(rocks)

    return filter_snaps, filter_groups, filter_rocks
