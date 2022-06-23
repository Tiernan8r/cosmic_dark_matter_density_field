import functools
import logging
import math
import os
import pickle
import re
from typing import Any, Dict, List, Tuple

from constants import (DATA, DIR_KEY, GROUPS_KEY, PATH_TO_CACHE, REDSHIFTS_KEY,
                       ROCKSTAR, ROCKSTARS_KEY, ROOT, SNAPSHOTS_KEY,
                       groups_regex, rockstar_a_factor, rockstar_ascii_reg,
                       rockstar_regex, rockstar_root_regex, sim_regex,
                       snapshots_regex)


@functools.lru_cache(maxsize=1)
def _get_cache() -> Dict[str, Any]:
    logger = logging.getLogger(__name__ + "." + _get_cache.__name__)

    if os.path.exists(PATH_TO_CACHE):
        with open(PATH_TO_CACHE, "rb") as f:
            logger.debug("Found existing cache, reading...")
            return pickle.load(f)
    else:
        logger.debug("Found no existing cache, creating empty dict")
        return {}


GLOBAL_CACHE = _get_cache()


def _save_cache():
    logger = logging.getLogger(__name__ + "." + _save_cache.__name__)
    global GLOBAL_CACHE
    with open(PATH_TO_CACHE, "wb") as f:
        logger.debug(f"Saving cache to '{PATH_TO_CACHE}'")
        pickle.dump(GLOBAL_CACHE, f)


def _find_directories(sim_name: str) -> Tuple[str, str, str]:
    logger = logging.getLogger(__name__ + "." + _find_directories.__name__)

    if not sim_regex.match(sim_name):
        logger.warn(
            f"'{sim_name}' did not match the expected pattern, defaulting to '/tmp'")
        return "/tmp", "/tmp", "/tmp"

    logger.debug(
        f"Compiling paths using the provided '{sim_name}' simulation data set name.")

    snapshots_root = ROOT + sim_name + "/" + DATA
    groups_root = snapshots_root
    rockstar_root = ROOT + sim_name + "/" + ROCKSTAR

    return snapshots_root, groups_root, rockstar_root


def find_data_files(sim_name: str) -> Tuple[List[str], List[str], List[str]]:
    logger = logging.getLogger(__name__ + "." + find_data_files.__name__)

    def find(dirname: str, file_reg: re.Pattern, root_reg: re.Pattern = None):
        lg = logging.getLogger(logger.name + "." + find.__name__)
        l = []

        for root, dirs, files in os.walk(dirname):
            for file in files:
                if file_reg.match(file):
                    if root_reg is not None:
                        if not root_reg.match(root):
                            continue
                    lg.debug(
                        f"File '{file}' matched the provided regex, allocating to the paths")
                    l.append(root + file)

        return l

    global GLOBAL_CACHE

    if sim_name not in GLOBAL_CACHE:
        GLOBAL_CACHE[sim_name] = {}

    if DIR_KEY not in GLOBAL_CACHE[sim_name]:
        logger.debug(
            f"'{DIR_KEY}' key not found in cache, compiling new entry...")

        snap, group, rock = _find_directories(sim_name)

        groups = find(group, groups_regex)
        rockstars = find(rock, rockstar_regex, rockstar_root_regex)
        snapshots = find(snap, snapshots_regex)

        dirs = {
            SNAPSHOTS_KEY: sorted(snapshots),
            GROUPS_KEY: sorted(groups),
            ROCKSTARS_KEY: sorted(rockstars),
        }

        GLOBAL_CACHE[sim_name][DIR_KEY] = dirs
        _save_cache()

    dirs = GLOBAL_CACHE[sim_name][DIR_KEY]
    return dirs[SNAPSHOTS_KEY], dirs[GROUPS_KEY], dirs[ROCKSTARS_KEY]


def determine_redshifts(sim_name: str) -> Dict[float, str]:
    logger = logging.getLogger(__name__ + "." + determine_redshifts.__name__)
    global GLOBAL_CACHE

    if sim_name not in GLOBAL_CACHE:
        GLOBAL_CACHE[sim_name] = {}

    if REDSHIFTS_KEY not in GLOBAL_CACHE[sim_name]:
        logger.warn(
            f"'{REDSHIFTS_KEY}' key not found in cache, creating entry...")

        _, _, rock = _find_directories(sim_name)

        map = {}

        for dirname, subdirs, files in os.walk(rock):
            for file in files:
                if rockstar_ascii_reg.match(file):
                    logger.debug(f"'{file}' matches ascii file regex")

                    with open(dirname + file) as f:
                        # Read the second line in the vals file, which says the expansion factor
                        a = f.readlines()[1]
                        a_val = float(rockstar_a_factor.match(a).group(1))
                        # convert from comoving to redshift
                        z = (1 / a_val) - 1

                        logger.debug(
                            f"Read a readshift of z={z} from '{file}'")

                        map[z] = rockstar_ascii_reg.match(file).group(2)

        GLOBAL_CACHE[sim_name][REDSHIFTS_KEY] = map
        _save_cache()

    return GLOBAL_CACHE[sim_name][REDSHIFTS_KEY]


def filter_redshifts(sim_name: str, desired: List[float], tolerance=0.02) -> Dict[float, str]:
    logger = logging.getLogger(__name__ + "." + filter_redshifts.__name__)

    all_redshifts = determine_redshifts(sim_name)

    redshifts = {}

    for k in all_redshifts.keys():
        for z in desired:
            if math.isclose(k, z, rel_tol=tolerance) and k not in redshifts:
                logger.debug(
                    f"Redshift of '{k}' is close to '{z}', storing path '{all_redshifts[k]}' in dict.")
                redshifts[k] = all_redshifts[k]
    return redshifts


def filter_data_files(sim_name: str, desired: List[float], tolerance=0.02) -> Tuple[List[str], List[str], List[str]]:
    logger = logging.getLogger(__name__ + "." + filter_data_files.__name__)

    redshifts = filter_redshifts(sim_name, desired, tolerance)
    snaps, groups, rocks = find_data_files(sim_name)

    logger.debug(f"Filtering data files around redshifts '{desired}'")

    file_idxs = redshifts.values()

    def filter(vals): return [
        v for v in vals if any([i in v for i in file_idxs])]

    filter_snaps = filter(snaps)
    filter_groups = filter(groups)
    filter_rocks = filter(rocks)

    return filter_snaps, filter_groups, filter_rocks
