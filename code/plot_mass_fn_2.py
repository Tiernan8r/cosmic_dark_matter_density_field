import pickle

import matplotlib.pyplot as plt
import numpy as np


def main():

    all_data = load_data()
    plotting(all_data)


def plotting(all_data):

    for sim_name in all_data.keys():

        redshifts_data = all_data[sim_name]

        for z, data in redshifts_data.items():

            for radii, masses in data.items():

                print(f"RADIUS: {radii} @ z={z}")
                print("#MASSES: ", len(masses))
                # print(masses)

                hist, bin_edges = np.histogram(masses, bins=100)

                a = 1 / (1+z)
                V = 4/3 * np.pi * (a*radii)**3

                hist = hist / V
                print("HISTS:")
                print(hist)

                plt.hist(x=masses, bins=100, density=True)
                # plt.plot(np.log(masses), hist)
                # ax = plt.gca()

                plt.title("TEST")
                plt.xlabel("X")
                plt.ylabel("Y")
                plt.savefig(f"../plots/tests/test_{sim_name}-{z:.2f}.png")
                plt.cla()


def load_data():

    with open("../data/mass_fn.pickle", "rb") as f:
        all_data = pickle.load(f)

    return all_data


if __name__ == "__main__":
    main()
