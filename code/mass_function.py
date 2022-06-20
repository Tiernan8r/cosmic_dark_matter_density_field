import os
import re
from typing import Tuple

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
            z, masses = halo_work(rck, radius, simulation_name)
            plot(z, radius, masses, sim_name=simulation_name)


def halo_work(rck: str, radius: float, simulation_name: str):
    print("working on rockstar file:", rck)

    ds = yt.load(rck)

    try:
        ad = ds.all_data()
    except TypeError as te:
        print("error reading all_data(), ignoring")
        print(te)
        return

    dist_units = ds.units.Mpc / ds.units.h

    z = ds.current_redshift

    print("redshift is:", z)

    sim_size = (ds.domain_width[0]).to(dist_units)
    print("simulation size is:", sim_size)

    coord_min = radius
    coord_max = sim_size.value - radius

    coords = rand_coords(
        NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

    ms = unyt.unyt_array(
        [], ds.units.Msun / ds.units.h)

    for c in coords:
        idxs = filter_halos(ds, ad, c, radius)

        masses = ad["halos", "particle_mass"][idxs]

        ms = unyt.uconcatenate((ms, masses))

    return z, sorted(ms)


def calc_radii(sim_size: float, min=0):
    radii = np.linspace(start=min, stop=sim_size,
                        num=NUM_SPHERE_SIZES)

    return [float(r) for r in radii]


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def filter_halos(ds, ad, centre: Tuple[float, float, float], radius: float):
    dist_units = ds.units.Mpc / ds.units.h

    x = ad["halos", "particle_position_x"].to(dist_units)
    y = ad["halos", "particle_position_y"].to(dist_units)
    z = ad["halos", "particle_position_z"].to(dist_units)

    c = unyt.unyt_array(centre, dist_units)
    r = unyt.unyt_array(radius, dist_units)

    dx = x - c[0]
    dy = y - c[1]
    dz = z - c[2]

    l = np.sqrt(dx**2 + dz**2 + dy**2).to(dist_units)

    idxs = np.where(l <= r)

    return idxs


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
