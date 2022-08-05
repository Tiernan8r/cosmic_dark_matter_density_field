import logging
from typing import List

import numpy as np
import src.calc.rho_bar as rb
import unyt
from scipy import integrate
from src.util.constants import DELTA_CRIT, PRESS_SCHECHTER_KEY
from src.util import units as u


class PressSchechter(rb.RhoBar):

    def analytic_press_schechter(self, avg_den: float, masses: List[float], sigmas: List[float]):
        frac = np.abs(np.log(sigmas) / np.log(masses))

        press_schechter = np.sqrt(2 / np.pi) * (avg_den / masses**2) * DELTA_CRIT / \
            sigmas * frac * np.exp(-DELTA_CRIT / (2 * sigmas**2))

        return press_schechter

    def numerical_mass_function(self, avg_den: float, radii: List[float], masses: List[List[float]], fitting_func, func_params):

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

    def mass_function(self, hf, radius):
        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # Get rho bar 0
        rho_0 = self.rho_bar_0(hf)
        if rho_0 is None:
            logger.warning("Could not calculate rho bar 0!")
            return
        rho_0 = rho_0.to(u.density(ds))

        logger.info(f"Simulation average density is: {rho_0}")

        # If cache entries exist, may not need to recalculate
        key = (hf, self.type.value, PRESS_SCHECHTER_KEY, z, float(radius))
        results = self.cache[key].val
        needs_recalculation = results is None
        needs_recalculation |= not self.config.caches.use_press_schechter_cache

        logger.debug(
            f"Override press-schechter cache? {not self.config.caches.use_press_schechter_cache}")  # noqa: E501

        masses, std_devs = [], []

        # If the radius key is missing, need to do a full sample run
        if needs_recalculation:
            logger.debug(
                f"Calculating cache values for '{PRESS_SCHECHTER_KEY}'...")

            # Run the full sample, and save the result to the cache
            masses = self.sample_masses(hf, radius)
            std_devs = self.sample_std_devs(hf, radius)

            self.cache[key] = (masses, std_devs)

        # The key can exist, but there may not be enough samples...
        else:
            logger.debug("Using cached press schechter values...")
            masses = results[0]
            std_devs = results[1]

        logger.info(f"Mass units are: {masses.units}")

        frac = np.abs(np.log(std_devs) / np.log(masses))

        press_schechter = np.sqrt(2 / np.pi) * (rho_0 / masses**2) * DELTA_CRIT / \
            std_devs * frac * np.exp(-DELTA_CRIT / (2 * std_devs**2))

        if isinstance(press_schechter, unyt.unyt_array):
            logger.debug(
                f"Press-Schechter mass function units are: {press_schechter.units}")

        sorted_zip = sorted(zip(masses, press_schechter))
        masses = [sz[0] for sz in sorted_zip]
        press_schechter = [sz[1] for sz in sorted_zip]

        return masses, press_schechter

    def sample_masses(self, hf, radius) -> unyt.unyt_array:
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self.sample_masses.__name__)

        # Load the halo data set
        ds = self.dataset_cache.load(hf)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(hf, radius, z)

        # Convert the list of masses per sample, into a 1D list
        masses = ds.arr([], u.mass(ds))

        logger.info(f"Masses units are: {masses.units}")

        for m in sphere_samples:
            # Ensure the units match
            m = m.to(masses.units)
            total_mass = ds.arr([np.sum(m)], masses.units)
            masses = unyt.uconcatenate((masses, total_mass))

        # Convert mass units to Msun
        masses = masses.to(u.mass(ds))

        return masses

    def sample_std_devs(self, hf, radius) -> np.ndarray:
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self.sample_std_devs.__name__)

        # Load the halo data set
        ds = self.dataset_cache.load(hf)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(hf, radius, z)

        # Convert the list of masses per sample, into a 1D list
        std_devs = []

        for m in sphere_samples:
            std_dev = np.std(m)
            std_devs.append(std_dev)

        return np.array(std_devs)
