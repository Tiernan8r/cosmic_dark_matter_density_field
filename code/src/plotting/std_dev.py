import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import src.plotting.interface as I
import yt


class StandardDeviation(I.IPlot):

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
