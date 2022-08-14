import os

from src.util import interface


class IPaths(interface.Interface):

    def _compile_plot_dir(self, subdir, *args):
        dir_ptrn = os.path.join(self.config.plotting.dirs.root, subdir)

        # ensure the paths exist
        dname = dir_ptrn.format(*args)
        if not os.path.isdir(dname):
            try:
                os.makedirs(dname)
            except FileExistsError as fee:
                pass

        return dname

    def _compile_plot_fname(self, subdir, fname, *args):
        fname_ptrn = os.path.join(
            self.config.plotting.dirs.root, subdir, fname)

        fname = fname_ptrn.format(*args)

        # Ensure the paths exist
        pth = os.path.dirname(fname)
        if not os.path.isdir(pth):
            try:
                os.makedirs(pth)
            except FileExistsError as fee:
                pass

        return fname
