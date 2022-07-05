import logging
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import yt

from constants import (MASS_FN_PLOTS_DIR, MASS_FN_PLOTS_FNAME_PTRN,
                       OVERDENSITY_PLOTS_DIR, OVERDENSITY_PLOTS_FNAME_PTRN)


def plot(z, radius, masses, deltas, num_hist_bins, num_overdensity_hist_bins, sim_name="default"):
    if not yt.is_root():
        return

    logger = logging.getLogger(__name__ + "." + plot.__name__)

    mass_hist, mass_bin_edges = np.histogram(masses, bins=num_hist_bins)

    # Filter hist/bins for non-zero masses
    valid_idxs = np.where(mass_hist > 0)
    mass_hist = mass_hist[valid_idxs]
    mass_bin_edges = mass_bin_edges[valid_idxs]

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
    plot_delta(deltas, num_overdensity_hist_bins, title, save_dir, plot_name)


def plot_mass_function(hist, bin_edges, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    logger = logging.getLogger(__name__ + "." + plot_mass_function.__name__)

    x = np.log10(bin_edges)
    y = np.log10(hist)

    fig = plt.figure()
    ax = fig.gca()

    ax.plot(x, y)
    # ax.set_xscale("log")
    # ax.set_yscale("log")

    fig.suptitle(title)
    ax.set_xlabel("$\log{M_{vir}}$")
    ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    fig.savefig(plot_f_name)

    logger.debug(f"Saved mass function figure to '{plot_f_name}'")

    plt.cla()
    plt.clf()


def plot_delta(deltas, num_bins, title, save_dir, plot_f_name):
    if not yt.is_root():
        return

    logger = logging.getLogger(__name__ + "." + plot_delta.__name__)

    fig = plt.figure()
    ax = fig.gca()

    ax.hist(deltas, bins=num_bins)
    ax.set_xlim(left=-1, right=2)

    fig.suptitle(title)
    ax.set_xlabel("Overdensity value")
    ax.set_ylabel("Overdensity $\delta$")

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    fig.savefig(plot_f_name)

    logger.debug(f"Saved overdensity plot to '{plot_f_name}'")

    plt.cla()
    plt.clf()


def ps_mass_function(z, ps: Dict, title, save_dir, plot_name):
    logger = logging.getLogger(plot_mass_function.__name__)
    logger.info(f"Generating figure for redshift {z}")

    x = np.array(list(ps.keys()))
    y = np.array(list(ps.values()))

    fig = plt.figure()
    ax = fig.gca()

    ax.plot(np.log10(x), np.log10(y))
    fig.suptitle(title)

    # ax = plt.gca()
    # ax.set_xscale("log")
    # ax.set_yscale("log")

    ax.set_xlabel("$\log{M_{vir}}$")
    ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

    # Ensure the folders exist before attempting to save an image to it...
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    fig.savefig(plot_name)

    logger.debug(f"Saved mass function figure to '{plot_name}'")
