import json
import logging
import logging.config
import os

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
import yt.extensions.legacy

import helpers
from constants import (DESIRED_RADII, DESIRED_REDSHIFTS, LOG_FILENAME,
                       MASS_FN_PLOTS_DIR, MASS_FN_PLOTS_FNAME_PTRN,
                       NUM_HIST_BINS, NUM_OVERDENSITY_HIST_BINS,
                       NUM_SPHERE_SAMPLES, OVERDENSITY_PLOTS_DIR,
                       OVERDENSITY_PLOTS_FNAME_PTRN, ROOT, SIM_FOLDER,
                       SIM_NAME, sim_regex)


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
        _, _, rockstars = helpers.filter_data_files(SIM_NAME, DESIRED_REDSHIFTS)
        logger.debug(
            f"Found {len(rockstars)} rockstar files that match these redshifts")

        for rck in rockstars:
            logger.debug(f"Working on rockstar file '{rck}'")

            total_mass_function(rck)

            for radius in DESIRED_RADII:
                z, masses, deltas = halo_work(rck, radius)

                logger.debug("Generating plot for this data...")
                plot(z, radius, masses, deltas, sim_name=SIM_NAME)

        logger.info("DONE calculations\n")


def total_mass_function(rck):
    if not yt.is_root():
        return

    logger = logging.getLogger(total_mass_function.__name__)

    logger.debug("Calculating total mass function:")

    ds = yt.load(rck)
    try:
        ad = ds.all_data()
    except TypeError as te:
        logger.error("error reading all_data(), ignoring...")
        logger.error(te)
        return

    masses = ad["halos", "particle_mass"].to(ds.units.Msun / ds.units.h)

    hist, bins = np.histogram(masses)

    z = ds.current_redshift
    a = 1 / (1+z)

    V = (ds.domain_width[0] * a)**3
    hist = hist / V

    title = f"Total Mass Function for @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(SIM_NAME)
    plot_name = (MASS_FN_PLOTS_DIR +
                 "total_mass_function_z{1:.2f}.png").format(SIM_FOLDER, z)

    plot_mass_function(hist, bins, title, save_dir, plot_name)


def halo_work(rck: str, radius: float):
    logger = logging.getLogger(halo_work.__name__)

    ds = yt.load(rck)

    dist_units = ds.units.Mpc / ds.units.h
    R = radius * dist_units

    z = ds.current_redshift
    a = 1/(1+z)

    logger.debug(f"Redshift z={z}")

    V = 4/3 * np.pi * (a*R)**3

    sim_size = (ds.domain_width[0]).to(dist_units)
    logger.debug(f"Simulation size = {sim_size}")

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = rand_coords(
        NUM_SPHERE_SAMPLES, min=coord_min, max=coord_max) * dist_units

    masses = unyt.unyt_array([], ds.units.Msun/ds.units.h)
    deltas = []

    # Try to get the entire dataset region
    try:
        ad = ds.all_data()
    except TypeError as te:
        logger.error("error getting all dataset region")
        logger.error(te)
        return z, unyt.unyt_array(masses), unyt.unyt_array(deltas)

    # Get the average density over the region
    try:
        rho_bar = ad.quantities.total_mass()[1] / (sim_size*a)**3
    except unyt.exceptions.IterableUnitCoercionError as te:
        logger.error(
            "Error reading regions quantities from database, ignoring...")
        logger.error(te)

    # Iterate over all the randomly sampled coordinates
    for c in yt.parallel_objects(coords):
        logger.debug(
            f"Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        # Try to sample a sphere of the given radius at this coord
        try:
            sp = ds.sphere(c, R)
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

        # Try to calculate the overdensity of the sphere
        try:
            rho = sp.quantities.total_mass()[1] / V
            delta = (rho - rho_bar) / rho_bar
            deltas.append(delta)
        except unyt.exceptions.IterableUnitCoercionError as te:
            logger.error("Error reading sphere quantities, ignoring...")
            logger.error(te)

    logger.info(f"DONE reading {NUM_SPHERE_SAMPLES} sphere samples\n")

    return z, masses, unyt.unyt_array(deltas)


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def plot(z, radius, masses, deltas, sim_name="default"):
    if not yt.is_root():
        return

    logger = logging.getLogger(plot.__name__)

    mass_hist, mass_bin_edges = np.histogram(masses, bins=NUM_HIST_BINS)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    mass_hist = mass_hist / V

    logger.debug(f"Plotting mass function at z={z:.2f}...")

    title = f"Mass Function for {sim_name} @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(sim_name)
    plot_name = MASS_FN_PLOTS_FNAME_PTRN.format(sim_name, radius, z)

    plot_mass_function(mass_hist, mass_bin_edges, title, save_dir, plot_name)

    logger.debug(f"Plotting overdensities at z={z:.2f}...")

    title = f"Overdensity for {sim_name} @ z={z:.2f}"
    save_dir = OVERDENSITY_PLOTS_DIR.format(sim_name)
    plot_name = OVERDENSITY_PLOTS_FNAME_PTRN.format(sim_name, radius, z)
    plot_delta(deltas, title, save_dir, plot_name)


def plot_mass_function(hist, bin_edges, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    x = np.log(bin_edges[:-1])
    y = np.log(hist)

    plt.plot(x, y)
    plt.gca().set_xscale("log")

    plt.title(title)
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()


def plot_delta(deltas, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    plt.hist(deltas, bins=NUM_OVERDENSITY_HIST_BINS)

    plt.title(title)
    plt.xlabel("Overdensity value")
    plt.ylabel("Overdensity $\delta$")

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()


if __name__ == "__main__":
    main()
