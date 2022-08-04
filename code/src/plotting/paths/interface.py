import os
from src import interface

class IPaths(interface.Interface):

    def _compile_plot_dir(self, subdir, *args):
        dirname = os.path.join(self.config.plotting.dirs.root, subdir)

        return dirname.format(*args)

    def _compile_plot_fname(self, subdir, fname, *args):
        plot_fname = os.path.join(self.config.plotting.dirs.root, subdir, fname)

        return plot_fname.format(*args)
