import logging
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from src.calc.mass_function import create_histogram
import src.plotting.interface as I
import yt


class MassFunction(I.IPlot):

    def _mass_function(self, x, y, title, save_dir, plot_name, label: str = None, fig=None):
        if len(x) == 0 or len(y) == 0:
            logger = logging.getLogger(
                __name__ + "." + self._mass_function.__name__)
            logger.warning("Attempting to plot empty data!")
            return

        autosave = fig is None
        if autosave:
            fig = self.new_figure()
        ax = fig.gca()

        # Filter values:
        y = np.round(y, decimals=100)
        non_zero = (y != 0)
        y = y[non_zero]
        x = x[non_zero]

        ax.plot(x, y, label=label)
        ax.set_xscale("log")
        ax.set_yscale("log")

        if label is not None:
            ax.legend()

        # fig.suptitle(title)
        # ax.set_xlabel("$\log{M_{vir}}$")  # noqa: W605
        # ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")  # noqa: W605, E501
        ax.set_xlabel("M ($M_\odot$/h)")  # noqa: W605
        ax.set_ylabel("$\phi=\\frac{d n}{d M}$")  # noqa: W605, E501

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

    def _scale_axes(self, x, y, ref):
        # Filter the PS mass function to be in x-axis range of total
        min_x_total = min(ref)
        max_x_total = max(ref)

        max_idxs = np.where(x < max_x_total)
        x = x[max_idxs]
        y = y[max_idxs]
        min_idxs = np.where(x > min_x_total)
        x = x[min_idxs]
        y = y[min_idxs]

        return x, y

    def press_schechter_total_comparison(self,
                                         z: float,
                                         total_bins: np.ndarray,
                                         total_hist: np.ndarray,
                                         Ms: np.ndarray,
                                         ps_fit: np.ndarray,
                                         sim_name: str):
        fig = self.new_figure()

        title = f"Compared Press Schecter Mass Function at z={z:.2f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_total_fname(sim_name, z)

        # Filter the PS mass function to be in x-axis range of total
        Ms, ps_fit = self._scale_axes(Ms, ps_fit, total_bins)

        if len(Ms) == 0 or len(ps_fit) == 0:
            logger = logging.getLogger(
                __name__ + "." + self.press_schechter_total_comparison.__name__)
            logger.warning("Scaled ps fit is empty!")
            return

        # Rescale:
        initial_val = total_hist[0]
        initial_ps_val = ps_fit[0]

        ps_fit = ps_fit / initial_ps_val * initial_val

        self._mass_function(total_bins, total_hist, title,
                            save_dir, plot_name, label="total mass function", fig=fig)
        self._mass_function(Ms, ps_fit, title,
                            save_dir, plot_name, label="press schechter mass function", fig=fig)

        ax = fig.gca()
        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=f"z = {z:.2f}"))
        ax.legend(handles=handles)

        fig.savefig(plot_name)

        logger = logging.getLogger(
            __name__ + "." + self.press_schechter_total_comparison.__name__)
        logger.debug(
            f"Saved press-schechter comparison mass function figure to '{plot_name}'")

    def press_schechter_analytic_comparison(self,
                                            z: float,
                                            radius: float,
                                            analytic_masses: np.ndarray,
                                            analytic: np.ndarray,
                                            ps_masses: np.ndarray,
                                            ps_fit: np.ndarray,
                                            sim_name: str):
        fig = self.new_figure()
        logger = logging.getLogger(
            __name__ + "." + self.press_schechter_analytic_comparison.__name__)

        title = f"Compared Press Schecter Mass Function at z={z:.2f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_analytic_fname(sim_name, z, radius)

        if len(analytic) == 0:
            logger.warning("Analytic mass function is empty, skipping!")
            return

        # Filter the PS mass function to be in x-axis range of the analytic
        ps_masses, ps_fit = self._scale_axes(
            ps_masses, ps_fit, analytic_masses)

        if len(ps_masses) == 0 or len(ps_fit) == 0:
            logger.warning("Scaled ps fit is empty, skipping!")
            return

        # Rescale:
        initial_val = analytic[0]
        initial_ps_val = ps_fit[0]

        ps_fit = ps_fit / initial_ps_val * initial_val

        self._mass_function(analytic_masses, analytic, title,
                            save_dir, plot_name, label="analytic mass function", fig=fig)
        self._mass_function(ps_masses, ps_fit, title,
                            save_dir, plot_name, label="press schechter mass function", fig=fig)

        ax = fig.gca()
        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=f"z = {z:.2f}"))
        handles.append(mpatches.Patch(
            color='none', label=f"R = {radius:.2f} Mpc/h"))
        ax.legend(handles=handles)

        fig.savefig(plot_name)

        logger.debug(
            f"Saved press-schechter comparison analytic mass function figure to '{plot_name}'")

    def press_schechter_numerical_comparison(self,
                                             z: float,
                                             Ms: np.ndarray,
                                             numeric: np.ndarray,
                                             ps_fit: np.ndarray,
                                             sim_name: str,
                                             fit_name: str):
        fig = self.new_figure()

        title = f"Compared Press Schecter Mass Function at z={z:.2f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_numerical_fname(sim_name, fit_name, z)

        # Rescale:
        initial_val = numeric[0]
        initial_ps_val = ps_fit[0]

        ps_fit = ps_fit / initial_ps_val * initial_val

        self._mass_function(Ms, numeric, title,
                            save_dir, plot_name, label=f"numerical ({fit_name}) mass function", fig=fig)
        self._mass_function(Ms, ps_fit, title,
                            save_dir, plot_name, label="press schechter mass function", fig=fig)

        ax = fig.gca()
        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=f"z = {z:.2f}"))
        ax.legend(handles=handles)

        fig.savefig(plot_name)

        logger = logging.getLogger(
            __name__ + "." + self.press_schechter_numerical_comparison.__name__)
        logger.debug(
            f"Saved press-schechter comparison numerical mass function figure to '{plot_name}'")

    def total_to_numerical_comparison(self,
                                      z: float,
                                      total_bins: np.ndarray,
                                      total_hist: np.ndarray,
                                      Ms: np.ndarray,
                                      numeric: np.ndarray,
                                      sim_name: str,
                                      fit_name: str):
        fig = self.new_figure()
        logger = logging.getLogger(
            __name__ + "." + self.total_to_numerical_comparison.__name__)

        title = f"Compared Press Schecter Mass Function at z={z:.2f}"  # noqa: E501
        save_dir = self.compared_dir(sim_name)
        plot_name = self.compared_total_to_numerical_fname(
            sim_name, fit_name, z)

        # Filter the numeric mass function to be in x-axis range of total
        Ms, numeric = self._scale_axes(Ms, numeric, total_bins)

        if len(Ms) == 0 or len(numeric) == 0:
            logger.debug("Scaled axes are empty, skipping!")
            return

        # Rescale:
        initial_val = numeric[0]
        initial_ps_val = total_hist[0]

        total_hist = total_hist / initial_ps_val * initial_val

        self._mass_function(Ms, numeric, title,
                            save_dir, plot_name, label=f"numerical ({fit_name}) mass function", fig=fig)
        self._mass_function(total_bins, total_hist, title,
                            save_dir, plot_name, label="total mass function", fig=fig)

        ax = fig.gca()
        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=f"z = {z:.2f}"))
        ax.legend(handles=handles)

        fig.savefig(plot_name)

        logger = logging.getLogger(
            __name__ + "." + self.press_schechter_numerical_comparison.__name__)
        logger.debug(
            f"Saved press-schechter comparison numerical mass function figure to '{plot_name}'")