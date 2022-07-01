#!/usr/bin/env python3
import logging
import logging.config
import os
import sys
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import yaml
import yt

import caching
import configuration
import dataset_cacher
import helpers
from constants import (LOG_FILENAME, MASS_FN_PLOTS_DIR,
                       MASS_FN_PLOTS_FNAME_PTRN, MASS_FUNCTION_KEY,
                       PATH_TO_CALCULATIONS_CACHE, PRESS_SCHECHTER_KEY,
                       REDSHIFT_KEY, RHO_BAR_0_KEY, STD_DEV_KEY, UNITS_KEY,
                       UNITS_PS_MASS, UNITS_PS_STD_DEV)

CACHE = caching.Cache()
DATASET_CACHE = dataset_cacher.new()

DELTA_CRIT = 1.686


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

            # Save the dataset cache to disk...
            DATASET_CACHE.save()

            logger.info("DONE calculations\n")


def tasks(rck):

    logger = logging.getLogger(tasks.__name__)

    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift

    # =================================================================
    # CALCULATING RHO BAR 0
    # =================================================================

    rho_0 = CACHE[rck, RHO_BAR_0_KEY, z].val
    if rho_0 is None or not CONFIG.use_rho_bar_cache:
        logger.debug(
            f"No entries found in cache for '{RHO_BAR_0_KEY}', calculating...")
        ds = DATASET_CACHE.load(rck)
        try:
            ad = DATASET_CACHE.all_data(rck)
        except TypeError as te:
            logger.error("Error reading all_data()")
            logger.error(te)
            return

        simulation_total_mass = ad.quantities.total_mass()[1].to(ds.units.Msun)
        simulation_size = ds.domain_width[0].to(ds.units.Mpc)
        simulation_volume = simulation_size ** 3
        rho_0 = simulation_total_mass / simulation_volume

        CACHE[rck, RHO_BAR_0_KEY, z] = rho_0

    else:
        logger.debug("Using cached 'rho_bar_0' value...")

    logger.info(f"Simulation average density is: {rho_0}")

    # =================================================================
    # PRESS SCHECHTER MASS FUNCTION
    # =================================================================

    press_schechter = CACHE[rck, PRESS_SCHECHTER_KEY, z].val
    if press_schechter is None or not CONFIG.use_press_schechter_cache:
        logger.debug(
            f"No press-schechter values cached for '{rck}' data set, caching...")

        std_dev_map = _std_dev_func_mass(rck)
        press_schechter = {}

        masses = np.array(list(std_dev_map.keys()))
        std_devs = np.array(list(std_dev_map.values()))

        frac = np.abs(np.log(std_devs) / np.log(masses))

        ps = np.sqrt(2 / np.pi) * (rho_0 / masses**2) * DELTA_CRIT / \
            std_devs * frac * np.exp(-DELTA_CRIT / (2 * std_devs**2))

        logger.debug(f"Press-Schechter mass function units are: {ps.units}")

        # Match up the entries into the dictionary
        for i in range(len(masses)):
            press_schechter[masses[i]] = ps[i]

        CACHE[rck, PRESS_SCHECHTER_KEY, z] = press_schechter

    else:
        logger.debug("Using cached press schechter values...")

    # =================================================================
    # PLOTTING
    # =================================================================
    plot_mass_function(z, press_schechter)


def _std_dev_func_mass(rck):
    logger = logging.getLogger(_std_dev_func_mass.__name__)

    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift

    std_dev_radii = CACHE[rck, STD_DEV_KEY, z].val
    if std_dev_radii is None:
        logger.warning(
            f"No standard deviations calculated for data set '{rck}'")
        return

    mass_radii = CACHE[rck, MASS_FUNCTION_KEY, z].val
    if mass_radii is None:
        logger.warning(f"No masses calculated for data set '{rck}'")
        return

    matching_radii = [r for r in std_dev_radii if r in mass_radii]

    logger.debug(f"Matching mass to std dev for the radii: {matching_radii}")

    std_dev_map = {}

    key = (rck, MASS_FUNCTION_KEY, z, float(radius))
    for radius in sorted(matching_radii):
        total_mass = np.sum(CACHE[key].val)
        std_dev = CACHE[rck, STD_DEV_KEY, z, float(radius)]

        # Ensure that mass units are consistent
        mass_units = CACHE[rck, UNITS_KEY, z, UNITS_PS_MASS].val
        if mass_units is None:
            CACHE[rck, UNITS_KEY, z, UNITS_PS_MASS] = total_mass.units
            logger.debug(f"Cached mass units as: {total_mass.units}")

        total_mass = total_mass.to(mass_units)

        # Ensure that std dev units are consistent:
        std_dev_units = CACHE[rck, UNITS_KEY, z, UNITS_PS_STD_DEV].val
        if std_dev_units is None:
            CACHE[rck, UNITS_KEY, z, UNITS_PS_STD_DEV] = std_dev.units
            logger.debug(f"Cached std dev units as: {std_dev.units}")

        std_dev = std_dev.to(std_dev_units)

        mass_value = float(total_mass.v)

        std_dev_map[mass_value] = float(std_dev)
        # if mass_value not in std_dev_map:
        #     std_dev_map[mass_value] = np.array([std_dev])
        # else:
        #     std_dev_map[mass_value] = np.concatenate((std_dev_map[mass_value], [std_dev]))

    return std_dev_map


def plot_mass_function(z, ps: Dict):
    logger = logging.getLogger(plot_mass_function.__name__)
    logger.info(f"Generating figure for redshift {z}")

    x = np.array(list(ps.keys()))
    y = np.array(list(ps.values()))

    fig = plt.figure()
    ax = fig.gca()

    ax.plot(np.log10(x), np.log10(y))
    fig.suptitle(f"Press Schecter Mass Function at z={z:.2f}")

    # ax = plt.gca()
    # ax.set_xscale("log")
    # ax.set_yscale("log")

    ax.set_xlabel("$\log{M_{vir}}$")
    ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

    save_dir = MASS_FN_PLOTS_DIR.format(CURRENT_SIM_NAME)
    PS_MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
        "press_schechter_mass_function_z{1:.2f}.png"
    plot_name = PS_MASS_FN_PLOTS_FNAME_PTRN.format(CURRENT_SIM_NAME, z)

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    fig.savefig(plot_name)

    logger.debug(f"Saved mass function figure to '{plot_name}'")


if __name__ == "__main__":
    main(sys.argv[1:])
