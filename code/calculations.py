import os
import re

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
import yt.extensions.legacy

import helpers

ROOT = "/disk12/legacy/"
SIM_NAME = "GVD_C700_l1600n2048_SLEGAC"
SIM_FOLDER = f"{SIM_NAME}/"

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")

NUM_SAMPLES_PER_SPHERE = 10
NUM_SPHERE_SIZES = 1
NUM_HIST_BINS = 1000

MASS_FN_PLOTS_DIR = "../plots/mass_function/{0}/"
MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
    "mass_function_r{1:.2f}-z{2:.2f}.png"

OVERDENSITY_PLOTS_DIR = "../plots/deltas/{0}/"
OVERDENSITY_PLOTS_FNAME_PTRN = OVERDENSITY_PLOTS_DIR + \
    "overdensity_r{1:.2f}-z{z:.2f}.png"

DESIRED_REDSHIFTS = [0, 1, 2, 6, 10]


def main():
    pth = ROOT + SIM_FOLDER
    print("Reading data set in:", pth)
    # Find halos for data set
    print("Filtering halo files to look for redshifts:", DESIRED_REDSHIFTS)
    _, _, rockstars = helpers.filter_data_files(SIM_NAME, DESIRED_REDSHIFTS)
    print("Found", len(rockstars), "rockstar files that match these redshifts")

    simulation_name = sim_regex.match(pth).group(1)
    sim_size = float(sim_regex.match(pth).group(3))

    for rck in rockstars:
        print("Working on rockstar file:", rck)

        total_mass_function(rck, sim_size)

        for radius in calc_radii(sim_size, min=50):
            z, masses, deltas = halo_work(rck, radius)
            plot(z, radius, masses, deltas, sim_name=simulation_name)


def total_mass_function(rck, sim_size):
    print("Calculating total mass function:")
    ds = yt.load(rck)
    try:
        ad = ds.all_data()
    except TypeError as te:
        print("error reading all_data(), ignoring...")
        print(te)
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

    print("redshift is:", z)

    V = 4/3 * np.pi * (a*R)**3

    sim_size = (ds.domain_width[0]).to(dist_units)
    print("simulation size is:", sim_size)

    # Get the average density over the region
    rg = ds.r[:]
    try:
        rho_bar = rg.quantities.total_mass()[1] / (sim_size*a)**3
    except unyt.exceptions.IterableUnitCoercionError as e:
        print("Error reading regions quantities from database, ignoring...")
        print(e)

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = rand_coords(
        NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

    masses = unyt.unyt_array(
        [], ds.units.Msun / ds.units.h)
    deltas = []

    for c in coords:
        print(f"Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")
        try:
            sp = ds.sphere(c, R)
        except Exception as e:
            print("error creating sphere sample")
            print(e)
            continue

        try:
            m = sp.quantities.total_mass()[1]
        except Exception as e:
            print("error reading sphere total_mass()")
            print(e)
            continue

        rho = m / V
        delta = (rho - rho_bar) / rho_bar
        deltas.append(delta)

        mass = m.to(ds.units.Msun / ds.units.h)

        masses = unyt.uconcatenate((masses, [mass]))

    return z, sorted(masses), sorted(deltas)


def calc_radii(sim_size: float, min=0):
    radii = np.linspace(start=min, stop=sim_size,
                        num=NUM_SPHERE_SIZES)

    return [float(r) for r in radii]


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def plot(z, radius, masses, deltas, sim_name="default"):
    mass_hist, mass_bin_edges = np.histogram(masses, bins=NUM_HIST_BINS)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    mass_hist = mass_hist / V

    title = f"Mass Function for {sim_name} @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(sim_name)
    plot_name = MASS_FN_PLOTS_FNAME_PTRN.format(sim_name, radius, z)

    plot_mass_function(mass_hist, mass_bin_edges, title, save_dir, plot_name)

    title = f"Overdensity for {sim_name} @ z={z:.2f}"
    save_dir = OVERDENSITY_PLOTS_DIR.format(sim_name)
    plot_name = OVERDENSITY_PLOTS_FNAME_PTRN.format(sim_name, radius, z)
    plot_delta(deltas, sim_name=sim_name)


def plot_mass_function(hist, bin_edges, title, save_dir, plot_f_name):
    plt.plot(np.log(bin_edges[:-1]), np.log(hist))
    plt.gca().set_xscale("log")

    plt.title(title)
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d n}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()


def plot_delta(deltas, title, save_dir, plot_f_name):
    plt.hist(deltas, bins=NUM_HIST_BINS)

    plt.title(title)
    plt.xlabel("Overdensity value")
    plt.ylabel("Overdensity $\delta$")

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()


if __name__ == "__main__":
    main()