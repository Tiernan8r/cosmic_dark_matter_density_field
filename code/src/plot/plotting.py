import logging
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import unyt
import yt
from src import data
from src import enum


class Plotter:

    def __init__(self, d: data.Data, type: enum.DataType):
        self._conf = d.config
        self._type = type.value
        self._cache = d.cache

    def new_figure(self):
        plt.cla()
        plt.clf()

        return plt.figure()

    def _compile_plot_dir(self, subdir, *args):
        dirname = os.path.join(self._conf.plotting.dirs.root, subdir)

        return dirname.format(*args)

    def _compile_plot_fname(self, subdir, fname, *args):
        plot_fname = os.path.join(self._conf.plotting.dirs.root, subdir, fname)

        return plot_fname.format(*args)

    def mass_fn_dir(self, sim_name: str):
        return self._compile_plot_dir(self._conf.plotting.dirs.mass_function,
                                      sim_name, self._type)

    def mass_fn_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.mass_function,
                                        self._conf.plotting.pattern.mass_function,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def overdensity_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.overdensity,
                                      sim_name, self._type)

    def overdensity_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.overdensity,
                                        self._conf.plotting.pattern.overdensity,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def total_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.total, sim_name, self._type)

    def total_fname(self, sim_name, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.total,
                                        self._conf.plotting.pattern.total,
                                        sim_name, self._type, z)

    def press_schechter_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.press_schechter,
                                      sim_name, self._type)

    def press_schechter_fname(self, sim_name, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.press_schechter,  # noqa: E501
                                        self._conf.plotting.pattern.press_schechter,  # noqa: E501
                                        sim_name, self._type, z)

    def compared_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.compared,
                                      sim_name, self._type)

    def compared_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.compared,
                                        self._conf.plotting.pattern.compared,
                                        sim_name, self._type, radius, z)

    def std_dev_dir(self, sim_name, as_func="radius"):
        return self._compile_plot_dir(self._conf.plotting.dirs.std_dev,
                                      sim_name, self._type, as_func)

    def std_dev_fname(self, sim_name, val, as_func="radius", prefix="z"):
        return self._compile_plot_fname(self._conf.plotting.dirs.std_dev,
                                        self._conf.plotting.pattern.std_dev,
                                        sim_name, self._type, as_func, prefix, val)

    def overdensities(self,
                      z: float,
                      radius: float,
                      deltas: unyt.unyt_array,
                      sim_name: str,
                      num_bins: int,
                      fig: plt.Figure = None):
        if not yt.is_root():
            return

        autosave = fig is None
        if autosave:
            fig: plt.Figure = self.new_figure()

        logger = logging.getLogger(
            __name__ + "." + self.overdensities.__name__)
        logger.debug(f"Plotting overdensities at z={z:.2f}...")

        title = f"Overdensity for {sim_name} @ z={z:.2f}"
        save_dir = self.overdensity_dir(sim_name)
        plot_name = self.overdensity_fname(sim_name, radius, z)

        ax: plt.Axes = fig.gca()

        od_bins = np.linspace(start=-1, stop=2, num=num_bins)
        _, _, analytic = ax.hist(deltas, bins=od_bins,
                                 label="Analytic Overdensities")
        ax.set_xlim(left=-1, right=2)

        fig.suptitle(title)
        ax.set_xlabel("Overdensity $\delta$")
        ax.set_ylabel("Frequency")  # noqa: W605

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

            logger.debug(f"Saved overdensity plot to '{plot_name}'")

        return fig

    def mass_function(self,
                      z: float,
                      radius: float,
                      mass_hist: np.ndarray,
                      bin_edges: np.ndarray,
                      sim_name: str,
                      min_mass=10**10):
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)
        logger.debug(f"Plotting mass function at z={z:.2f}...")

        title = f"Mass Function for {sim_name}; z={z:.2f}"
        save_dir = self.mass_fn_dir(sim_name)
        plot_name = self.mass_fn_fname(sim_name, radius, z)

        self._mass_function(bin_edges, mass_hist, title,
                            save_dir, plot_name, x_min=min_mass)
        logger.debug(f"Saved mass function figure to '{plot_name}'")

    def total_mass_function(self,
                            z: float,
                            mass_hist: np.ndarray,
                            mass_bins: np.ndarray,
                            sim_name: str,
                            min_mass: float):
        # Set the parameters used for the plotting & plot the mass function
        title = f"Total Mass Function for z={z:.2f}"
        save_dir = self.total_dir(sim_name)
        plot_name = self.total_fname(sim_name, z)

        self._mass_function(mass_bins, mass_hist, title,
                            save_dir, plot_name, x_min=min_mass)

    def press_schechter(self,
                        z: float,
                        ps_hist: np.ndarray,
                        bin_edges: np.ndarray,
                        sim_name: str,
                        min_mass=10**10):
        title = f"Press Schecter Mass Function at z={z:.2f}"
        save_dir = self.press_schechter_dir(sim_name)
        plot_name = self.press_schechter_fname(sim_name, z)

        self._mass_function(bin_edges, ps_hist, title,
                            save_dir, plot_name, x_min=min_mass)

    def _mass_function(self, x, y, title, save_dir, plot_name, fig=None, x_min=10**10):
        if len(x) == 0 or len(y) == 0:
            logger = logging.getLogger(
                __name__ + "." + self._mass_function.__name__)
            logger.warning("Attempting to plot empty data!")
            return

        autosave = fig is None
        if autosave:
            fig = self.new_figure()
        ax = fig.gca()

        ax.plot(x, y)
        ax.set_xscale("log")
        ax.set_yscale("log")

        x_max = np.max(x)
        if isinstance(x_min, unyt.unyt_array):
            x_min = x_min.value
        ax.set_xlim(x_min, x_max)

        fig.suptitle(title)
        ax.set_xlabel("$\log{M_{vir}}$")  # noqa: W605
        ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")  # noqa: W605, E501

        # Ensure the folders exist before attempting to save an image to it...
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

        return fig

    def press_schechter_comparison(self,
                                   z: float,
                                   radius: float,
                                   hist: np.ndarray,
                                   bins: np.ndarray,
                                   ps_hist: np.ndarray,
                                   ps_bins: np.ndarray,
                                   sim_name: str):
        fig = self.new_figure()

        title = f"Compared Press Schecter Mass Function at z={z:.2f}; r={radius:.0f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_fname(sim_name, radius, z)

        self._mass_function(bins, hist, title, save_dir, plot_name, fig=fig)
        self._mass_function(ps_bins, ps_hist, title,
                            save_dir, plot_name, fig=fig)

        fig.savefig(plot_name)

        logger = logging.getLogger(
            __name__ + "." + self.press_schechter_comparison.__name__)
        logger.debug(
            f"Saved press-schechter comparison mass function figure to '{plot_name}'")

    def _std_dev(self,
                 x: np.ndarray,
                 y: np.ndarray,
                 title: str,
                 save_dir: str,
                 plot_fname: str,
                 xlabel: str,
                 ylabel: str,
                 logscale=False):
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)

        fig = self.new_figure()
        ax = fig.gca()

        ax.plot(x, y)

        fig.suptitle(title)
        ax.set_xlabel(xlabel)  # noqa: W605
        ax.set_ylabel(ylabel)  # noqa: W605, E501

        if logscale:
            ax.set_xscale("log")
            ax.set_yscale("log")

        # Ensure the folders exist before attempting to save an image to it...
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        fig.savefig(plot_fname)

        plt.cla()
        plt.clf()

        logger.debug(f"Saved mass function figure to '{plot_fname}'")

    def std_dev_func_M(self,
                       z: float,
                       Ms: np.ndarray,
                       sigmas: np.ndarray,
                       sim_name: str,
                       logscale=True):
        title = f"Standard Deviation as a function of sphere mass for {sim_name}; z={z:.2f}"
        save_dir = self.std_dev_dir(sim_name)
        plot_name = self.std_dev_fname(sim_name, z)

        self._std_dev(Ms, sigmas, title, save_dir,
                      plot_name, xlabel="M $(M_\odot / h)$", ylabel="$\sigma^2$", logscale=logscale)

    def std_dev_func_z(self,
                       R: float,
                       redshifts: np.ndarray,
                       sigmas: np.ndarray,
                       sim_name: str):
        title = f"Standard Deviation as a function of redshift for {sim_name}; R={R:.2f} Mpc/h"
        save_dir = self.std_dev_dir(sim_name, as_func="redshift")
        plot_name = self.std_dev_fname(
            sim_name, R, as_func="redshift", prefix="r")

        self._std_dev(redshifts, sigmas, title, save_dir,
                      plot_name, xlabel="z", ylabel="$\sigma$")
