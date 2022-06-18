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

NUM_SAMPLES_PER_SPHERE = 10
NUM_SPHERE_SIZES = 10


def main():
    pth = ROOT + SIM_FOLDER
    print("Reading data set in:", pth)
    # Find halos for data set
    _, rockstars, _ = helpers.find_halos(pth)

    simulation_name = sim_regex.match(pth).group(1)

    for rck in rockstars:
        print("working on rockstar file:", rck)

        ds = yt.load(rck)

        try:
            ad = ds.all_data()
        except TypeError as te:
            print("error reading all_data(), ignoring")
            print(te)
            continue

        dist_units = ds.units.Mpc / ds.units.h

        z = ds.current_redshift
        a = 1 / (1 + z)

        print("redshift is:", z)

        sim_size = (ds.domain_width[0]).to(dist_units)
        print("simulation size is:", sim_size)

        # data = {}

        radius = 50
        print("sampling with radius:", radius)

        coord_min = radius
        coord_max = sim_size.value - radius

        coords = rand_coords(
            NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

        default_masses = unyt.unyt_array(
            [], ds.units.Msun / ds.units.h)
        # ms = data.get(radius, default_masses)
        ms = default_masses

        for c in coords:
            idxs = filter_halos(ds, ad, c, radius)

            masses = ad["halos", "particle_mass"][idxs]

            ms = unyt.uconcatenate((ms, masses))

        plot(z, radius, sorted(ms), sim_name=simulation_name)


def plot(z, radius, masses, sim_name=""):

    print(f"RADIUS: {radius} @ z={z}")
    print("#MASSES: ", len(masses))
    # print(masses)

    hist, bin_edges = np.histogram(masses, bins=100)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    hist = hist / V
    # print("HISTS:")
    # print(hist)

    # plt.hist(x=masses, bins=100, density=True)
    plt.plot(np.log(bin_edges[:-1]), hist)
    plt.gca().set_xscale("log")
    # ax = plt.gca()

    plt.title(f"Mass Function for {sim_name} @ z={z:.2f}")
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d n}{d \log{M_{vir}}}$")
    plt.savefig(
        f"../plots/tests/test_simple_{sim_name}-z{z:.2f}-r{radius}.png")
    plt.cla()


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


if __name__ == "__main__":
    main()
