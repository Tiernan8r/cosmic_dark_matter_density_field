import logging
from typing import Dict

import numpy as np
import src.calc.sample as sample
from src.const.constants import (MASS_FUNCTION_KEY, OVERDENSITIES_KEY, STD_DEV_KEY, UNITS_KEY,
                                 UNITS_PS_MASS, UNITS_PS_STD_DEV)


class StandardDeviation(sample.Sampler):

    def std_dev_func_mass(self, rck) -> Dict[float, float]:
        logger = logging.getLogger(
            __name__ + "." + self.std_dev_func_mass.__name__)

        ds = self._dataset_cache.load(rck)
        z = ds.current_redshift

        std_dev_map = None

        for radius in sorted(self._config.radii):

            masses = self._cache[rck, MASS_FUNCTION_KEY, z, float(radius)].val
            if masses is None:
                logger.warning(
                    f"No masses calculated for dataset '{rck}' at a radius of '{radius}'")
                continue

            avg_mass = np.average(masses)

            std_dev = self._cache[rck, STD_DEV_KEY, z, float(radius)].val
            if std_dev is None:
                logger.warning(
                    f"No standard deviation calculated for data set '{rck}' at a radius '{radius}'")
                continue

            # Ensure that mass units are consistent
            mass_units = self._cache[rck, UNITS_KEY, z, UNITS_PS_MASS].val
            if mass_units is None:
                mass_units = avg_mass.units
                self._cache[rck, UNITS_KEY, z,
                            UNITS_PS_MASS] = mass_units
                logger.debug(f"Cached mass units as: {mass_units}")

            avg_mass = avg_mass.to(mass_units)

            # Ensure that std dev units are consistent:
            std_dev_units = self._cache[rck,
                                        UNITS_KEY, z, UNITS_PS_STD_DEV].val
            if std_dev_units is None:
                std_dev_units = std_dev.units
                self._cache[rck, UNITS_KEY, z,
                            UNITS_PS_STD_DEV] = std_dev_units
                logger.debug(f"Cached std dev units as: {std_dev_units}")

            std_dev = std_dev.to(std_dev_units)

            mass_value = float(avg_mass.v)

            if std_dev_map is None:
                std_dev_map = {}

            std_dev_map[mass_value] = float(std_dev)
            # if mass_value not in std_dev_map:
            #     std_dev_map[mass_value] = np.array([std_dev])
            # else:
            #     std_dev_map[mass_value] = np.concatenate((std_dev_map[mass_value], [std_dev]))

        return std_dev_map

    def std_dev(self, rck, radius):
        logger = logging.getLogger(__name__ + "." + self.std_dev.__name__)

        ds = self.dataset_cache.load(rck)
        z = ds.current_redshift

        # If cache entries exist, may not need to recalculate
        key = (rck, STD_DEV_KEY, z, float(radius))
        std_dev = self._cache[key].val
        needs_recalculation = std_dev is None
        # Could force recalculation
        needs_recalculation |= not self.config.caches.use_standard_deviation_cache
        logger.debug(
            f"Override standard deviation cache? {not self.config.caches.use_standard_deviation_cache}")

        if needs_recalculation:
            logger.debug(
                f"No standard deviation found in cache for '{STD_DEV_KEY}', calculating...")

            # Get the overdensities calculated for this radius
            od_key = (rck, OVERDENSITIES_KEY, z, float(radius))
            overdensities = self.cache[od_key].val

            std_dev = np.std(overdensities)
            self.cache[key] = std_dev

        else:
            logger.debug("Standard deviation already cached.")

        logger.info(f"Overdensities standard deviation is {std_dev}")

        return std_dev
