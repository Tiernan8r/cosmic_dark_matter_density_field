#!/usr/bin/env python
import functools
import json
import logging
import logging.config
import os
import pickle
from typing import Any, Dict

import numpy as np
import unyt
import yt
import yt.extensions.legacy

import coordinates
import dataset_cacher
import helpers
import plotting
from constants import (DESIRED_RADII, DESIRED_REDSHIFTS, LOG_FILENAME,
                       MASS_FN_PLOTS_DIR, MASS_FUNCTION_KEY,
                       NUM_SPHERE_SAMPLES, OVERDENSITIES_KEY,
                       PATH_TO_CALCULATIONS_CACHE, REDSHIFT_KEY, RHO_BAR_KEY,
                       ROOT, SIM_FOLDER, SIM_NAME, TOTAL_MASS_FUNCTION_KEY)


@functools.lru_cache(maxsize=1)
def _get_cache() -> Dict[str, Any]:
    logger = logging.getLogger(_get_cache.__name__)

    if os.path.exists(PATH_TO_CALCULATIONS_CACHE):
        with open(PATH_TO_CALCULATIONS_CACHE, "rb") as f:
            logger.debug("Found existing cache, reading...")
            return pickle.load(f)
    else:
        logger.debug("Found no existing cache, creating empty dict")
        return {}


GLOBAL_CACHE = _get_cache()
DATASET_CACHE = dataset_cacher.new()


def _save_cache():
    logger = logging.getLogger(_save_cache.__name__)
    global GLOBAL_CACHE
    with open(PATH_TO_CALCULATIONS_CACHE, "wb") as f:
        logger.debug(f"Saving cache to '{PATH_TO_CALCULATIONS_CACHE}'")
        pickle.dump(GLOBAL_CACHE, f)


def setup_logging() -> logging.Logger:
    logging_path = os.path.abspath(LOG_FILENAME)
    with open(logging_path) as f:
        dict_config = json.load(f)

    logging.config.dictConfig(dict_config)


def main():
    if yt.is_root():

        setup_logging()
        logger = logging.getLogger(main.__name__)

        yt.enable_parallelism()
        logger.info("Parallelism enabled...")

        pth = ROOT + SIM_FOLDER
        logger.debug(f"Reading data set in '{pth}'")

        # Find halos for data set
        logger.debug(
            f"Filtering halo files to look for redshifts: {DESIRED_REDSHIFTS}")
        _, _, rockstars = helpers.filter_data_files(
            SIM_NAME, DESIRED_REDSHIFTS)
        logger.debug(
            f"Found {len(rockstars)} rockstar files that match these redshifts")

        for rck in rockstars:
            logger.debug(f"Working on rockstar file '{rck}'")

            total_mass_function(rck)

            for radius in DESIRED_RADII:

                # Errors handled in code, so can ignore...
                try:
                    z, masses, deltas = halo_work(rck, radius)
                except:
                    continue

                logger.debug("Generating plot for this data...")
                plotting.plot(z, radius, masses, deltas, sim_name=SIM_NAME)

        # Save the dataset cache to disk...
        DATASET_CACHE.save()

        logger.info("DONE calculations\n")


def total_mass_function(rck):
    if not yt.is_root():
        return

    logger = logging.getLogger(total_mass_function.__name__)

    logger.debug("Calculating total mass function:")

    global GLOBAL_CACHE
    if rck not in GLOBAL_CACHE:
        GLOBAL_CACHE[rck] = {}

    ds = DATASET_CACHE.load(rck)

    if TOTAL_MASS_FUNCTION_KEY not in GLOBAL_CACHE[rck]:
        logger.debug(f"No masses cached for '{rck}' data set, caching...")

        try:
            ad = DATASET_CACHE.all_data(rck)
        except TypeError as te:
            logger.error("error reading all_data(), ignoring...")
            logger.error(te)
            return

        masses = ad["halos", "particle_mass"].to(ds.units.Msun / ds.units.h)

        if REDSHIFT_KEY not in GLOBAL_CACHE[rck]:
            GLOBAL_CACHE[rck][REDSHIFT_KEY] = ds.current_redshift

        GLOBAL_CACHE[rck][TOTAL_MASS_FUNCTION_KEY] = masses
        _save_cache()
    else:
        logger.debug("Using cached masses in plots...")

    masses = GLOBAL_CACHE[rck][TOTAL_MASS_FUNCTION_KEY]

    hist, bins = np.histogram(masses)

    z = GLOBAL_CACHE[rck][REDSHIFT_KEY]
    a = 1 / (1+z)

    V = (ds.domain_width[0] * a)**3
    hist = hist / V

    title = f"Total Mass Function for @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(SIM_NAME)
    plot_name = (MASS_FN_PLOTS_DIR +
                 "total_mass_function_z{1:.2f}.png").format(SIM_FOLDER, z)

    plotting.plot_mass_function(hist, bins, title, save_dir, plot_name)


def halo_work(rck: str, radius: float):
    logger = logging.getLogger(halo_work.__name__)
    global GLOBAL_CACHE

    if rck not in GLOBAL_CACHE:
        GLOBAL_CACHE[rck] = {}

    logger.info("Working on rho_bar value:")

    if RHO_BAR_KEY not in GLOBAL_CACHE[rck]:
        logger.debug(
            f"No entries found in cache for '{RHO_BAR_KEY}', calculating...")

        try:
            rb = _calc_rho_bar(rck)
        except TypeError as te:
            logger.error("error getting all dataset region")
            logger.error(te)
            raise te
        except unyt.exceptions.IterableUnitCoercionError as iuce:
            logger.error(
                "Error reading regions quantities from database, ignoring...")
            logger.error(iuce)
            raise iuce

        GLOBAL_CACHE[rck][RHO_BAR_KEY] = rb
        _save_cache()
    else:
        logger.debug("Using cached `rho_bar` value...")

    rho_bar = GLOBAL_CACHE[rck][RHO_BAR_KEY]

    logger.info("Working on overdensities:")

    if OVERDENSITIES_KEY not in GLOBAL_CACHE[rck]:
        GLOBAL_CACHE[rck][OVERDENSITIES_KEY] = {}

    if radius not in GLOBAL_CACHE[rck][OVERDENSITIES_KEY]:
        logger.debug(
            f"No entries found in cache for '{OVERDENSITIES_KEY}', calculating...")

        GLOBAL_CACHE[rck][OVERDENSITIES_KEY][radius] = _calc_overdensities(
            rck, radius, rho_bar)
        _save_cache()
    else:
        ods = GLOBAL_CACHE[rck][OVERDENSITIES_KEY][radius]

        if len(ods) < NUM_SPHERE_SAMPLES:
            logger.debug(
                f"Entries in cache exist, but need {NUM_SPHERE_SAMPLES - len(ods)} more values...")

            GLOBAL_CACHE[rck][OVERDENSITIES_KEY][radius] = _calc_overdensities(
                rck, radius, rho_bar, existing=ods)
            _save_cache()

        else:
            logger.debug("Using cached overdensities...")

    logger.info("Working on mass function:")

    if MASS_FUNCTION_KEY not in GLOBAL_CACHE[rck]:
        GLOBAL_CACHE[rck][MASS_FUNCTION_KEY] = {}

    if radius not in GLOBAL_CACHE[rck][MASS_FUNCTION_KEY]:
        logger.debug(
            f"No entries found in cache for '{MASS_FUNCTION_KEY}', calculating...")

        GLOBAL_CACHE[rck][MASS_FUNCTION_KEY][radius] = _sample_masses(
            rck, radius)
        _save_cache()
    else:
        ms = GLOBAL_CACHE[rck][MASS_FUNCTION_KEY][radius]
        if len(ms) < NUM_SPHERE_SAMPLES:
            logger.debug(
                f"Entries in cache exist, but need {NUM_SPHERE_SAMPLES - len(ods)} more values...")
            GLOBAL_CACHE[rck][MASS_FUNCTION_KEY][radius] = _sample_masses(
                rck, radius, existing=ms)
            _save_cache()
        else:
            logger.debug("Using cached halo masses...")

    z = GLOBAL_CACHE[rck][REDSHIFT_KEY]
    # Get the values from the cache, and truncate the lists to the desired number of values
    # if there are too many
    masses = GLOBAL_CACHE[rck][MASS_FUNCTION_KEY][radius][:NUM_SPHERE_SAMPLES]
    deltas = GLOBAL_CACHE[rck][OVERDENSITIES_KEY][radius][:NUM_SPHERE_SAMPLES]

    return z, masses, deltas


def _calc_rho_bar(rck):
    logger = logging.getLogger(_calc_rho_bar.__name__)

    ds = DATASET_CACHE.load(rck)

    dist_units = ds.units.Mpc / ds.units.h

    global GLOBAL_CACHE
    if REDSHIFT_KEY not in GLOBAL_CACHE[rck]:
        GLOBAL_CACHE[rck][REDSHIFT_KEY] = ds.current_redshift

    z = GLOBAL_CACHE[rck][REDSHIFT_KEY]
    a = 1/(1+z)

    logger.debug(f"Redshift z={z}")

    sim_size = (ds.domain_width[0]).to(dist_units)
    logger.debug(f"Simulation size = {sim_size}")

    # Try to get the entire dataset region
    ad = DATASET_CACHE.all_data(rck)

    # Get the average density over the region
    rho_bar = ad.quantities.total_mass()[1] / (sim_size*a)**3

    return rho_bar


def _calc_overdensities(rck, radius, rho_bar, existing: unyt.unyt_array = None):
    logger = logging.getLogger(_calc_overdensities.__name__)

    ds = DATASET_CACHE.load(rck)

    dist_units = ds.units.Mpc / ds.units.h
    R = radius * dist_units

    global GLOBAL_CACHE
    if REDSHIFT_KEY not in GLOBAL_CACHE[rck]:
        GLOBAL_CACHE[rck][REDSHIFT_KEY] = ds.current_redshift

    z = GLOBAL_CACHE[rck][REDSHIFT_KEY]
    a = 1/(1+z)

    logger.debug(f"Redshift z={z}")

    V = 4/3 * np.pi * (a*R)**3

    sim_size = (ds.domain_width[0]).to(dist_units)
    logger.debug(f"Simulation size = {sim_size}")

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = coordinates.rand_coords(
        NUM_SPHERE_SAMPLES, min=coord_min, max=coord_max) * dist_units

    # If there are existing entries, truncate the number of new calculations...
    deltas = unyt.unyt_array([])
    if existing is not None:
        coords = coords[len(existing):]

        deltas = existing

    # Iterate over all the randomly sampled coordinates
    for c in yt.parallel_objects(coords):
        logger.debug(
            f"Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        # Try to sample a sphere of the given radius at this coord
        try:
            sp = DATASET_CACHE.sphere(rck, c, R)
        except TypeError as te:
            logger.error("error creating sphere sample")
            logger.error(te)
            continue

        # Try to calculate the overdensity of the sphere
        try:
            rho = sp.quantities.total_mass()[1] / V
            delta = (rho - rho_bar) / rho_bar
            d = unyt.unyt_array([delta])

            deltas = unyt.uconcatenate((deltas, d))
        except unyt.exceptions.IterableUnitCoercionError as iuce:
            logger.error("Error reading sphere quantities, ignoring...")
            logger.error(iuce)

    return unyt.unyt_array(deltas)


def _sample_masses(rck, radius, existing: unyt.unyt_array = None):
    logger = logging.getLogger(_sample_masses.__name__)

    ds = DATASET_CACHE.load(rck)

    dist_units = ds.units.Mpc / ds.units.h
    R = radius * dist_units

    global GLOBAL_CACHE
    if REDSHIFT_KEY not in GLOBAL_CACHE[rck]:
        GLOBAL_CACHE[rck][REDSHIFT_KEY] = ds.current_redshift

    z = GLOBAL_CACHE[rck][REDSHIFT_KEY]

    logger.debug(f"Redshift z={z}")

    sim_size = (ds.domain_width[0]).to(dist_units)
    logger.debug(f"Simulation size = {sim_size}")

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = coordinates.rand_coords(
        NUM_SPHERE_SAMPLES, min=coord_min, max=coord_max) * dist_units

    # Truncate the number of values to calculate, if some already exist...
    masses = unyt.unyt_array([], ds.units.Msun/ds.units.h)
    if existing is not None:
        coords = coords[len(existing):]
        masses = existing

    # Iterate over all the randomly sampled coordinates
    for c in yt.parallel_objects(coords):
        logger.debug(
            f"Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        # Try to sample a sphere of the given radius at this coord
        try:
            sp = DATASET_CACHE.sphere(rck, c, R)
        except TypeError as te:
            logger.error("error creating sphere sample")
            logger.error(te)
            continue

        # Try to read the masses of halos in this sphere
        try:
            m = sp["halos", "particle_mass"]
        except TypeError as te:
            logger.error("error reading sphere total_mass()")
            logger.error(te)
            continue

        logger.debug(f"Found {len(m)} halos in this sphere sample")

        masses = unyt.uconcatenate((masses, m))

    logger.info(f"DONE reading {NUM_SPHERE_SAMPLES} sphere samples\n")

    return masses


if __name__ == "__main__":
    main()
