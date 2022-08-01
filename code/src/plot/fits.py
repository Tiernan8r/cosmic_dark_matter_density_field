import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize
import unyt
import yt
from src.plot import plotting


class Fits(plotting.Plotter):

    def gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self._conf.plotting.dirs.gaussian_fit,
                                      sim_name, self._type)

    def gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self._conf.plotting.dirs.gaussian_fit,
                                        self._conf.plotting.pattern.gaussian_fit,  # noqa: E501
                                        sim_name, self._type, radius, z)

    def gaussian_fit(self,
                     z: float,
                     radius: float,
                     deltas: unyt.unyt_array,
                     sim_name: str,
                     num_bins: int,
                     fig: plt.Figure = None):
        logger = logging.getLogger(__name__ + "." + self.gaussian_fit.__name__)

        if not yt.is_root():
            return

        logger.debug(f"Plotting gaussian fit at z={z:.2f}...")

        title = f"Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"
        save_dir = self.gaussian_fit_dir(sim_name)
        plot_name = self.gaussian_fit_fname(sim_name, radius, z)

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

        # Define model function to be used to fit to the data above:
        def gauss(x, *p):
            A, mu, sigma = p
            return A*np.exp(-(x-mu)**2/(2.*sigma**2))

        # p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
        p0 = [1., 0., 1.]

        coeff, var_matrix = scipy.optimize.curve_fit(
            gauss, bin_centres, hist, p0=p0)

        # Get the fitted curve
        hist_fit = gauss(bin_centres, *coeff)

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
