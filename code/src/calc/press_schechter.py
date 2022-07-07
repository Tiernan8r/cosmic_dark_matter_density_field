#!/usr/bin/env python3
import logging
import logging.config
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import src.calc.rho_bar as rho_bar
import src.calc.standard_deviation as standard_deviation
import unyt
import yt
from src import data
from src.const.constants import (MASS_FN_PLOTS_DIR, MASS_FUNCTION_KEY,
                                 PRESS_SCHECHTER_KEY)
from src.init import setup
from src.plot import plotting
from src.util import helpers

DELTA_CRIT = 1.686


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation
        d = setup.setup(args)

        logger = logging.getLogger(main.__name__)

        for sim_name in d.config.sim_data.simulation_names:
            d.sim_name = sim_name

            logger.info(f"Working on simulation: {sim_name}")

            # Find halos for data set
            logger.debug(
                f"Filtering halo files to look for redshifts: {d.config.redshifts}")
            _, _, rockstars = helpers.filter_data_files(
                d.sim_name, d.config.sim_data.root, d.config.redshifts)
            logger.debug(
                f"Found {len(rockstars)} rockstar files that match these redshifts")

            # Run the calculations over all the rockstar files found
            for rck in rockstars:
                tasks(rck)

            # Save the dataset cache to disk...
            # DATASET_CACHE.save()

            logger.info("DONE calculations\n")


def tasks(rck, d: data.Data):
    logger = logging.getLogger(tasks.__name__)

    ds = d.dataset_cache.load(rck)
    z = ds.current_redshift
    logger.info(f"Redshift is: {z}")

    rb = rho_bar.RhoBar(d)
    std_dev = standard_deviation.StandardDeviation(d)

    rho_0 = rb.rho_bar_0(rck)
    if rho_0 is None:
        logger.warning(f"Could not calculate rho bar 0!")
        return

    logger.info(f"Simulation average density is: {rho_0}")

    # =================================================================
    # PRESS SCHECHTER MASS FUNCTION
    # =================================================================

    press_schechter = d.cache[rck, PRESS_SCHECHTER_KEY, z].val
    if press_schechter is None or not d.config.caches.use_press_schechter_cache:
        logger.debug(
            f"No press-schechter values cached for '{rck}' data set, caching...")

        std_dev_map = std_dev.std_dev_func_mass(rck)
        if std_dev_map is None:
            logger.warn(
                f"No standard deviations mapped for this redshift, stopping...")
            return

        press_schechter = {}

        masses = np.array(sorted(std_dev_map.keys()))
        std_devs = np.array([std_dev_map[k] for k in masses])

        frac = np.abs(np.log(std_devs) / np.log(masses))

        ps = np.sqrt(2 / np.pi) * (rho_0 / masses**2) * DELTA_CRIT / \
            std_devs * frac * np.exp(-DELTA_CRIT / (2 * std_devs**2))

        if isinstance(ps, unyt.unyt_array):
            logger.debug(
                f"Press-Schechter mass function units are: {ps.units}")

        # Match up the entries into the dictionary
        for i in range(len(masses)):
            press_schechter[masses[i]] = ps[i]

        d.cache[rck, PRESS_SCHECHTER_KEY, z] = press_schechter

    else:
        logger.debug("Using cached press schechter values...")

    # =================================================================
    # PLOTTING
    # =================================================================
    title = f"Press Schecter Mass Function at z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(d.sim_name)
    PS_MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
        "press_schechter_mass_function_z{1:.2f}.png"
    plot_name = PS_MASS_FN_PLOTS_FNAME_PTRN.format(d.sim_name, z)

    plotting.ps_mass_function(z, press_schechter, title, save_dir, plot_name)

    for radius in d.config.radii:

        ms = d.cache[rck, MASS_FUNCTION_KEY, z, float(radius)].val
        if ms is None:
            continue

        title = f"Compared Press Schecter Mass Function at z={z:.2f}; r={radius:.0f}"
        save_dir = MASS_FN_PLOTS_DIR.format(d.sim_name)
        PS_MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
            "composite_press_schechter_mass_function_z{1:.2f}_r{2:.0f}.png"
        plot_name = PS_MASS_FN_PLOTS_FNAME_PTRN.format(
            d.sim_name, z, radius)

        plotting.plot_ps_both(z, radius, ms, d.config.sampling.num_hist_bins,
                              press_schechter, title, save_dir, plot_name)


if __name__ == "__main__":
    main(sys.argv[1:])
