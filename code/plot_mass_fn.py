import pickle

import matplotlib.pyplot as plt
import numpy as np
import yt


def main():

    all_data = load_data()

    for sim_name in all_data.keys():

        redshifts_data = all_data[sim_name]

        for z, data in redshifts_data.items():

            pairings = []

            for radii, tuples in data.items():
                masses = tuples[0]
                number_densities = tuples[1]

                for i in range(len(masses)):
                    pairings.append((masses[i], number_densities[i]))

            sorted_pairs = sorted(pairings)
            sorted_masses = [s[0] for s in sorted_pairs]
            sorted_number_densities = [s[1] for s in sorted_pairs]

            # print("SORTED MASS")
            # print(sorted_masses)
            # print("SORTED NUMBER DENSITIES")
            # print(sorted_number_densities)

            plot(sorted_masses, sorted_number_densities, sim_name, z)

def plot(M, n, simulation_name, redshift):

    # if redshift == 0:
    #     print("NUMBER DENSITIES")
    #     print(n)
    #     print("-----------------")
    #     print("MASSES")
    #     print(M)

    plt.plot(M, n)
    plt.title(f"Mass Function @ $z={redshift:2f}$ for simulation {simulation_name}")
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d n}{d \log{M_{vir}}}$")

    plt.savefig(f"../plots/test_mass_fn-{simulation_name}_{redshift:2f}.png")
    plt.cla()

def load_data():

    with open("../data/mass_fn.pickle", "rb") as f:
        all_data = pickle.load(f)

    return all_data


if __name__ == "__main__":
    main()

# # Sphere centers from a file
# c = np.loadtxt("examples/random_locs.txt", max_rows=500)

# z_arr = np.load("/home/tstapleton/dissertation/data/z.npy")
# delta_arr = np.load("/home/tstapleton/dissertation/data/delta.npy")

# a_arr = 1 / (1+z_arr)

# # plot the data
# for i in range(len(c)):
#     plt.plot(a_arr, delta_arr.T[i], alpha=0.1)

# plt.title("Overdensity evolution with cosmic scale factor")
# plt.xlabel("Scale factor $a$")
# plt.ylabel("Overdensity $\delta$")
# plt.savefig("delta_vs_a_final_50Mpc.png")
