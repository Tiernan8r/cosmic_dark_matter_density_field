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
                 legend=str,
                 logscale=False,
                 fig: plt.Figure = None):
        if not yt.is_root():
            return

        autosave = fig is None
        if autosave:
            fig: plt.Figure = self.new_figure()

        logger = logging.getLogger(
            __name__ + "." + self._std_dev.__name__)

        ax = fig.gca()

        ax.plot(x, y, label=legend)

        # fig.suptitle(title)
        ax.set_xlabel(xlabel)  # noqa: W605
        ax.set_ylabel(ylabel)  # noqa: W605, E501

        if logscale:
            ax.set_xscale("log")
            ax.set_yscale("log")

        # Ensure the folders exist before attempting to save an image to it...
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_fname)
            plt.close(fig)

            logger.debug(f"Saved std dev figure to '{plot_fname}'")

        return fig

    def std_dev_func_M(self,
                       z: float,
                       Ms: np.ndarray,
                       sigmas: np.ndarray,
                       sim_name: str,
                       logscale=True,
                       fig=None):
        title = f"Standard Deviation as a function of sphere mass for {sim_name}; z={z:.2f}"
        save_dir = self.std_dev_dir(sim_name)
        plot_name = self.std_dev_fname(sim_name, z)
        legend = f"z = {z:.2f}"

        return self._std_dev(Ms, sigmas, title, save_dir,
                             plot_name, xlabel="M ($M_\odot$/h)", ylabel="$\sigma^2$", legend=legend, logscale=logscale, fig=fig)

    def std_dev_func_R(self,
                       z: float,
                       Rs: np.ndarray,
                       sigmas: np.ndarray,
                       sim_name: str,
                       logscale=True,
                       fig=None):
        title = f"Standard Deviation as a function of sampling radius for {sim_name}; z={z:.2f}"
        save_dir = self.std_dev_dir(sim_name)
        plot_name = self.std_dev_fname(sim_name, z)
        legend = f"z = {z:.2f}"

        return self._std_dev(Rs, sigmas, title, save_dir,
                             plot_name, xlabel="R (Mpc/h)", ylabel="$\sigma^2$", legend=legend, logscale=logscale, fig=fig)
