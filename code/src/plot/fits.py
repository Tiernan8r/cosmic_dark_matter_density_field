import os
import logging

import matplotlib.pyplot as plt
import numpy as np
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

        od_bins = np.linspace(start=-1, stop=2, num=num_bins)
        _, _, analytic = ax.hist(deltas, bins=od_bins, density=True)
        ax.set_xlim(left=-1, right=2)

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
        hist, _ = np.histogram(deltas, bins=x, density=True)

        # Multiply the peak of the Gaussian, to match the peak value of the histogram
        hist_total = np.sum(hist)
        gauss_total = np.sum(gauss)

        # scale = hist_max / gauss_max
        scale = hist_total / gauss_total
        gauss *= scale

        # Plot the gaussian with the overdensity
        gaussian, = ax.plot(x, gauss, label="Gaussian Fit")

        fig.suptitle(title)
        ax.legend()

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)

            logger.debug(f"Saved overdensity plot to '{plot_name}'")

        # Add legend to plot
        # ax.legend([analytic, gaussian], ["Analytic Overdensities",
        #                                  "Gaussian Fit"])

        return fig
