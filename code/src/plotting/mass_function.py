import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import src.plotting.interface as I
import yt


class MassFunction(I.IPlot):

    def _mass_function(self, x, y, title, save_dir, plot_name, fig=None):
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

        fig.suptitle(title)
        ax.set_xlabel("$\log{M_{vir}}$")  # noqa: W605
        ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")  # noqa: W605, E501

        # Ensure the folders exist before attempting to save an image to it...
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)
            plt.close(fig)

        return fig

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

        self._mass_function(bin_edges, mass_hist, title,
                            save_dir, plot_name)
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

        self._mass_function(mass_bins, mass_hist, title,
                            save_dir, plot_name)

    def press_schechter(self,
                        z: float,
                        ps_hist: np.ndarray,
                        bin_edges: np.ndarray,
                        sim_name: str):
        title = f"Press Schecter Mass Function at z={z:.2f}"
        save_dir = self.press_schechter_dir(sim_name)
        plot_name = self.press_schechter_fname(sim_name, z)

        self._mass_function(bin_edges, ps_hist, title,
                            save_dir, plot_name)

    def numerical_mass_function(self,
                                z: float,
                                vals: np.ndarray,
                                masses: np.ndarray,
                                sim_name: str,
                                func_name: str):
        title = f"Numerical Mass Function at z={z:.2f} (fit = {func_name})"
        save_dir = self.numerical_mass_function_dir(sim_name, func_name)
        plot_name = self.numerical_mass_function_fname(
            sim_name, func_name, z)

        self._mass_function(masses, vals, title,
                            save_dir, plot_name)

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
