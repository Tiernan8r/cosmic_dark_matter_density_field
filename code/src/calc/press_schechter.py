import logging
from typing import List

import numpy as np
import unyt
from scipy import integrate
from src.calc import rho_bar, sample, std_dev
from src.util import enum
from src.util.constants import DELTA_CRIT, PRESS_SCHECHTER_KEY
from src.util.halos import halo_finder
from typing import Callable


class PressSchechter(sample.Sampler):

    def analytic_press_schechter(self, avg_den: float, masses: List[float], sigmas: List[float]):
        frac = np.abs(sigmas / masses).value

        press_schechter = np.sqrt(2 / np.pi) * (DELTA_CRIT / sigmas**2) * (
            avg_den / masses) * frac * np.exp(-DELTA_CRIT**2 / (2 * sigmas**2))

        return press_schechter

    def numerical_mass_function(self, avg_den: float, radii: List[float], masses: List[List[float]], fitting_func: Callable, func_params):

        F = []

        for i in range(len(radii)):
            popt = func_params[i]

            def f(x):
                return fitting_func(x, *popt)

            integrand, err = integrate.quad(f, DELTA_CRIT, np.inf)
            F.append(integrand)

        dF_dR = np.abs(np.gradient(F, radii))

        dR_dM = np.abs(np.gradient(radii, masses))

        dF_dM = dF_dR * dR_dM

        dn_dM = dF_dM * avg_den / masses

        return dn_dM

    def mass_function(self, hf):
        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        logger.debug(f"Working on redshift: {z}")

        tp = enum.DataType.SNAPSHOT
        snapshots_finder = halo_finder.HalosFinder(
            tp, self.config.sim_data.root, self.sim_name)

        # Translate the halo redshift back to the rounded one from the
        # config
        zs = self.config.redshifts
        nearest_z = min(zs, key=lambda x: abs(x-z))

        logger.info(f"Halo redshift of '{z}' corresponds to '{nearest_z}'")

        sf, = snapshots_finder.filter_data_files([nearest_z])
        ds_sf = self.dataset_cache.load(sf)
        z = ds_sf.current_redshift

        logger.debug(f"Found snapshot file '{sf}' that matches this redshift")

        sd = std_dev.StandardDeviation(self, tp, self.sim_name)
        rb = rho_bar.RhoBar(self, tp, self.sim_name)

        avg_den = rb.rho_bar(sf)

        logger.info(f"Simulation average density is: {avg_den}")

        # If cache entries exist, may not need to recalculate
        key = (sf, self.type.value, PRESS_SCHECHTER_KEY, z)
        results = self.cache[key].val
        needs_recalculation = results is None
        needs_recalculation |= not self.config.caches.use_press_schechter_cache

        logger.debug(
            f"Override press-schechter cache? {not self.config.caches.use_press_schechter_cache}")  # noqa: E501

        masses, ps = [], []

        # If the radius key is missing, need to do a full sample run
        if needs_recalculation:
            logger.debug(
                f"Calculating cache values for '{PRESS_SCHECHTER_KEY}'...")

            # Run the full sample, and save the result to the cache
            masses, sigmas = sd.masses_sigmas(
                sf, self.config.sampling.std_dev_from_fit)
            ps = self.analytic_press_schechter(avg_den, masses, sigmas)

            self.cache[key] = (masses, ps)

        # The key can exist, but there may not be enough samples...
        else:
            logger.debug("Using cached press schechter values...")
            masses, ps = results

        if isinstance(ps, unyt.unyt_array):
            logger.info(f"Press Schechter units are: {ps.units}")

        return masses, ps
