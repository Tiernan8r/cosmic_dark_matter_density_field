import logging
import os
from typing import Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import src.plotting.interface as I
import unyt
import yt
from src.fitting import fits, funcs
from src.util import data, enum


class Fits(I.IPlot):

    def __init__(self, d: data.Data, type: enum.DataType = ..., sim_name: str = ...):
        super().__init__(d, type, sim_name)
        self.fitter = fits.Fits(d, type, sim_name)

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
            f"Plotting fitted function '{self.fitter.func.__name__}' at z={z:.2f}...")

        title = self.fitter.title(sim_name, z)
        save_dir = self.fitter.fit_dir(sim_name)
        plot_name = self.fitter.fit_fname(sim_name, radius, z)

        autosave = fig is None
        if autosave:
            fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.gca()

        bin_centres, hist_fit, r2, popt = self.fitter.calc_fit(
            z, radius, deltas, num_bins)

        label = "Fitted data"
        if self.fitter.func.__name__ is funcs.gaussian.__name__:
            _, _, sigma = popt
            label += f" ($\sigma = {abs(sigma):.2f}$)"

        ax.plot(bin_centres, hist_fit, label=label)

        # Show the R^2 in the legend:
        legend_addendum = f"$R^2 = {r2:.4f}$"

        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=legend_addendum))

        # fig.suptitle(title)
        ax.legend(handles=handles)

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)
            plt.close(fig)

            logger.debug(f"Saved Gaussian overdensity plot to '{plot_name}'")

        return fig, popt

    
    def gaussian_fit(self,
                     z: float,
                     radius: float,
                     deltas: unyt.unyt_array,
                     sim_name: str,
                     num_bins: int,
                     fig: plt.Figure = None) -> Tuple[plt.Figure, np.ndarray]:
        self.fitter.setup_gaussian()
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)

    def skewed_gaussian_fit(self,
                            z: float,
                            radius: float,
                            deltas: unyt.unyt_array,
                            sim_name: str,
                            num_bins: int,
                            fig: plt.Figure = None) -> Tuple[plt.Figure, np.ndarray]:
        self.fitter.setup_skewed_gaussian()
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)

    def n_gaussian_fit(self,
                       z: float,
                       radius: float,
                       deltas: unyt.unyt_array,
                       sim_name: str,
                       num_bins: int,
                       fig: plt.Figure = None,
                       num_fits: int = 10) -> Tuple[plt.Figure, np.ndarray]:
        self.fitter.setup_n_gaussian(num_fits)
        return self._gen_fit(z, radius, deltas, sim_name, num_bins, fig=fig)
