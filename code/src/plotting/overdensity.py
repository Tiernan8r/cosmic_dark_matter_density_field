import logging
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import unyt
import yt
import numpy as np
import src.plotting.interface as I


class Overdensity(I.IPlot):

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

        # fig.suptitle(title)
        ax.set_xlabel("Overdensity $\delta$")
        ax.set_ylabel("Frequency")  # noqa: W605

        handles, _ = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=f"z = {z:.2f}"))
        handles.append(mpatches.Patch(
            color='none', label=f"R = {radius:.2f} Mpc/h"))
        ax.legend(handles=handles)

        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)

        if autosave:
            fig.savefig(plot_name)
            plt.close(fig)

            logger.debug(f"Saved overdensity plot to '{plot_name}'")

        return fig
