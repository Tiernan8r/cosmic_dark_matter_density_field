#!/usr/bin/env python3
import logging
import logging.config
import os
import sys
from typing import Tuple

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import yt

from src import data
from src.calc import mass_function, overdensity, rho_bar
from src.const.constants import (MASS_FUNCTION_KEY, OVERDENSITIES_KEY,
                                 STD_DEV_KEY)
from src.init import setup
from src.plot import plotting
from src.util import helpers


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation

        d = setup.setup(args)

        logger = logging.getLogger(main.__name__)

        # Iterate over the simulations
        for sim_name in d.config.sim_data.simulation_names:
            d.sim_name = sim_name

            logger.info(f"Working on simulation: {d.sim_name}")

            # Find halos for data set
            logger.debug(
                f"Filtering halo files to look for redshifts: {d.config.redshifts}")
            _, _, rockstars = helpers.filter_data_files(
                d.sim_name, d.config.sim_data.root, d.config.redshifts)
            logger.debug(
                f"Found {len(rockstars)} rockstar files that match these redshifts")

            # Run the calculations over all the rockstar files found
            for rck in rockstars:
                tasks(rck, d)
                # Clear the data set cache between iterations as the
                # data isn't persistent anyway, and this saves memory
                logger.debug("Clearing dataset cache for new iteration")
                d.dataset_cache.clear()

            d.cache.reset()

            logger.info("DONE calculations\n")


def tasks(rck: str, d: data.Data):
    logger = logging.getLogger(tasks.__name__)

    logger.debug(f"Working on rockstar file '{rck}'")

    logger.debug("Calculating total halo mass function")

    mass_fn = mass_function.MassFunction(d)
    rb = rho_bar.RhoBar(d)

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
    for radius in d.config.radii:

        logger.debug(
            f"Calculating overdensities and halo mass functions at a radius of '{radius}'")

        # Errors handled in code, so can ignore...
        try:
            z, mass_hist, bin_edges, deltas = halo_work(rck, radius, d)
        except Exception as e:
            logger.error(e)
            continue

        logger.debug("Generating plots for this data...")

        plotting.plot_overdensities(
            z, radius, deltas, d.sim_name, d.config.sampling.num_od_hist_bins)
        plotting.plot_mass_function(
            z, radius, mass_hist, bin_edges, d.sim_name)


def halo_work(rck: str, radius: float, d: data.Data):
    """
    Calculates the halo mass function when sampling with spheres, and the
    overdensities at the same time
    """

    ds = d.dataset_cache.load(rck)
    z = ds.current_redshift

    # Get the number of samples needed
    num_sphere_samples = d.config.sampling.num_sp_samples

    deltas = overdensities(rck, radius, d)
    std_dev = standard_deviation(rck, radius, d)
    mass_hist, bin_edges = mass_fn(rck, radius, d)

    # Get the values from the cache, and truncate the lists to the desired number of values
    # if there are too many
    mass_hist = mass_hist[:num_sphere_samples]
    bin_edges = bin_edges[:num_sphere_samples]
    deltas = deltas[:num_sphere_samples]

    return z, mass_hist, bin_edges, deltas


def overdensities(rck: str, radius: float, d: data.Data):
    logger = logging.getLogger(overdensities.__name__)

    od = overdensity.Overdensity(d)

    # =================================================================
    # OVERDENSITIES:
    # =================================================================
    logger.info("Working on overdensities:")

    ds = d.dataset_cache.load(rck)
    z = ds.current_redshift

    # Get the number of samples needed
    num_sphere_samples = d.config.sampling.num_sp_samples

    # If cache entries exist, probably don't need to recalculate
    key = (rck, OVERDENSITIES_KEY, z, float(radius))

    # Determine if new entries need to be calculates
    deltas = d.cache[key].val
    needs_recalculation = deltas is None
    # Calculation required if not enough entries cached
    if not needs_recalculation:
        amount_entries = len(deltas)
        logger.debug(
            f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")
        needs_recalculation = amount_entries < num_sphere_samples
        logger.debug(f"Need more calculations: {needs_recalculation}")
    # Could force recalculation
    needs_recalculation |= not d.config.caches.use_overdensities_cache

    logger.debug(
        f"Override overdensities cache? {not d.config.caches.use_overdensities_cache}")

    # Calculate if required...
    if needs_recalculation:
        # Do the full sampling and save the cache to disk
        deltas = od.calc_overdensities(rck, radius)

    else:
        logger.debug("Using cached overdensities...")

    logger.info(f"Overdensity units: {deltas.units}")

    return deltas


def standard_deviation(rck: str, radius: float, d: data.Data):
    logger = logging.getLogger(standard_deviation.__name__)

    # =================================================================
    # STANDARD DEVIATION
    # =================================================================
    logger.debug("Working on standard deviation")

    ds = d.dataset_cache.load(rck)
    z = ds.current_redshift

    # If the radius key is missing, need to calculate the standard deviation
    # for that radius sampling
    key = (rck, STD_DEV_KEY, z, float(radius))
    std_dev = d.cache[key].val
    if std_dev is None or not d.config.caches.use_standard_deviation_cache:
        logger.debug(
            f"No standard deviation found in cache for '{STD_DEV_KEY}', calculating...")

        # Get the overdensities calculated for this radius
        od_key = (rck, OVERDENSITIES_KEY, z, float(radius))
        overdensities = d.cache[od_key].val

        std_dev = np.std(overdensities)
        d.cache[key] = std_dev

    else:
        logger.debug("Standard deviation already cached.")

    logger.info(f"Overdensities standard deviation is {std_dev}")

    return std_dev


def mass_fn(rck: str, radius: float, d: data.Data) -> Tuple[np.ndarray, np.ndarray]:
    logger = logging.getLogger(mass_fn.__name__)

    mf = mass_function.MassFunction(d)

    # =================================================================
    # MASS FUNCTION:
    # =================================================================
    logger.info("Working on mass function:")

    ds = d.dataset_cache.load(rck)
    z = ds.current_redshift

    # Get the number of samples needed
    num_sphere_samples = d.config.sampling.num_sp_samples

    # If cache entries exist, may not need to recalculate
    key = (rck, MASS_FUNCTION_KEY, z, float(radius))
    masses = d.cache[key].val
    needs_recalculation = masses is None
    # run calculation if not enough values cached
    if not needs_recalculation:
        amount_entries = len(masses)
        logger.debug(
            f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")
        needs_recalculation = amount_entries < num_sphere_samples
        logger.debug(f"Need more calculations: {needs_recalculation}")
    # Could force recalculation
    needs_recalculation |= not d.config.caches.use_masses_cache

    logger.debug(
        f"Override masses cache? {not d.config.caches.use_masses_cache}")

    # If the radius key is missing, need to do a full sample run
    if needs_recalculation:
        logger.debug(
            f"Calculating cache values for '{MASS_FUNCTION_KEY}'...")

        # Run the full sample, and save the result to the cache
        masses = mf.sample_masses(rck, radius)
        d.cache[key] = masses

    # The key can exist, but there may not be enough samples...
    else:
        logger.debug("Using cached halo masses...")

    logger.info(f"Mass units are: {masses.units}")

    mass_hist, mass_bin_edges = np.histogram(
        masses, bins=d.config.sampling.num_hist_bins)

    # Filter hist/bins for non-zero masses
    valid_idxs = np.where(mass_hist > 0)
    mass_hist = mass_hist[valid_idxs]
    mass_bin_edges = mass_bin_edges[valid_idxs]

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3 * num_sphere_samples

    mass_hist = mass_hist / V

    return mass_hist, mass_bin_edges


if __name__ == "__main__":
    # Drop the program name from the sys.args
    main(sys.argv[1:])
