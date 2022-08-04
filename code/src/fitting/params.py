import abc

import src.fitting.funcs as funcs
from src.plotting.paths.fits import Fits

class FittingParameters(Fits):

    def setup_parameters(self, func_name, *args):
        if func_name == funcs.gaussian.__name__:
            self.setup_gaussian()
        elif func_name == funcs.skew_gaussian.__name__:
            self.setup_skewed_gaussian()
        elif func_name == funcs.n_gaussian.__name__:
            self.setup_n_gaussian(*args)

    def setup_gaussian(self):
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = [1, 0, 1]
        self.title = self.gaussian_title
        self.func = funcs.gaussian
        self.fit_dir = self.gaussian_fit_dir
        self.fit_fname = self.gaussian_fit_fname

    def setup_skewed_gaussian(self):
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = [1, 0, 1, 0, 0]
        self.title = self.skewed_gaussian_title
        self.func = funcs.skew_gaussian
        self.fit_dir = self.skewed_gaussian_fit_dir
        self.fit_fname = self.skewed_gaussian_fit_fname

    def setup_n_gaussian(self, num_fits: int = 10):
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma for Gaussian...)
        self._p0 = []
        for i in range(num_fits):
            self._p0 += [i, 1, 1]
        self.title = self.n_gaussian_title
        self.func = funcs.n_gaussian
        self.fit_dir = self.n_gaussian_fit_dir
        self.fit_fname = self.n_gaussian_fit_fname
