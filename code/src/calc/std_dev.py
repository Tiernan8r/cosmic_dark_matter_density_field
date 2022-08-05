import logging
from typing import Tuple

import numpy as np
from src.calc import overdensity
import src.calc.rho_bar as rho_bar
import src.util.units as u
import unyt
from src.fitting import fits
from src.util.constants import OVERDENSITIES_KEY, STD_DEV_KEY
from src.util.halos import halo_finder


class StandardDeviation(rho_bar.RhoBar):

    def masses_sigmas(self, hf, from_fit=True) -> Tuple[unyt.unyt_array, np.ndarray]:
        logger = logging.getLogger(
            __name__ + "." + self.masses_sigmas.__name__)

        ds = self.dataset_cache.load(hf)

        sigmas = []

        radii = self.config.radii
        logger.debug(f"Creating std devs for radii '{radii}'")

        for radius in radii:
            sdev = self.std_dev(hf, radius, from_fit=from_fit)

            sigmas.append(sdev)

        av_den = self.rho_bar(hf)

        masses = []
        for r in radii:
            R = ds.quan(r, u.length_cm(ds))

            V = 4 / 3 * np.pi * R**3
            m = av_den * V

            masses.append(m)

        return ds.arr(masses, u.mass(ds)), np.abs(sigmas)

    def std_dev(self, hf: str, radius: float, from_fit=True):
        logger = logging.getLogger(__name__ + "." + self.std_dev.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # If cache entries exist, may not need to recalculate
        key = (hf, self.type.value, STD_DEV_KEY, z, float(radius))
        std_dev = self.cache[key].val
        needs_recalculation = std_dev is None
        # Could force recalculation
        needs_recalculation |= not self.config.caches.use_standard_deviation_cache  # noqa: E501
        logger.debug(
            f"Override standard deviation cache? {not self.config.caches.use_standard_deviation_cache}")  # noqa: E501

        if needs_recalculation:
            logger.debug(
                f"No standard deviation found in cache for '{STD_DEV_KEY}', calculating...")  # noqa: E501

            # Get the overdensities calculated for this radius
            logger.debug(f"Reading cached overdensities at r={radius}; z={z}")
            od = overdensity.Overdensity(self, self.type, self.sim_name)
            overdensities = od.calc_overdensities(hf, radius)

            if from_fit:
                # Reads gaussian fits by default
                fitter = fits.Fits(self, self.type, self.sim_name)
                _, _, _, popt = fitter.calc_fit(
                    z, radius, overdensities, self.config.sampling.num_hist_bins)

                _, _, std_dev = popt
                # Make sure the sigma is positive
                std_dev = np.abs(std_dev)

            else:

                std_dev = np.std(overdensities)

            self.cache[key] = std_dev

        else:
            logger.debug("Standard deviation already cached.")

        logger.info(f"Overdensities standard deviation is {std_dev}")

        return std_dev

    def extrapolate(self, from_z: float, to_z: float, radius: float, from_fits=True):
        logger = logging.getLogger(__name__ + "." + self.extrapolate.__name__)

        logger.debug(
            f"Finding {self.type.value} file for a redshift of {from_z:.2f} on simulation '{self.sim_name}'")  # noqa: E501
        halos_finder = halo_finder.HalosFinder(
            halo_type=self.type, root=self.config.sim_data.root, sim_name=self.sim_name)

        halo_files = halos_finder.filter_data_files(desired=[from_z])

        logger.debug(
            f"Extrapolating the standard deviation at {from_z:.2f} to {to_z:.2f}")
        logger.debug(f"Found halo files = {halo_files}")
        from_hf = halo_files[0]

        from_std_dev = self.std_dev(from_hf, radius, from_fit=from_fits)

        extrapolated = from_std_dev * (1 + from_z) / (1 + to_z)

        return extrapolated
