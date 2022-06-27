import logging
import time

import numpy as np

import caching
from constants import PATH_TO_COORDS_CACHE

CACHE = caching.Cacher(PATH_TO_COORDS_CACHE)


def rand_coords(amount: int, min: int = 0, max: int = 100):
    global CACHE
    logger = logging.getLogger(__name__ + "." + rand_coords.__name__)

    RANGE_KEY = (min, max)

    if RANGE_KEY not in CACHE:
        logger.debug(
            f"Coordinates in range ({min}, {max}) not found in cache, generating new entries...")

        coords = _gen_coords(min, max, amount)
        CACHE[RANGE_KEY] = coords
        CACHE.save_cache()

    else:
        existing_coords = CACHE[RANGE_KEY]
        num_existing = len(existing_coords)

        if amount > num_existing:
            logger.debug(
                f"Entries in cache exist, but require {amount} values, and only have {num_existing}")
            extra_coords = _gen_coords(min, max, amount - num_existing)
            coords = np.append(existing_coords, extra_coords, axis=0)

            CACHE[RANGE_KEY] = coords
            CACHE.save_cache()

        else:
            logger.debug(f"Using existing coordinates for key {RANGE_KEY}")

    # There can be more coords cached than we need, so split the list to that amount
    return CACHE[RANGE_KEY][:amount]


def _gen_coords(min: int, max: int, amount: int) -> np.ndarray:
    logger = logging.getLogger(__name__ + "." + _gen_coords.__name__)
    logger.debug(
        f"Generating {amount} coordinates in range ({min}, {max})")

    np.random.seed(int(time.time()))
    return (max - min) * np.random.rand(amount, 3) + min
