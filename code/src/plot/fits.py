import logging
import os
from typing import Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import scipy.stats
import unyt
import yt
from src import data, enum
from src.const.constants import (BIN_CENTRE_KEY, FITS_KEY, HIST_FIT_KEY,
                                 POPT_KEY, R2_KEY)
from src.plot import funcs, plotting


class Fits(plotting.Plotter):

    def __init__(self, d: data.Data, type: enum.DataType):
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = [1., 0., 1.]
        self._title = self.gaussian_title
        self._func = funcs.gauss
        self._fit_dir = self.gaussian_fit_dir
        self._fit_fname = self.gaussian_fit_fname
        super().__init__(d, type)

    def gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.gaussian_fit,
                                      sim_name, self._type)

    def gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.gaussian_fit,
                                        self._conf.plotting.pattern.gaussian_fit,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def gaussian_title(self, sim_name, z):
        return f"Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"

    def skewed_gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.skewed_gaussian_fit,
                                      sim_name, self._type)

    def skewed_gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.skewed_gaussian_fit,
                                        self._conf.plotting.pattern.skewed_gaussian_fit,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def skewed_gaussian_title(self, sim_name, z):
        return f"Skewed Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"

    def n_gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.n_gaussian_fit,
                                      sim_name, self._type)

    def n_gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.n_gaussian_fit,
                                        self._conf.plotting.pattern.n_gaussian_fit,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def n_gaussian_title(self, sim_name, z):
        return f"N Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"

    def _gen_fit(self,
                 z: float,
                 radius: float,
                 deltas: unyt.unyt_array,
                 sim_name: str,
                 num_bins: int,
                 fig: plt.Figure = None) -> Tuple[plt.Figure, np.ndarray]:
        logger = logging.getLogger(__name__ + "." + self._gen_fit.__name__)

        if not yt.is_root():
            return

        logger.debug(
            f"Plotting fitted function '{self._func.__name__}' at z={z:.2f}...")

        title = self._title(sim_name, z)
        save_dir = self._fit_dir(sim_name)
        plot_name = self._fit_fname(sim_name, radius, z)

        autosave = fig is None
        if autosave:
            fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.gca()

        bin_centres, hist_fit, r2, popt = self.calc_fit(
            z, deltas, num_bins, sim_name)

        ax.plot(bin_centres, hist_fit, label='Fitted data')

        # Show the R^2 in the legend:
        legend_addendum = f"$R^2 = {r2:.4f}$"

        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=legend_addendum))

        fig.suptitle(title)
        ax.legend(handles=handles)

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

            logger.debug(f"Saved Gaussian overdensity plot to '{plot_name}'")

        return fig, popt

    def calc_fit(self,
                 z: float,
                 deltas: unyt.unyt_array,
                 num_bins: int,
                 sim_name: str) -> Tuple[np.ndarray, np.ndarray, float, list]:
        logger = logging.getLogger(__name__ + "." + self.calc_fit.__name__)

        logger.debug(
            f"Calculating fitting parameters for function '{self._func.__name__}' at z={z:.2f}...")

        key = (sim_name, self._type.value, FITS_KEY, self._func.__name__, z)
        cache_vals = self._cache[key].val

        if cache_vals is None or not self._conf.caches.use_fits_cache:
            logger.debug(f"Recalculating cached fit values...")

            # ================
            # Fit the Function
            # ================
            od_bins = np.linspace(start=-1, stop=2, num=num_bins)

            hist, bin_edges = np.histogram(deltas, bins=od_bins)
            bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

            popt, pcov = scipy.optimize.curve_fit(
                self._func, bin_centres, hist, p0=self._p0)

            logger.debug(f"Curve fit coefficients are: {popt}")

            # Get the fitted curve
            hist_fit = self._func(bin_centres, *popt)

            # =============================================================
            # R^2 QUALITY OF FIT TEST
            # =============================================================
            logger.debug("Calculating R^2 value")

            ss_res = np.sum((hist - hist_fit)**2)
            ss_tot = np.sum((hist - np.mean(hist))**2)

            r2 = 1 - (ss_res / ss_tot)

            logger.debug(f"R^2 is = {r2}")

            # =============================================================
            # CACHE RESULTS
            # =============================================================
            cache_vals = {
                BIN_CENTRE_KEY: bin_centres,
                HIST_FIT_KEY: hist_fit,
                R2_KEY: r2,
                POPT_KEY: popt
            }

            self._cache[key] = cache_vals
        else:
            logger.debug("Using cached fits values...")

        return cache_vals[BIN_CENTRE_KEY], cache_vals[HIST_FIT_KEY], cache_vals[R2_KEY], cache_vals[POPT_KEY]

    def gaussian_fit(self,
                     z: float,
                     radius: float,
                     deltas: unyt.unyt_array,
                     sim_name: str,
                     num_bins: int,
                     fig: plt.Figure = None) -> Tuple[plt.Figure, np.ndarray]:
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = [1., 0., 1.]
        self._title = self.gaussian_title
        self._func = funcs.gauss
        self._fit_dir = self.gaussian_fit_dir
        self._fit_fname = self.gaussian_fit_fname
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)

    def skewed_gaussian_fit(self,
                            z: float,
                            radius: float,
                            deltas: unyt.unyt_array,
                            sim_name: str,
                            num_bins: int,
                            fig: plt.Figure = None) -> Tuple[plt.Figure, np.ndarray]:
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = [1., 0., 1., 0., 0.]
        self._title = self.skewed_gaussian_title
        self._func = funcs.skew
        self._fit_dir = self.skewed_gaussian_fit_dir
        self._fit_fname = self.skewed_gaussian_fit_fname
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)

    def n_gaussian_fit(self,
                       z: float,
                       radius: float,
                       deltas: unyt.unyt_array,
                       sim_name: str,
                       num_bins: int,
                       fig: plt.Figure = None,
                       num_fits: int = 10) -> Tuple[plt.Figure, np.ndarray]:
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = []
        for i in range(num_fits):
            self._p0 += [i, 1, 1]
        self._title = self.n_gaussian_title
        self._func = funcs.n_gaussian
        self._fit_dir = self.n_gaussian_fit_dir
        self._fit_fname = self.n_gaussian_fit_fname
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)
