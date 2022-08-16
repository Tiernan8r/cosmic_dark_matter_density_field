import matplotlib.pyplot as plt
from src.plotting.paths import Paths


class IPlot(Paths):

    def new_figure(self):
        plt.cla()
        plt.clf()

        fig = plt.figure()
        fig.tight_layout()

        return fig
