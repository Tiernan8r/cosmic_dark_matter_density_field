#!/usr/bin/env python3
import logging
import logging.config
import os
import sys
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt

import caching
import dataset_cacher
import helpers
import plotting
import rho_bar
import setup
import standard_deviation
from constants import MASS_FN_PLOTS_DIR, PRESS_SCHECHTER_KEY

CACHE = caching.Cache()
CONFIG = None
CURRENT_SIM_NAME = None
DATASET_CACHE = dataset_cacher.new()
DELTA_CRIT = 1.686


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation
        global CONFIG, DATASET_CACHE, CURRENT_SIM_NAME
        CONFIG, DATASET_CACHE = setup.setup(args)

        logger = logging.getLogger(main.__name__)

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
            # DATASET_CACHE.save()

            logger.info("DONE calculations\n")


def tasks(rck):
    global CACHE, CONFIG, CURRENT_SIM_NAME, DATASET_CACHE

    logger = logging.getLogger(tasks.__name__)

    ds = DATASET_CACHE.load(rck)
    z = ds.current_redshift
    logger.info(f"Redshift is: {z}")

    rb = rho_bar.RhoBar(CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)
    std_dev = standard_deviation.StandardDeviation(
        CONFIG, DATASET_CACHE, CACHE, CURRENT_SIM_NAME)

    rho_0 = rb.rho_bar_0(rck)
    if rho_0 is None:
        logger.warning(f"Could not calculate rho bar 0!")
        return

    logger.info(f"Simulation average density is: {rho_0}")

    # =================================================================
    # PRESS SCHECHTER MASS FUNCTION
    # =================================================================

    press_schechter = CACHE[rck, PRESS_SCHECHTER_KEY, z].val
    if press_schechter is None or not CONFIG.use_press_schechter_cache:
        logger.debug(
            f"No press-schechter values cached for '{rck}' data set, caching...")

        std_dev_map = std_dev.std_dev_func_mass(rck)
        if std_dev_map is None:
            logger.warn(
                f"No standard deviations mapped for this redshift, stopping...")
            return

        press_schechter = {}

        masses = np.array(list(std_dev_map.keys()))
        std_devs = np.array(list(std_dev_map.values()))

        frac = np.abs(np.log(std_devs) / np.log(masses))

        ps = np.sqrt(2 / np.pi) * (rho_0 / masses**2) * DELTA_CRIT / \
            std_devs * frac * np.exp(-DELTA_CRIT / (2 * std_devs**2))

        if isinstance(ps, unyt.unyt_array):
            logger.debug(
                f"Press-Schechter mass function units are: {ps.units}")

        # Match up the entries into the dictionary
        for i in range(len(masses)):
            press_schechter[masses[i]] = ps[i]

        CACHE[rck, PRESS_SCHECHTER_KEY, z] = press_schechter

    else:
        logger.debug("Using cached press schechter values...")

    # =================================================================
    # PLOTTING
    # =================================================================
    title = f"Press Schecter Mass Function at z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(CURRENT_SIM_NAME)
    PS_MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
        "press_schechter_mass_function_z{1:.2f}.png"
    plot_name = PS_MASS_FN_PLOTS_FNAME_PTRN.format(CURRENT_SIM_NAME, z)

    plotting.ps_mass_function(z, press_schechter, title, save_dir, plot_name)


if __name__ == "__main__":
    main(sys.argv[1:])
