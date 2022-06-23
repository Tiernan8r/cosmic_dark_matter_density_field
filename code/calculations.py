import logging
import logging.config
import os
import re

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
import yt.extensions.legacy
import yaml

import helpers

LOG_FILENAME = "logging.yaml"

ROOT = "/disk12/legacy/"
SIM_NAME = "GVD_C700_l1600n2048_SLEGAC"
SIM_FOLDER = f"{SIM_NAME}/"

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")

NUM_SPHERE_SAMPLES = 1000
NUM_HIST_BINS = 1000
NUM_OVERDENSITY_HIST_BINS = 1000

MASS_FN_PLOTS_DIR = "../plots/mass_function/{0}/"
MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
    "mass_function_r{1:.2f}-z{2:.2f}.png"

OVERDENSITY_PLOTS_DIR = "../plots/deltas/{0}/"
OVERDENSITY_PLOTS_FNAME_PTRN = OVERDENSITY_PLOTS_DIR + \
    "overdensity_r{1:.2f}-z{2:.2f}.png"

DESIRED_REDSHIFTS = [0, 1, 2, 6, 10]
DESIRED_RADII = [50]
# DESIRED_RADII = [10, 20, 50, 100]


def setup_logging() -> logging.Logger:
    logging_path = os.path.abspath(LOG_FILENAME)
    with open(logging_path) as f:
        dict_config = yaml.load(f, Loader=yaml.SafeLoader)

    logging.config.dictConfig(dict_config)

    logger = logging.getLogger(__name__)

    return logger


LOGGER = setup_logging()


def main():
    pth = ROOT + SIM_FOLDER
    LOGGER.debug(f"Reading data set in '{pth}'")
    # Find halos for data set
    LOGGER.debug(
        f"Filtering halo files to look for redshifts: {DESIRED_REDSHIFTS}")
    _, _, rockstars = helpers.filter_data_files(SIM_NAME, DESIRED_REDSHIFTS)
    LOGGER.debug(
        f"Found {len(rockstars)} rockstar files that match these redshifts")

    simulation_name = sim_regex.match(pth).group(1)
    sim_size = float(sim_regex.match(pth).group(3))

    for rck in rockstars:
        LOGGER.debug(f"Working on rockstar file '{rck}'")

        total_mass_function(rck, sim_size)

        for radius in DESIRED_RADII:
            z, masses, deltas = halo_work(rck, radius)

            LOGGER.debug("Generating plot for this data...")
            plot(z, radius, masses, deltas, sim_name=simulation_name)

    LOGGER.info("DONE calculations\n")


def total_mass_function(rck, sim_size):
    LOGGER.debug("Calculating total mass function:")
    ds = yt.load(rck)
    try:
        ad = ds.all_data()
    except TypeError as te:
        LOGGER.error("error reading all_data(), ignoring...")
        LOGGER.error(te)
        return

    masses = ad["halos", "particle_mass"]

    hist, bins = np.histogram(masses)

    z = ds.current_redshift
    a = 1 / (1+z)

    V = (sim_size * a)**3
    hist = hist / V

    title = f"Total Mass Function for @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(SIM_NAME)
    plot_name = (MASS_FN_PLOTS_DIR +
                 "total_mass_function_z{1:.2f}.png").format(SIM_FOLDER, z)

    plot_mass_function(hist, bins, title, save_dir, plot_name)


def halo_work(rck: str, radius: float):
    ds = yt.load(rck)

    dist_units = ds.units.Mpc / ds.units.h
    R = radius * dist_units

    z = ds.current_redshift
    a = 1/(1+z)

    LOGGER.debug(f"Redshift z={z}")

    V = 4/3 * np.pi * (a*R)**3

    sim_size = (ds.domain_width[0]).to(dist_units)
    LOGGER.debug(f"Simulation size = {sim_size}")

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
        LOGGER.error("error getting all dataset region")
        LOGGER.error(te)
        return z, unyt.unyt_array(masses), unyt.unyt_array(deltas)

    # Get the average density over the region
    try:
        rho_bar = ad.quantities.total_mass()[1] / (sim_size*a)**3
    except unyt.exceptions.IterableUnitCoercionError as e:
        LOGGER.error(
            "Error reading regions quantities from database, ignoring...")
        LOGGER.error(e)

    # Iterate over all the randomly sampled coordinates
    for c in coords:
        LOGGER.debug(
            f"Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        # Try to sample a sphere of the given radius at this coord
        try:
            sp = ds.sphere(c, R)
        except Exception as e:
            LOGGER.error("error creating sphere sample")
            LOGGER.error(e)
            continue

        # Try to read the masses of halos in this sphere
        try:
            m = sp["halos", "particle_mass"]
        except Exception as e:
            LOGGER.error("error reading sphere total_mass()")
            LOGGER.error(e)
            continue

        LOGGER.debug(f"Found {len(m)} halos in this sphere sample")

        masses = unyt.uconcatenate((masses, m))

        # Try to calculate the overdensity of the sphere
        try:
            rho = sp.quantities.total_mass()[1] / V
            delta = (rho - rho_bar) / rho_bar
            deltas.append(delta)
        except unyt.exceptions.IterableUnitCoercionError as e:
            LOGGER.error("Error reading sphere quantities, ignoring...")
            LOGGER.error(e)

    LOGGER.info(f"DONE reading {NUM_SPHERE_SAMPLES} sphere samples\n")

    return z, masses, unyt.unyt_array(deltas)


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def plot(z, radius, masses, deltas, sim_name="default"):
    mass_hist, mass_bin_edges = np.histogram(masses, bins=NUM_HIST_BINS)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    mass_hist = mass_hist / V

    LOGGER.debug(f"Plotting mass function at z={z:.2f}...")

    title = f"Mass Function for {sim_name} @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(sim_name)
    plot_name = MASS_FN_PLOTS_FNAME_PTRN.format(sim_name, radius, z)

    plot_mass_function(mass_hist, mass_bin_edges, title, save_dir, plot_name)

    LOGGER.debug(f"Plotting overdensities at z={z:.2f}...")

    title = f"Overdensity for {sim_name} @ z={z:.2f}"
    save_dir = OVERDENSITY_PLOTS_DIR.format(sim_name)
    plot_name = OVERDENSITY_PLOTS_FNAME_PTRN.format(sim_name, radius, z)
    plot_delta(deltas, title, save_dir, plot_name)


def plot_mass_function(hist, bin_edges, title, save_dir, plot_f_name):
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
