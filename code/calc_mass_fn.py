import re
from typing import Tuple

import numpy as np
import yt
import yt.extensions.legacy
from yt.data_objects.static_output import Dataset

import helpers

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d{3})n(\d+)_SLEGAC).*$")

NUM_COORDS_PER_ITERATION = 10
NUM_SPHERE_SAMPLES = 10


def main():
    # Iterate over datasets
    for pth in helpers.TEST_PATHS:
        # Find halos for data set
        _, rockstars = helpers.find_halos(pth)

        all_data = {}

        for rck in rockstars:
            ds = yt.load(rck)

            z = ds.current_redshift
            a = 1 / (1 + z)

            match = sim_regex.match(rck)
            simulation_name = match.group(1)
            sim_size = int(match.group(3))

            all_data[simulation_name] = {}
            storage = {}

            for r in np.arange(0, sim_size, NUM_SPHERE_SAMPLES):
                coords = rand_coords(NUM_COORDS_PER_ITERATION, max=sim_size)

                masses = []
                ns = []

                for c in coords:
                    idxs = filter_halos(ds, c, r)

                    N = len(idxs)
                    ad = ds.all_data()
                    masses = ad["halos", "particle_mass"][idxs]

                    R = ds.units.Mpc / ds.units.h

                    M = np.sum(masses)
                    n = N / (4/3 * np.pi * (a * R)**3)

                    masses.append(M)
                    ns.append(n)

                storage[r] = (masses, ns)
            all_data[simulation_name][z] = storage



def rand_coords(amount: int, min: int = 0, max: int = 100, seed="legacy"):
    np.random.seed(seed)
    coords = np.random.rand(amount, 3)

    return (max - min) * coords + min


def filter_halos(ds: Dataset, centre: Tuple(float, float, float), radius: float):
    ad = ds.all_data()
    x = ad["halos", "particle_position_x"]
    y = ad["halos", "particle_position_y"]
    z = ad["halos", "particle_position_z"]

    distance_units = ds.units.Mpc / ds.units.h

    c = centre * distance_units
    r = radius * distance_units

    dx = x - c[0]
    dy = y - c[1]
    dz = z - c[2]

    l = np.sqrt(dx**2 + dz**2 + dy**2).to(distance_units)

    idxs = np.where(l <= r)

    return idxs


if __name__ == "__main__":
    main()
