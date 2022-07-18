import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import logging

import numpy as np
import src.util.halo_finder as hf
from src import enum
from src.cache import caching
from src.const.constants import COORDINATES_CACHE_TOP5_NAME

CACHE = caching.Cache()


def get_halo_coords(halo_type: enum.DataType, root: str, sim_name: str, ds_cache):
    logger = logging.getLogger(__name__ + "." + get_halo_coords.__name__)

    data = CACHE[sim_name, COORDINATES_CACHE_TOP5_NAME].val
    if data is None:
        logger.info("Values missing from cache, calculating...")

        halo_finder = hf.HalosFinder(halo_type, root, sim_name)

        halo_fname = halo_finder.filter_data_files([0], tolerance=1e-9)
        if len(halo_fname < 1) or len(halo_fname >= 2):
            logger.warning("Too many halo files found!")
            return

        fname = halo_fname[0]

        ad = ds_cache.all_data(fname)

        logger.debug("Reading halo masses from dataset")
        masses = ad[halo_type.index]

        logger.debug("Filtering masses for top 5 most massive")
        top5_idxs = np.argpartition(masses, -5)[-5:]

        logger.debug("Finding matching coords")
        top5_masses = masses[top5_idxs]
        xs = ad[halo_type.coord_index_x()]
        ys = ad[halo_type.coord_index_y()]
        zs = ad[halo_type.coord_index_z()]

        x = xs[top5_idxs]
        y = ys[top5_idxs]
        z = zs[top5_idxs]

        virial_radii = ad[halo_type.virial_radii()]
        v_radius = virial_radii[top5_idxs]

        logger.debug("Compiling cache data...")

        data = {}
        for i in range(len(top5_idxs)):
            data[i] = {
                "coords": (x[i], y[i], z[i]),
                "mass": top5_masses[i],
                "virial_radius": v_radius[i]
            }
            logger.info(data[i])

        CACHE[sim_name, COORDINATES_CACHE_TOP5_NAME] = data

    return data
