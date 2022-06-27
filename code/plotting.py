import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import yt

from constants import (MASS_FN_PLOTS_DIR, MASS_FN_PLOTS_FNAME_PTRN,
                       NUM_HIST_BINS, NUM_OVERDENSITY_HIST_BINS,
                       OVERDENSITY_PLOTS_DIR, OVERDENSITY_PLOTS_FNAME_PTRN)


def plot(z, radius, masses, deltas, sim_name="default"):
    if not yt.is_root():
        return

    logger = logging.getLogger(__name__ + "." + plot.__name__)

    mass_hist, mass_bin_edges = np.histogram(masses, bins=NUM_HIST_BINS)

    a = 1 / (1+z)
    V = 4/3 * np.pi * (a*radius)**3

    mass_hist = mass_hist / V

    logger.debug(f"Plotting mass function at z={z:.2f}...")

    title = f"Mass Function for {sim_name} @ z={z:.2f}"
    save_dir = MASS_FN_PLOTS_DIR.format(sim_name)
    plot_name = MASS_FN_PLOTS_FNAME_PTRN.format(sim_name, radius, z)

    plot_mass_function(mass_hist, mass_bin_edges, title, save_dir, plot_name)

    logger.debug(f"Plotting overdensities at z={z:.2f}...")

    title = f"Overdensity for {sim_name} @ z={z:.2f}"
    save_dir = OVERDENSITY_PLOTS_DIR.format(sim_name)
    plot_name = OVERDENSITY_PLOTS_FNAME_PTRN.format(sim_name, radius, z)
    plot_delta(deltas, title, save_dir, plot_name)


def plot_mass_function(hist, bin_edges, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    x = np.log(bin_edges[:-1])
    y = np.log(hist)

    plt.plot(x, y)
    plt.gca().set_xscale("log")

    plt.title(title)
    plt.xlabel("$\log{M_{vir}}$")
    plt.ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()


def plot_delta(deltas, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    plt.hist(deltas, bins=NUM_OVERDENSITY_HIST_BINS)

    plt.title(title)
    plt.xlabel("Overdensity value")
    plt.ylabel("Overdensity $\delta$")

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    plt.savefig(plot_f_name)
    plt.cla()

