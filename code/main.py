#!/usr/bin/env python3
import logging
import logging.config
import sys

import numpy as np
import yt

import caching
import helpers
import mass_function
import overdensity
import plotting
import rho_bar
import setup
from constants import (MASS_FUNCTION_KEY, OVERDENSITIES_KEY, RHO_BAR_KEY,
                       STD_DEV_KEY)

CACHE = caching.Cache()
CONFIG = None
CURRENT_SIM_NAME = None
DATASET_CACHE = None


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation
        global CONFIG, DATASET_CACHE

        CONFIG, DATASET_CACHE = setup.setup(args)

        logger = logging.getLogger(main.__name__)

        global CURRENT_SIM_NAME

        for sim_name in CONFIG.sim_names:
            CURRENT_SIM_NAME = sim_name

            logger.info(f"Working on simulation: {sim_name}")

            # Find halos for data set
            logger.debug(
                f"Filtering halo files to look for redshifts: {CONFIG.redshifts}")
            _, _, rockstars = helpers.filter_data_files(
                CURRENT_SIM_NAME, CONFIG.redshifts)
            logger.debug(
                f"Found {len(rockstars)} rockstar files that match these redshifts")

            # Run the calculations over all the rockstar files found
            for rck in rockstars:
                tasks(rck)
                # Clear the data set cache between iterations as the
                # data isn't persistent anyway, and this saves memory
                logger.debug("Clearing dataset cache for new iteration")
                DATASET_CACHE.clear()

            # Save the dataset cache to disk...
            # TODO: Make work??
            # DATASET_CACHE.save()
            CACHE.reset()

            logger.info("DONE calculations\n")


def tasks(rck: str):
    logger = logging.getLogger(tasks.__name__)

    logger.debug(f"Working on rockstar file '{rck}'")

    logger.debug("Calculating total halo mass function")

    global CACHE, CONFIG, CURRENT_SIM_NAME, DATASET_CACHE

    mass_fn = mass_function.MassFunction(
        CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)
    od = overdensity.Overdensity(
        CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)
    rb = rho_bar.RhoBar(CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)

    # =================================================================
    # TOTAL MASS FUNCTION
    # =================================================================
    mass_fn.total_mass_function(rck)

    # =================================================================
    # RHO BAR
    # =================================================================
    try:
        rb.rho_bar(rck)
    except Exception as e:
        logger.error(e)

    # Iterate over the radii to sample for
    for radius in CONFIG.radii:

        logger.debug(
            f"Calculating overdensities and halo mass functions at a radius of '{radius}'")

        # Errors handled in code, so can ignore...
        try:
            z, masses, deltas = halo_work(rck, radius)
        except Exception as e:
            logger.error(e)
            continue

        logger.debug("Generating plot for this data...")
        plotting.plot(z,
                      radius,
                      masses,
                      deltas,
                      num_hist_bins=CONFIG.num_hist_bins,
                      num_overdensity_hist_bins=CONFIG.num_overdensity_hist_bins,
                      sim_name=CURRENT_SIM_NAME)


def halo_work(rck: str, radius: float):
    """
    Calculates the halo mass function when sampling with spheres, and the
    overdensities at the same time
    """

    logger = logging.getLogger(halo_work.__name__)

    # Ensure there is an entry in the cache for this rockstar data file
    global CACHE, CONFIG, CURRENT_SIM_NAME, DATASET_CACHE

    mass_fn = mass_function.MassFunction(
        CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)
    od = overdensity.Overdensity(
        CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)

    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift

    # =================================================================
    # OVERDENSITIES:
    # =================================================================
    logger.info("Working on overdensities:")

    # Get the number of samples needed
    num_sphere_samples = CONFIG.num_sphere_samples

    # If cache entries exist, probably don't need to recalculate
    key = (rck, OVERDENSITIES_KEY, z, float(radius))

    deltas = CACHE[key].val
    needs_recalculation = deltas is None
    # Calculation required if not enough entries cached
    if not needs_recalculation:
        amount_entries = len(deltas)
        logger.debug(
            f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")
        needs_recalculation = amount_entries < num_sphere_samples
        logger.debug(f"Need more calculations: {needs_recalculation}")
    # Could force recalculation
    needs_recalculation |= not CONFIG.use_overdensities_cache

    logger.debug(
        f"Override overdensities cache? {not CONFIG.use_overdensities_cache}")

    # If there isn't an entry for this radius sample size, need to do full sampling
    if needs_recalculation:
        logger.debug(
            f"Calculating cache values for '{OVERDENSITIES_KEY}'...")

        # Get the cached rho_bar value
        rho_bar = CACHE[rck, RHO_BAR_KEY, z].val

        # Attempt to get the existing overdensities if they exist
        existing_ods = deltas

        # Do the full sampling and save the cache to disk
        deltas = od.calc_overdensities(
            rck, radius, rho_bar, existing=existing_ods)
        CACHE[key] = deltas

    else:
        logger.debug("Using cached overdensities...")

    logger.info(f"Overdensity units: {deltas.units}")

    # =================================================================
    # STANDARD DEVIATION
    # =================================================================
    logger.debug("Working on standard deviation")

    # If the radius key is missing, need to calculate the standard deviation
    # for that radius sampling
    key = (rck, STD_DEV_KEY, z, float(radius))
    std_dev = CACHE[key].val
    if std_dev is None or not CONFIG.use_standard_deviation_cache:
        logger.debug(
            f"No standard deviation found in cache for '{STD_DEV_KEY}', calculating...")

        # Get the overdensities calculated for this radius
        od_key = (rck, OVERDENSITIES_KEY, z, float(radius))
        overdensities = CACHE[od_key].val

        std_dev = np.std(overdensities)
        CACHE[key] = std_dev

    else:
        logger.debug("Standard deviation already cached.")

    logger.info(f"Overdensities standard deviation is {std_dev}")

    # =================================================================
    # MASS FUNCTION:
    # =================================================================
    logger.info("Working on mass function:")

    # If cache entries exist, may not need to recalculate
    key = (rck, MASS_FUNCTION_KEY, z, float(radius))
    masses = CACHE[key].val
    needs_recalculation = masses is None
    # run calculation if not enough values cached
    if not needs_recalculation:
        amount_entries = len(masses)
        logger.debug(
            f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")
        needs_recalculation = amount_entries < num_sphere_samples
        logger.debug(f"Need more calculations: {needs_recalculation}")
    # Could force recalculation
    needs_recalculation |= not CONFIG.use_masses_cache

    logger.debug(f"Override masses cache? {not CONFIG.use_masses_cache}")

    # If the radius key is missing, need to do a full sample run
    if needs_recalculation:
        logger.debug(
            f"Calculating cache values for '{MASS_FUNCTION_KEY}'...")

        # Try get existing masses
        existing_ms = masses

        # Run the full sample, and save the result to the cache
        masses = mass_fn.sample_masses(rck, radius, existing=existing_ms)
        CACHE[key] = masses

    # The key can exist, but there may not be enough samples...
    else:
        logger.debug("Using cached halo masses...")

    # Get the cached redshift for this data set file
    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift
    # Get the values from the cache, and truncate the lists to the desired number of values
    # if there are too many
    masses = masses[:num_sphere_samples]
    deltas = deltas[:num_sphere_samples]

    logger.info(f"Mass units are: {masses.units}")

    return z, masses, deltas


if __name__ == "__main__":
    # Drop the program name from the sys.args
    main(sys.argv[1:])
