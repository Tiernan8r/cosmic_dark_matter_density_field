from src.plotting import mass_function, overdensity, std_dev, fits
import matplotlib.pyplot as plt
import src.fitting.funcs as f
import numpy as np
import yt
import os


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

        ax = fig.gca()
        ax.plot(x, gauss, linestyle="dashed",
                label=f"Gaussian Fit $\sigma = {sigma}$")

        return fig
