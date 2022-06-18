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

NUM_SAMPLES_PER_SPHERE = 10
NUM_SPHERE_SIZES = 10


def main():
    # Iterate over datasets
    all_data = {}
    coords_radii_map = {}

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

            dist_units = ds.units.Mpc / ds.units.h

            z = ds.current_redshift
            a = 1 / (1 + z)

            print("redshift is:", z)

            sim_size = (ds.domain_width[0]).to(dist_units)
            print("simulation size is:", sim_size)

            storage = {}

            radii = np.linspace(start=0, stop=sim_size.value,
                                num=NUM_SPHERE_SIZES)
            print("sampling with radii of the following sizes:", radii)

            for r in radii:

                # Reuse random coordinates between simulations
                if r not in coords_radii_map:
                    coord_min = r
                    coord_max = sim_size.value - r

                    coords = rand_coords(
                        NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

                    coords_radii_map[r] = coords
                else:
                    coords = coords_radii_map[r]

                ms = []
                ns = []

                for c in coords:
                    idxs = filter_halos(ds, ad, c, r)

                    N = len(idxs[0])
                    print(
                        f"Found {N} halos within {r}Mpc of ({c[0]}, {c[1]}, {c[2]})")

                    masses = ad["halos", "particle_mass"][idxs]

                    M = np.sum(masses)

                    R = r * dist_units
                    V = 4/3 * np.pi * (a * R)**3
                    print("Volume of sample:", V)

                    # n = N / V
                    n=N

                    ms.append(M)
                    ns.append(n)

                storage[r] = (ms, ns)
            all_data[simulation_name][z] = storage

    with open("../data/mass_fn.pickle", "wb") as f:
        pickle.dump(all_data, f)

    # print(all_data)


def rand_coords(amount: int, min: int = 0, max: int = 100, seed=0):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def filter_halos(ds: Dataset, ad: YTRegion, centre: Tuple[float, float, float], radius: float):
    dist_units = ds.units.Mpc / ds.units.h

    x = ad["halos", "particle_position_x"].to(dist_units)
    y = ad["halos", "particle_position_y"].to(dist_units)
    z = ad["halos", "particle_position_z"].to(dist_units)

    c = unyt_array(centre, dist_units)
    r = unyt_array(radius, dist_units)

    dx = x - c[0]
    dy = y - c[1]
    dz = z - c[2]

    l = np.sqrt(dx**2 + dz**2 + dy**2).to(dist_units)

    idxs = np.where(l <= r)

    return idxs


if __name__ == "__main__":
    main()
