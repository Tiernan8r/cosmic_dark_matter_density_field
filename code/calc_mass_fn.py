import pickle
import re
from typing import Tuple

import numpy as np
import yt
import yt.extensions.legacy
from unyt import unyt_array
from yt.data_objects.selection_objects.region import YTRegion
from yt.data_objects.static_output import Dataset

import helpers

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d{3})n(\d+)_SLEGAC).*$")

NUM_COORDS_PER_ITERATION = 100
NUM_SPHERE_SAMPLES = 100


def main():
    # Iterate over datasets
    all_data = {}
    for pth in helpers.TEST_PATHS:
        print("Reading data set in:", pth)
        # Find halos for data set
        _, rockstars = helpers.find_halos(pth)

        simulation_name = sim_regex.match(pth).group(1)
        all_data[simulation_name] = {}

        for rck in rockstars:
            print("working on rockstar file:", rck)

            ds: Dataset = yt.load(rck)

            try:
                ad: YTRegion = ds.all_data()
            except TypeError as te:
                print("error reading all_data(), ignoring")
                print(te)
                continue

            z = ds.current_redshift
            a = 1 / (1 + z)

            sim_size = ds.domain_width[0]

            storage = {}

            for r in np.arange(0, sim_size, NUM_SPHERE_SAMPLES):
                coords = rand_coords(NUM_COORDS_PER_ITERATION, max=sim_size)

                ms = []
                ns = []

                for c in coords:
                    idxs = filter_halos(ds, ad, c, r)

                    N = len(idxs)
                    ad = ds.all_data()
                    masses = ad["halos", "particle_mass"][idxs]

                    R = ds.units.Mpc / ds.units.h

                    M = np.sum(masses)
                    n = N / (4/3 * np.pi * (a * R)**3)

                    ms.append(M)
                    ns.append(n)

                storage[r] = (ms, ns)
            all_data[simulation_name][z] = storage

    with open("../data/mass_fn.pickle", "wb") as f:
        pickle.dump(all_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    # print(all_data)    

def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def filter_halos(ds: Dataset, ad: YTRegion, centre: Tuple[float, float, float], radius: float):
    distance_units = ds.units.Mpc / ds.units.h
    

    x = ad["halos", "particle_position_x"].to(distance_units)
    y = ad["halos", "particle_position_y"].to(distance_units)
    z = ad["halos", "particle_position_z"].to(distance_units)

    c = unyt_array(centres, distance_units)
    r = unyt_array(radius, distance_units)

    dx = x - c[0]
    dy = y - c[1]
    dz = z - c[2]

    l = np.sqrt(dx**2 + dz**2 + dy**2).to(distance_units)

    idxs = np.where(l <= r)

    return idxs


if __name__ == "__main__":
    main()
