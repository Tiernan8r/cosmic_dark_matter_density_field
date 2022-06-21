import os
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import yt
from unyt.exceptions import IterableUnitCoercionError

import helpers

# MPI Stuff
NUM_SNAPSHOTS = 102
# Sphere radius
RADIUS = 50

ROOT = "/disk12/legacy/"
SIMULATION = "GVD_C700_l600n2048_SLEGAC"
SIMULATION_PATH = ROOT + SIMULATION + "/"

PLOTS_PATH = "../plots/delta/{0}/"
PLOTS_FILENAME = "delta_vs_a_final_50Mpc.png"


def main():
    z_arr, delta_arr = calc()
    save(z_arr, delta_arr)
    plot(z_arr, delta_arr)


def calc() -> Tuple[np.ndarray, np.ndarray]:
    # Sphere centers from a file
    random_centres = np.loadtxt("examples/random_locs.txt", max_rows=500)
    print("loaded", len(random_centres), "random coordinates from the file")

    snapshots, _, _ = helpers.find_data_files(SIMULATION_PATH)

    storage = {}

    print("Beginning iteration over", len(snapshots), "snapshots")

    for snap_f_name in snapshots:
        print("Working on snapshot:", snap_f_name)

        units = {"length": (1.0, "Mpc/h")}

        # load in the simulation
        ds = yt.load(snap_f_name, unit_base=units)

        z = ds.current_redshift
        print("Redshift is:", z)

        a = 1 / (1+z)

        # define a region containing the full box and get its density
        rg = ds.r[:]

        try:
            rho_bar = rg.quantities.total_mass(
            )[1] / (ds.domain_width[0]*a)**3
        except IterableUnitCoercionError as e:
            print("Error reading regions quantities from database, ignoring...")
            print(e)
            continue

        # overdensities
        delta = []

        # give units to the sphere radius
        radius_units = RADIUS * ds.units.Mpc / ds.units.h

        R = radius_units.to('code_length')

        # create spheres at random locations from the file and get their overdensities
        for i in range(len(random_centres)):
            centres = random_centres[i]

            sp = ds.sphere(centres, R)

            V = 4/3 * np.pi * (a*R)**3

            try:
                rho = sp.quantities.total_mass()[1] / V
            except IterableUnitCoercionError as e:
                print(
                    i, "- Error reading regions quantities from database, defaulting to rho_bar...")
                print(e)
                rho = rho_bar

            delta.append((rho - rho_bar) / rho_bar)

        print("Finished calculating delta for snapshot...")
        print("-----\n")
        # store results from each process
        storage[z] = delta

    return wrangle(storage)


def wrangle(storage: dict) -> Tuple[np.ndarray, np.ndarray]:
    deltas = []
    z = []

    # get the data from storage
    for zs, dels in sorted(storage.items()):
        z.append(zs)
        deltas.append(dels)

    z_arr = np.array(z)
    delta_arr = np.array(deltas)

    return z_arr, delta_arr


def save(z_arr: np.array, delta_arr: np.array):
    print("Saving data to file...")
    
    if not os.path.isdir("../data"):
        os.makedirs("../data")

    # write the data
    with open("../data/z.npy", "wb") as f:
        np.save(f, z_arr)

    with open("../data/delta.npy", "wb") as f:
        np.save(f, delta_arr)


def plot(z_arr: np.ndarray, delta_arr: np.ndarray):
    # Sphere centers from a file
    c = np.loadtxt("examples/random_locs.txt", max_rows=500)

    a_arr = 1 / (1+z_arr)

    try:
        # plot the data
        for i in range(len(c)):
            plt.plot(a_arr, delta_arr.T[i], alpha=0.1)

        plt.title("Overdensity evolution with cosmic scale factor")
        plt.xlabel("Scale factor $a$")
        plt.ylabel("Overdensity $\delta$")

        dir_name = PLOTS_PATH.format(SIMULATION)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        
        plt_f_name = PLOTS_PATH + PLOTS_FILENAME
        plt.savefig(plt_f_name.format(SIMULATION))

    except IndexError:
        print("error making plot, skipping...")
        return

if __name__ == "__main__":
    main()
