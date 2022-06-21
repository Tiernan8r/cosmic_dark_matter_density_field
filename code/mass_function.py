import os
import re

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
import yt.extensions.legacy

import helpers

ROOT = "/disk12/legacy/"
SIM_FOLDER = "GVD_C700_l1600n2048_SLEGAC/"

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")

NUM_SAMPLES_PER_SPHERE = 1000
NUM_SPHERE_SIZES = 10
NUM_HIST_BINS = 1000

PLOTS_FOLDER = "../plots/mass_function/{0}/"
PLOTS_FILENAME_PATTERN = PLOTS_FOLDER + "mass_function_r{1:.2f}-z{2:.2f}.png"


def main():
    pth = ROOT + SIM_FOLDER
    print("Reading data set in:", pth)
    # Find halos for data set
    _, rockstars, _ = helpers.find_halos(pth)

    simulation_name = sim_regex.match(pth).group(1)
    sim_size = float(sim_regex.match(pth).group(3))

    for rck in rockstars:
        for radius in calc_radii(sim_size, min=50):
            z, masses = halo_work(rck, radius)
            plot(z, radius, masses, sim_name=simulation_name)


def halo_work(rck: str, radius: float):
    print("working on rockstar file:", rck)

    ds = yt.load(rck)

    dist_units = ds.units.Mpc / ds.units.h

    z = ds.current_redshift

    print("redshift is:", z)

    sim_size = (ds.domain_width[0]).to(dist_units)
    print("simulation size is:", sim_size)

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = rand_coords(
        NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

    masses = unyt.unyt_array(
        [], ds.units.Msun / ds.units.h)

    for c in coords:
        sp = ds.sphere(c, radius)
        m = sp.quantities.total_mass()[1]
        mass = m.to(ds.units.Msun / ds.units.h)

        masses = unyt.uconcatenate((masses, mass))

    return z, sorted(masses)


def calc_radii(sim_size: float, min=0):
    radii = np.linspace(start=min, stop=sim_size,
                        num=NUM_SPHERE_SIZES)

    return [float(r) for r in radii]


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def plot(z, radius, masses, sim_name="default"):

    print(f"RADIUS: {radius} @ z={z}")

    hist, bin_edges = np.histogram(masses, bins=NUM_HIST_BINS)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    hist = hist / V

    plt.plot(np.log(bin_edges[:-1]), hist)
    plt.gca().set_xscale("log")

    plt.title(f"Mass Function for {sim_name} @ z={z:.2f}")
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d n}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    dir_name = PLOTS_FOLDER.format(sim_name)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)

    plt.savefig(PLOTS_FILENAME_PATTERN.format(sim_name, radius, z))
    plt.cla()


if __name__ == "__main__":
    main()
