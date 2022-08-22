import logging
import time

import numpy as np

from src.util.constants import COORDINATES_CACHE_NAME
from src.cache import caching

CACHE = caching.Cache()


def rand_coords(amount: int, min: int = 0, max: int = 100):
    global CACHE
    logger = logging.getLogger(__name__ + "." + rand_coords.__name__)

    RANGE_KEY = (COORDINATES_CACHE_NAME, min, max)
    existing_coords = CACHE[RANGE_KEY].val
    num_existing = 0
    if existing_coords is not None:
        num_existing = len(existing_coords)

    if amount > num_existing:
        logger.debug(
            f"Entries in cache exist, but require {amount} values, and only have {num_existing}")  # noqa: E501
        extra_coords = _gen_coords(min, max, amount - num_existing)
        if existing_coords is None:
            coords = extra_coords
        else:
            coords = np.append(existing_coords, extra_coords, axis=0)

        CACHE[RANGE_KEY] = coords

    else:
        logger.debug(f"Using existing coordinates for key {RANGE_KEY}")
        coords = existing_coords

    # There can be more coords cached than we need, so
    # split the list to that amount
    return coords[:amount]


def _gen_coords(min: int, max: int, amount: int) -> np.ndarray:
    logger = logging.getLogger(__name__ + "." + _gen_coords.__name__)
    logger.debug(
        f"Generating {amount} coordinates in range ({min}, {max})")

    np.random.seed(int(time.time()))
    return (max - min) * np.random.rand(amount, 3) + min
