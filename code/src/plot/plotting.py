import logging
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
from src import data


class Plotter:

    def __init__(self, d: data.Data):
        self._conf = d.config

    def _compile_plot_dir(self, subdir, *args):
        dirname = os.path.join(self._conf.plotting.dirs.root, subdir)

        return dirname.format(*args)

    def _compile_plot_fname(self, subdir, fname, *args):
        plot_fname = os.path.join(self._conf.plotting.dirs.root, subdir, fname)

        return plot_fname.format(*args)

    def mass_fn_dir(self, sim_name: str):
        return self._compile_plot_dir(self._conf.plotting.dirs.mass_function,
                                      sim_name)

    def mass_fn_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.mass_function,
                                        self._conf.plotting.pattern.mass_function,  # noqa: E501
                                        sim_name, radius, z)

    def overdensity_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.overdensity,
                                      sim_name)

    def overdensity_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.overdensity,
                                        self._conf.plotting.pattern.overdensity,  # noqa: E501
                                        sim_name, radius, z)

    def total_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.total, sim_name)

    def total_fname(self, sim_name, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.total,
                                        self._conf.plotting.pattern.total,
                                        sim_name, z)

    def press_schechter_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.press_schechter,
                                      sim_name)

    def press_schechter_fname(self, sim_name, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.press_schechter,  # noqa: E501
                                        self._conf.plotting.pattern.press_schechter,  # noqa: E501
                                        sim_name, z)

    def compared_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.compared,
                                      sim_name)

    def compared_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.compared,
                                        self._conf.plotting.pattern.compared,
                                        sim_name, radius, z)

    def overdensities(self,
                      z: float,
                      radius: float,
                      deltas: unyt.unyt_array,
                      sim_name: str,
                      num_bins: int):
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.overdensities.__name__)
        logger.debug(f"Plotting overdensities at z={z:.2f}...")

        title = f"Overdensity for {sim_name} @ z={z:.2f}"
        save_dir = self.overdensity_dir(sim_name)
        plot_name = self.overdensity_fname(sim_name, radius, z)

        fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.gca()

        od_bins = np.linspace(start=-1, stop=2, num=num_bins)
        _, _, analytic = ax.hist(deltas, bins=od_bins)
        ax.set_xlim(left=-1, right=2)

        fig.suptitle(title)
        ax.set_xlabel("Overdensity value")
        ax.set_ylabel("Overdensity $\delta$")  # noqa: W605

        # =============
        # Fit Gaussian:
        # =============

        # A standard gaussian overdensity field is in range [-1, 1]
        gaussian_range_deltas = [d for d in deltas if d <= 1 and d >= -1]
        x = [x for x in od_bins if x <= 1 and x >= -1]

        std_dev = np.std(gaussian_range_deltas)
        mean = np.mean(gaussian_range_deltas)

        # Calculate the gaussian distribution
        pre_factor = 1 / (std_dev * np.sqrt(2 * np.pi))
        gauss = pre_factor * np.exp(-0.5 * ((x - mean) / std_dev)**2)

        # Scale the Gaussian to match the analytical scale
        hist, _ = np.histogram(deltas, bins=x)

        # Multiply the peak of the Gaussian, to match the peak value of the histogram
        hist_total = np.sum(hist)
        gauss_total = np.sum(gauss)

        # scale = hist_max / gauss_max
        scale = hist_total / gauss_total
        gauss *= scale

        # Plot the gaussian with the overdensity
        gaussian, = ax.plot(x, gauss)

        # Add legend to plot
        ax.legend([analytic, gaussian], ["Analytic Overdensities",
                   "Gaussian Fit"])

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        fig.savefig(plot_name)

        logger.debug(f"Saved overdensity plot to '{plot_name}'")

        plt.close(fig)

    def mass_function(self,
                      z: float,
                      radius: float,
                      mass_hist: np.ndarray,
                      bin_edges: np.ndarray,
                      sim_name: str):
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)
        logger.debug(f"Plotting mass function at z={z:.2f}...")

        title = f"Mass Function for {sim_name}; z={z:.2f}"
        save_dir = self.mass_fn_dir(sim_name)
        plot_name = self.mass_fn_fname(sim_name, radius, z)

        self._mass_function(bin_edges, mass_hist, title, save_dir, plot_name)
        logger.debug(f"Saved mass function figure to '{plot_name}'")

    def total_mass_function(self,
                            z: float,
                            mass_hist: np.ndarray,
                            mass_bins: np.ndarray,
                            sim_name: str):
        # Set the parameters used for the plotting & plot the mass function
        title = f"Total Mass Function for z={z:.2f}"
        save_dir = self.total_dir(sim_name)
        plot_name = self.total_fname(sim_name, z)

        self._mass_function(mass_bins, mass_hist, title, save_dir, plot_name)

    def press_schechter(self, z: float, press_schechter, sim_name: str):
        title = f"Press Schecter Mass Function at z={z:.2f}"
        save_dir = self.press_schechter_dir(sim_name)
        plot_name = self.press_schechter_fname(sim_name, z)

        x = press_schechter.keys()
        y = press_schechter.values()

        self._mass_function(x, y, title, save_dir, plot_name)

    def _mass_function(self, x, y, title, save_dir, plot_name, fig=None):
        autosave = fig is None
        if autosave:
            fig = plt.figure()
        ax = fig.gca()

        ax.plot(x, y)
        ax.set_xscale("log")
        ax.set_yscale("log")

        fig.suptitle(title)
        ax.set_xlabel("$\log{M_{vir}}$")  # noqa: W605
        ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")  # noqa: W605, E501

        # Ensure the folders exist before attempting to save an image to it...
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

            plt.cla()
            plt.clf()

    def press_schechter_comparison(self,
                                   z: float,
                                   radius: float,
                                   hist: np.ndarray,
                                   bins: np.ndarray,
                                   ps: Dict,
                                   sim_name: str):
        fig = plt.figure()

        title = f"Compared Press Schecter Mass Function at z={z:.2f}; r={radius:.0f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_fname(sim_name, radius, z)

        self._mass_function(hist, bins, title, save_dir, plot_name, fig=fig)
        x = ps.keys()
        y = ps.values()
        self._mass_function(x, y, title, save_dir, plot_name, fig=fig)

        fig.savefig(plot_name)
