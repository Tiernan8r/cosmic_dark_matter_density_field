import pickle
import re
from typing import Tuple

import numpy as np
import unyt
import yt
import yt.extensions.legacy
from yt.data_objects.selection_objects.region import YTRegion
from yt.data_objects.static_output import Dataset

import helpers
import plot_mass_fn_2

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d{3})n(\d+)_SLEGAC).*$")

NUM_SAMPLES_PER_SPHERE = 10
NUM_SPHERE_SIZES = 10


def main():
    # Iterate over datasets
    all_data = {}

    for pth in helpers.PATHS:
        print("Reading data set in:", pth)
        # Find halos for data set
        _, rockstars, _ = helpers.find_halos(pth)

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

            data = {}

            # radii = np.linspace(start=1e-10, stop=sim_size.value,
            #                     num=NUM_SPHERE_SIZES)
            radii = [50]
            print("sampling with radii of the following sizes:", radii)

            for r in radii:

                coord_min = r
                coord_max = sim_size.value - r

                coords = rand_coords(
                    NUM_SAMPLES_PER_SPHERE, min=coord_min, max=coord_max) * dist_units

                ms = data.get(r, unyt.unyt_array(
                    [], ds.units.Msun / ds.units.h))

                for c in coords:
                    idxs = filter_halos(ds, ad, c, r)

                    masses = ad["halos", "particle_mass"][idxs]

                    ms = unyt.uconcatenate((ms, masses))

                plot_mass_fn_2.plot(z, r, sorted(ms), sim_name=simulation_name)
                # data[r] = sorted(ms)
            # all_data[simulation_name][z] = data

    # with open("../data/mass_fn.pickle", "wb") as f:
    #     pickle.dump(all_data, f)
    # print("GENNING PLOTS:")
    # plot_mass_fn_2.plotting(all_data)

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
