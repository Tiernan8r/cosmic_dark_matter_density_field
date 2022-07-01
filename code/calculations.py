#!/usr/bin/env python3
import logging
import logging.config
import os
import sys

import numpy as np
import unyt
import yaml
import yt
import yt.extensions.legacy

import caching
import configuration
import coordinates
import dataset_cacher
import helpers
import plotting
from constants import (LOG_FILENAME, MASS_FN_PLOTS_DIR, MASS_FUNCTION_KEY,
                       OVERDENSITIES_KEY, REDSHIFT_KEY, RHO_BAR_KEY,
                       STD_DEV_KEY, TOTAL_MASS_FUNCTION_KEY)

CACHE = caching.Cache()
DATASET_CACHE = dataset_cacher.new()


def setup_logging() -> logging.Logger:
    logging_path = os.path.abspath(LOG_FILENAME)
    with open(logging_path) as f:
        dict_config = yaml.safe_load(f)

    logging.config.dictConfig(dict_config)


CONFIG = configuration.Configuration()
CURRENT_SIM_NAME = None


def setup(args):
    setup_logging()
    logger = logging.getLogger(setup.__name__)

    logger.debug("Logging initialised")

    # Read the configuration file from the args if provided.
    global CONFIG
    CONFIG = configuration.new(args)

    logger.debug(f"Configuration read from file '{CONFIG._config_file}'")

    yt.enable_parallelism()
    logger.info("Parallelism enabled...")

    logger.debug(f"Reading data set(s) in: {CONFIG.paths}")


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation
        setup(args)
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

    # =================================================================
    # TOTAL MASS FUNCTION
    # =================================================================
    total_mass_function(rck)

    # =================================================================
    # RHO BAR
    # =================================================================
    try:
        rho_bar(rck)
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


def total_mass_function(rck):
    # Only need to run this once per file, so run only on root
    if not yt.is_root():
        return

    logger = logging.getLogger(total_mass_function.__name__)

    logger.debug("Calculating total mass function...")

    # Load in the rockstar data set, potentially from a cache to optimise it
    ds = DATASET_CACHE.load(rck)

    # Get the redshift from the data set
    z = ds.current_redshift

    # Cache the masses if they are not already
    _cache_total_mass_function(rck)

    # Get the cached values, the _cache_total_mass_function() method can error,
    # so need to use the get() notation
    masses = CACHE[rck, TOTAL_MASS_FUNCTION_KEY, z].val
    if masses is None:
        logger.debug("Skipping plotting this total mass function...")
        return

    if len(masses) > 0:
        logger.info(f"Mass units are: {masses.units}")

    bin_min = np.log10(np.min(masses))
    bin_max = np.log10(np.max(masses))
    log_bins = np.logspace(bin_min, bin_max, CONFIG.num_hist_bins)

    # Calculate the histogram of the masses
    hist, bins = np.histogram(masses, bins=log_bins)

    # Filter hist/bins for non-zero masses
    valid_idxs = np.where(hist > 0)
    hist = hist[valid_idxs]
    bins = bins[valid_idxs]

    # Calculate the scale factor
    a = 1 / (1+z)

    # Calculate the area of the box (is a cube)
    sim_size = ds.domain_width[0].to(ds.units.Mpc)
    V = (a * sim_size)**3

    logger.info(f"Volume units are: {V.units}")

    # Divide the number of halos per bin by the volume to get the number density
    hist = hist / V

    # Set the parameters used for the plotting & plot the mass function
    title = f"Total Mass Function for z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(CURRENT_SIM_NAME)
    plot_name = (MASS_FN_PLOTS_DIR +
                 "total_mass_function_z{1:.2f}.png").format(CURRENT_SIM_NAME, z)

    plotting.plot_mass_function(hist, bins, title, save_dir, plot_name)


def _cache_total_mass_function(rck: str):
    """
    Runs the calculations of halo masses for the entire data set and caches the results
    """

    logger = logging.getLogger(_cache_total_mass_function.__name__)

    logger.debug("Calculating total mass function...")

    # Ensure that the cache contains the data needed
    global CACHE

    # Load in the rockstar data set, potentially from a cache to optimise it
    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift

    # If key is in cache, doesn't neet recalculation
    masses = CACHE[rck, TOTAL_MASS_FUNCTION_KEY, z].val
    logger.debug(
        f"Override total mass cache? {not CONFIG.use_total_masses_cache}")

    # If a value for the calculation doesn't exist in the cache, need to calculate it...
    if masses is None or not CONFIG.use_total_masses_cache:

        logger.debug(f"No masses cached for '{rck}' data set, caching...")

        # Try to read all the particle data from the data set (can error with the earlier
        # redshift data sets due to box issues??)
        try:
            ad = DATASET_CACHE.all_data(rck)
        except TypeError as te:
            logger.error("error reading all_data(), ignoring...")
            logger.error(te)
            return

        # Get the halo virial masses from the data
        masses = ad["halos", "particle_mass"]

        # Also store the redshift of this data set if it isn't cached already
        z = ds.current_redshift

        # Cache the calculated values, and save the cache to disk
        CACHE[rck, TOTAL_MASS_FUNCTION_KEY, z] = masses

    else:
        logger.debug("Using cached masses in plots...")


def rho_bar(rck):
    logger = logging.getLogger(halo_work.__name__)

    # Ensure there is an entry in the cache for this rockstar data file
    global CACHE

    # =================================================================
    # RHO BAR:
    # =================================================================
    logger.info("Working on rho_bar value:")

    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift

    # Calculate the density of the entire region if is not cached...
    rho_bar = CACHE[rck, RHO_BAR_KEY, z].val
    if rho_bar is None or not CONFIG.use_rho_bar_cache:
        logger.debug(
            f"No entries found in cache for '{RHO_BAR_KEY}', calculating...")

        # Try to calculate the rho_bar value
        try:
            rho_bar = _calc_rho_bar(rck)
        # Can error on some of the earlier redshift data sets due to region bounding issues
        # (don't know exactly why though...)
        except TypeError as te:
            logger.error("error getting all dataset region")
            logger.error(te)
            raise te
        # Can also error when the IGM is tagged as being dimensionless rather than 0g...
        except unyt.exceptions.IterableUnitCoercionError as iuce:
            logger.error(
                "Error reading regions quantities from database, ignoring...")
            logger.error(iuce)
            raise iuce

        # Cache the result
        CACHE[rck, RHO_BAR_KEY, z] = rho_bar

    else:
        logger.debug("Using cached 'rho_bar' value...")

    logger.info(f"Average density calculated as: {rho_bar}")
    logger.info(f"Density units are: {rho_bar.units}")


def _calc_rho_bar(rck):
    """
    Calculates the overdensity of the entire data set
    """
    logger = logging.getLogger(_calc_rho_bar.__name__)

    # Load the data set, if it is cached already this operation will be faster...
    ds = DATASET_CACHE.load(rck)

    # Get the distance units used in the code
    dist_units = ds.units.Mpc / ds.units.h

    # Ensure the redshift is cached for this data set
    global CACHE

    z = ds.current_redshift

    # Calculate the scale factor
    a = 1/(1+z)

    logger.debug(f"Redshift z={z}")

    # Get the size of one side of the box
    sim_size = (ds.domain_width[0]).to(dist_units)
    logger.debug(f"Simulation size = {sim_size}")

    # Get the entire dataset region, can be cached for performance
    # optimisation
    ad = DATASET_CACHE.all_data(rck)

    # Get the average density over the region
    total_mass = ad.quantities.total_mass()[1]
    volume = (sim_size * a)**3

    rho_bar = total_mass / volume

    logger.debug(f"Calculated a rho_bar of '{rho_bar}' for dataset '{rck}'")

    return rho_bar


def halo_work(rck: str, radius: float):
    """
    Calculates the halo mass function when sampling with spheres, and the
    overdensities at the same time
    """

    logger = logging.getLogger(halo_work.__name__)

    # Ensure there is an entry in the cache for this rockstar data file
    global CACHE

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
        deltas = _calc_overdensities(
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
        masses = _sample_masses(rck, radius, existing=existing_ms)
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


def _calc_overdensities(rck, radius, rho_bar, existing: unyt.unyt_array = None):
    """
    Calculates the overdensities of a sample of spheres of a given radius over
    the given dataset, if there are existing samples, only calculates the extra
    samples required to get the total desired.
    """
    logger = logging.getLogger(_calc_overdensities.__name__)

    # Load the (cached?) data set
    ds = DATASET_CACHE.load(rck)

    # Get the units used in the simulation
    dist_units = ds.units.Mpc / ds.units.h
    # Convert the given radius to an unyt unit object
    R = radius * dist_units

    z = ds.current_redshift
    a = 1/(1+z)

    logger.debug(f"Redshift z={z}")

    # Calculate the volume of the spheres that we sample on in comoving units
    V = 4/3 * np.pi * (R)**3

    # Get the size of the simulation
    sim_size = (ds.domain_width[0]).to(dist_units) * a
    logger.debug(f"Simulation size = {sim_size}")

    # Since we are sampling with spheres, don't want to get a coord too close to the
    # edge of the simulation, so the sphere sample doesn't contain mostly missing
    # data
    coord_min = radius
    coord_max = sim_size.value - radius

    # Generate the random coordinates in this boundary (can be cached...)
    # The coordinates returned are persistent across calculations, so the
    # existing samples indices will match to the coordinate indices
    coords = coordinates.rand_coords(
        CONFIG.num_sphere_samples, min=coord_min, max=coord_max) * dist_units

    # If there are existing entries, truncate the number of new calculations...
    deltas = unyt.unyt_array([])
    if existing is not None:
        # Only iterate over the extra coordinates
        coords = coords[len(existing):]

        # Save the existing deltas to the list calculated on
        deltas = existing

    # Iterate over all the randomly sampled coordinates
    i = 0
    for c in yt.parallel_objects(coords):
        logger.debug(
            f"({i}) Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        i += 1

        # Try to sample a sphere of the given radius at this coord
        try:
            sp = DATASET_CACHE.sphere(rck, c, R)
        # Can error with yt unable to create the Region object (why?? who knows...)
        except TypeError as te:
            logger.error("error creating sphere sample")
            logger.error(te)
            continue

        # Try to calculate the overdensity of the sphere
        try:
            # Get the density
            rho = sp.quantities.total_mass()[1] / V
            # The overdensity
            delta = (rho - rho_bar) / rho_bar

            # Create a temporary one entry array so we can concatenate this overdensity
            # onto the total list
            d = unyt.unyt_array([delta])
            deltas = unyt.uconcatenate((deltas, d))

        # Can error on reading to quantities.total_mass() value if yt thinks that
        # the IGM is dimensionless rather than units of mass...
        except unyt.exceptions.IterableUnitCoercionError as iuce:
            logger.error("Error reading sphere quantities, ignoring...")
            logger.error(iuce)

    # Return the units array of overdensities
    return unyt.unyt_array(deltas)


def _sample_masses(rck, radius, existing: unyt.unyt_array = None):
    """
    Randomly samples the data set with spheres of the given radius to find
    halos within that sample
    """
    logger = logging.getLogger(_sample_masses.__name__)

    # Load the rockstar data set
    ds = DATASET_CACHE.load(rck)

    # Get the distance units used by the simulation
    dist_units = ds.units.Mpc / ds.units.h
    # Convert the radius to the distance units
    R = radius * dist_units

    z = ds.current_redshift

    # Get the redshift from the cache
    a = 1 / (1+z)

    logger.debug(f"Redshift z={z}")

    # Get the size of the simulation
    sim_size = (ds.domain_width[0]).to(dist_units) * a
    logger.debug(f"Simulation size = {sim_size}")

    # Bound the coordinate sampling, so that the spheres only overlap with
    # volumes within the simulation region
    coord_min = radius
    coord_max = sim_size.value - radius

    # Get the desired number of random coords for this sampling
    coords = coordinates.rand_coords(
        CONFIG.num_sphere_samples, min=coord_min, max=coord_max) * dist_units

    # Truncate the number of values to calculate, if some already exist...
    masses = unyt.unyt_array([], ds.units.Msun/ds.units.h)
    if existing is not None:
        coords = coords[len(existing):]
        masses = existing

    # Iterate over all the randomly sampled coordinates
    i = 0
    for c in yt.parallel_objects(coords):
        logger.debug(
            f"({i}) Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        i += 1

        # Try to sample a sphere of the given radius at this coord
        try:
            sp = DATASET_CACHE.sphere(rck, c, R)
        # Can error on higher redshift data sets due to sampling regions
        # erroring in yt
        except TypeError as te:
            logger.error("error creating sphere sample")
            logger.error(te)
            continue

        # Try to read the masses of halos in this sphere
        try:
            m = sp["halos", "particle_mass"]
        except TypeError as te:
            logger.error("error reading sphere halo masses")
            logger.error(te)
            continue

        logger.debug(f"Found {len(m)} halos in this sphere sample")

        # Add these masses to the list
        masses = unyt.uconcatenate((masses, m))

    logger.info(f"DONE reading {CONFIG.num_sphere_samples} sphere samples\n")

    # Convert mass units to Msun
    masses = masses.to(ds.units.Msun)

    return masses


if __name__ == "__main__":
    # Drop the program name from the sys.args
    main(sys.argv[1:])
