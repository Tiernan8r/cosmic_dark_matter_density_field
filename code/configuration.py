from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import yaml

from constants import (CONF_KEY_CACHE_MASS, CONF_KEY_CACHE_OD,
                       CONF_KEY_CACHE_PS, CONF_KEY_CACHE_RHO_BAR,
                       CONF_KEY_CACHE_STD_DEV, CONF_KEY_CACHE_TOTAL,
                       CONF_KEY_NUM_HIST_BINS, CONF_KEY_NUM_OD_HIST_BINS,
                       CONF_KEY_NUM_SPHERE_SAMPLES, CONF_KEY_RADII,
                       CONF_KEY_REDSHIFTS, CONF_KEY_ROOT, CONF_KEY_SIM_NAMES,
                       CONFIGURATION_FILE)
from defaults import (DEF_NUM_HIST_BINS, DEF_NUM_OD_HIST_BINS,
                      DEF_NUM_SPHERE_SAMPLES, DEF_RADII, DEF_REDSHIFTS,
                      DEF_ROOT, DEF_SIM_NAMES, DEF_USE_MASSES_CACHE,
                      DEF_USE_OVERDENSITIES_CACHE, DEF_USE_PS_CACHE,
                      DEF_USE_RHO_BAR_CACHE, DEF_USE_STD_DEV_CACHE,
                      DEF_USE_TOTAL_MASSES_CACHE)


def new(args: List[str]) -> Configuration:
    logger = logging.getLogger(__name__ + "." + new.__name__)
    logger.debug(f"Initialising config parsing with arguments: {args}")

    config_file = CONFIGURATION_FILE
    if len(args) > 0:
        config_file = args[0]

    logger.debug(
        f"Attempting to create Configuration object with config file='{config_file}'")

    # Return the default Configuration if there was an issue reading
    # the provided file, eg: doesn't exist, or yaml loading error
    try:
        return Configuration(config_file)
    except:
        return Configuration()


class Configuration:

    def __init__(self, config_file=CONFIGURATION_FILE):
        self._config_file = config_file
        self._config = self._load()

    def _load(self) -> Dict[str, Any]:
        conf = {}
        with open(self._config_file) as f:
            conf = yaml.load(f, Loader=yaml.SafeLoader)

        return conf

    @property
    def num_hist_bins(self):
        return self._config.get(CONF_KEY_NUM_HIST_BINS, DEF_NUM_HIST_BINS)

    @property
    def num_overdensity_hist_bins(self):
        return self._config.get(CONF_KEY_NUM_OD_HIST_BINS, DEF_NUM_OD_HIST_BINS)

    @property
    def num_sphere_samples(self):
        return self._config.get(CONF_KEY_NUM_SPHERE_SAMPLES, DEF_NUM_SPHERE_SAMPLES)

    @property
    def radii(self):
        return self._config.get(CONF_KEY_RADII, DEF_RADII)

    @property
    def redshifts(self):
        return self._config.get(CONF_KEY_REDSHIFTS, DEF_REDSHIFTS)

    @property
    def root(self):
        return self._config.get(CONF_KEY_ROOT, DEF_ROOT)

    @property
    def sim_names(self):
        return self._config.get(CONF_KEY_SIM_NAMES, DEF_SIM_NAMES)

    @property
    def paths(self):
        pths = []
        for sm in self.sim_names:
            pth = os.path.join(self.root, sm)
            pths.append(pth)

        return pths

    @property
    def use_total_masses_cache(self):
        return self._config.get(CONF_KEY_CACHE_TOTAL, DEF_USE_TOTAL_MASSES_CACHE)

    @property
    def use_masses_cache(self):
        return self._config.get(CONF_KEY_CACHE_MASS, DEF_USE_MASSES_CACHE)

    @property
    def use_overdensities_cache(self):
        return self._config.get(CONF_KEY_CACHE_OD, DEF_USE_OVERDENSITIES_CACHE)

    @property
    def use_rho_bar_cache(self):
        return self._config.get(CONF_KEY_CACHE_RHO_BAR, DEF_USE_RHO_BAR_CACHE)

    @property
    def use_standard_deviation_cache(self):
        return self._config.get(CONF_KEY_CACHE_STD_DEV, DEF_USE_STD_DEV_CACHE)

    @property
    def use_press_schechter_cache(self):
        return self._config.get(CONF_KEY_CACHE_PS, DEF_USE_PS_CACHE)
