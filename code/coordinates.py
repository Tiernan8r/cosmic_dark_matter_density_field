import functools
import logging
import os
import pickle
import time
from typing import Any, Dict

import numpy as np

from constants import PATH_TO_COORDS_CACHE


@functools.lru_cache(maxsize=1)
def _get_cache() -> Dict[str, Any]:
    logger = logging.getLogger(__name__ + "." + _get_cache.__name__)

    if os.path.exists(PATH_TO_COORDS_CACHE):
        with open(PATH_TO_COORDS_CACHE, "rb") as f:
            logger.debug("Found existing cache, reading...")
            return pickle.load(f)
    else:
        logger.debug("Found no existing cache, creating empty dict")
        return {}


GLOBAL_CACHE = _get_cache()


def _save_cache():
    logger = logging.getLogger(__name__ + "." + _save_cache.__name__)
    global GLOBAL_CACHE
    with open(PATH_TO_COORDS_CACHE, "wb") as f:
        logger.debug(f"Saving cache to '{PATH_TO_COORDS_CACHE}'")
        pickle.dump(GLOBAL_CACHE, f)


def rand_coords(amount: int, min: int = 0, max: int = 100):
    global GLOBAL_CACHE
    logger = logging.getLogger(__name__ + "." + rand_coords.__name__)

    RANGE_KEY = (min, max)

    if RANGE_KEY not in GLOBAL_CACHE:
        logger.debug(
            f"Coordinates in range ({min}, {max}) not found in cache, generating new entries...")

        coords = _gen_coords(min, max, amount)
        GLOBAL_CACHE[RANGE_KEY] = coords
        _save_cache()
    else:
        existing_coords = GLOBAL_CACHE[RANGE_KEY]
        num_existing = len(existing_coords)

        if amount > num_existing:
            logger.debug(
                f"Entries in cache exist, but require {amount} values, and only have {num_existing}")
            extra_coords = _gen_coords(min, max, amount - num_existing)
            coords = np.append(existing_coords, extra_coords, axis=0)

            GLOBAL_CACHE[RANGE_KEY] = coords
            _save_cache()
        else:
            logger.debug(f"Using existing coordinates for key {RANGE_KEY}")

    # There can be more coords cached than we need, so split the list to that amount
    return GLOBAL_CACHE[RANGE_KEY][:amount]


def _gen_coords(min: int, max: int, amount: int) -> np.ndarray:
    logger = logging.getLogger(__name__ + "." + _gen_coords.__name__)
    logger.debug(
        f"Generating {amount} coordinates in range ({min}, {max})")

    np.random.seed(int(time.time()))
    return (max - min) * np.random.rand(amount, 3) + min
