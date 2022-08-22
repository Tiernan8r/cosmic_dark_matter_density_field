import matplotlib.pyplot as plt
import numpy as np
import src.fitting.funcs as f
import unyt
import yt
from src.plotting import fits, mass_function, overdensity, std_dev


class Plotter(mass_function.MassFunction, overdensity.Overdensity, std_dev.StandardDeviation, fits.Fits):

    def gaussian(self,
                 A: float,
                 mu: float,
                 sigma: float,
                 num_bins: int,
                 fig: plt.Figure = None):

        if not yt.is_root():
            return

        autosave = fig is None
        if autosave:
            fig: plt.Figure = self.new_figure()

        x = np.linspace(-1, 2, num_bins)
        gauss = f.gaussian(x, A, mu, sigma)

        s = sigma
        if isinstance(s, unyt.unyt_quantity):
            s = sigma.value
        label = f"Gaussian Fit ($\sigma = {s:.2f}$)"

        ax = fig.gca()
        ax.plot(x, gauss, linestyle="dashed",
                label=label)
        ax.legend()

        return fig
