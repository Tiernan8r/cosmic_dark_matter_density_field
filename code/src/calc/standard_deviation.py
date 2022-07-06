import logging
from typing import Dict

import numpy as np
from src.calc.classes import calculator
from src.const.constants import (MASS_FUNCTION_KEY, STD_DEV_KEY, UNITS_KEY,
                                 UNITS_PS_MASS, UNITS_PS_STD_DEV)


class StandardDeviation(calculator.Calculator):

    def std_dev_func_mass(self, rck) -> Dict[float, float]:
        logger = logging.getLogger(
            __name__ + "." + self.std_dev_func_mass.__name__)

        ds = self._dataset_cache.load(rck)
        z = ds.current_redshift

        std_dev_map = None

        for radius in sorted(self._config.radii):

            masses = self._cache[rck, MASS_FUNCTION_KEY, z, float(radius)].val
            if masses is None:
                logger.warning(f"No masses calculated for dataset '{rck}' at a radius of '{radius}'")
                continue

            avg_mass = np.average(masses)

            std_dev = self._cache[rck, STD_DEV_KEY, z, float(radius)].val
            if std_dev is None:
                logger.warning(f"No standard deviation calculated for data set '{rck}' at a radius '{radius}'")
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
