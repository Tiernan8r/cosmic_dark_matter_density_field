import logging
import os
from typing import Callable, Dict, Tuple

import numpy as np
import scipy.optimize
import scipy.stats
import unyt
from src.util.constants import (BIN_CENTRE_KEY, FITS_KEY, HIST_FIT_KEY,
                                POPT_KEY, R2_KEY)
from src.fitting import funcs
from src.fitting.params import FittingParameters
from src.util import data, enum
from src.calc import mass_function


class Fits(FittingParameters):

    def __init__(self, d: data.Data, type: enum.DataType = ..., sim_name: str = ...):
        super().__init__(d, type, sim_name)
        self.setup_gaussian()

    def fit_functions(self) -> Dict[str, Callable]:
        return {
            funcs.gaussian.__name__: funcs.gaussian,
            funcs.skew_gaussian.__name__: funcs.skew_gaussian,
            funcs.n_gaussian.__name__: funcs.n_gaussian,
        }

    def filter_fit(self, y: np.ndarray) -> np.ndarray:
        # # offset final values to get close to 0
        # final_val: float = y[-1]

        # y = y - final_val
        # print("OFFSET Y NOW=", y)

        # filter for close to 0, and set equal to 0
        zeros = np.zeros(y.shape)
        zero_idxs = np.where(np.isclose(y, zeros))

        y[zero_idxs] = 0

        # Filter for neg values
        neg_idxs = np.where(y < 0)
        y[neg_idxs] = 0

        return y

    def calc_fit(self,
                 z: float,
                 radius: float,
                 deltas: unyt.unyt_array,
                 num_bins: int) -> Tuple[np.ndarray, np.ndarray, float, list]:
        logger = logging.getLogger(__name__ + "." + self.calc_fit.__name__)

        logger.debug(
            f"Calculating fitting parameters for function '{self.func.__name__}' at z={z:.2f}; r={radius:.2f}...")

        key = (self.sim_name, self.type.value, FITS_KEY,
               self.func.__name__, z, float(radius))
        cache_vals = self._cache[key].val

        if cache_vals is None or not self.config.caches.use_fits_cache:
            logger.debug(f"Recalculating cached fit values...")

            # ================
            # Fit the Function
            # ================
            od_bins = np.linspace(start=-1, stop=2, num=num_bins)

            hist, bin_edges = np.histogram(deltas,
                                           bins=od_bins)
            bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

            try:
                popt, pcov = scipy.optimize.curve_fit(
                    self.func, bin_centres, hist, p0=self._p0)
            except RuntimeError as re:
                logger.error(
                    "Could not fit curve to data, defaulting to initial guess parameters!")
                logger.error(re)
                unpacker = lambda *x: x
                popt = unpacker(*self._p0)

            logger.debug(f"Curve fit coefficients are: {popt}")

            # Get the fitted curve
            hist_fit = self.func(bin_centres, *popt)

            # Filter the result:
            hist_fit = self.filter_fit(hist_fit)

            # =============================================================
            # R^2 QUALITY OF FIT TEST
            # =============================================================
            logger.debug("Calculating R^2 value")

            ss_res = np.sum((hist - hist_fit)**2)
            ss_tot = np.sum((hist - np.mean(hist))**2)

            r2 = 1 - (ss_res / ss_tot)

            logger.debug(f"R^2 is = {r2}")

            # =============================================================
            # CACHE RESULTS
            # =============================================================
            cache_vals = {
                BIN_CENTRE_KEY: bin_centres,
                HIST_FIT_KEY: hist_fit,
                R2_KEY: r2,
                POPT_KEY: popt
            }

            self._cache[key] = cache_vals
        else:
            logger.debug("Using cached fits values...")

        return cache_vals[BIN_CENTRE_KEY], cache_vals[HIST_FIT_KEY], cache_vals[R2_KEY], cache_vals[POPT_KEY]
