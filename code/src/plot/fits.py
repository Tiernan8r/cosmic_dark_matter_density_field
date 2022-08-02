import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import unyt
import yt
from src import data, enum
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
                 fig: plt.Figure = None):
        logger = logging.getLogger(__name__ + "." + self.gaussian_fit.__name__)

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

        # =============
        # Fit Gaussian:
        # =============

        od_bins = np.linspace(start=-1, stop=2, num=num_bins)

        hist, bin_edges = np.histogram(deltas, bins=od_bins)
        bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

        coeff, var_matrix = scipy.optimize.curve_fit(
            self._func, bin_centres, hist, p0=self._p0)

        logger.debug(f"Curve fit coefficients are: {coeff}")

        # Get the fitted curve
        hist_fit = self._func(bin_centres, *coeff)

        ax.plot(bin_centres, hist_fit, label='Fitted data')

        # Finally, lets get the fitting parameters, i.e. the mean and standard deviation:
        logger.info(f"Fitted mean = {coeff[1]}")
        logger.info(f"Fitted standard deviation = {coeff[2]}")

        fig.suptitle(title)
        ax.legend()

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

            logger.debug(f"Saved Gaussian overdensity plot to '{plot_name}'")

        # Add legend to plot
        # ax.legend([analytic, gaussian], ["Analytic Overdensities",
        #                                  "Gaussian Fit"])

        return fig

    def gaussian_fit(self,
                     z: float,
                     radius: float,
                     deltas: unyt.unyt_array,
                     sim_name: str,
                     num_bins: int,
                     fig: plt.Figure = None):
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
                            fig: plt.Figure = None):
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
                       num_fits: int = 12):
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = []
        for i in range(num_fits):
            self._p0 += [i, 1, 1]
        self._title = self.n_gaussian_title
        self._func = funcs.n_gaussian
        self._fit_dir = self.n_gaussian_fit_dir
        self._fit_fname = self.n_gaussian_fit_fname
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)
