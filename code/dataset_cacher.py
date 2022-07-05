import __future__

import logging
import os
import threading

import numpy as np
import unyt
import yt
import yt.extensions.legacy

_existing_instance = None


def new():
    global _existing_instance
    if _existing_instance is None:
        _existing_instance = CachedDataSet()

    return _existing_instance


class CachedDataSet:

    _load_key = "dataset"
    _all_data_key = "all_data"
    _sphere_key = "sphere"

    _save_path = "../data/data_set_cache.npy"

    def __init__(self):
        self._mutex = threading.Lock()
        with self._mutex:
            self._cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self._save_path):
            with open(self._save_path, "rb") as f:
                return np.load(f, allow_pickle=True)
        else:
            return {}

    def clear(self):
        with self._mutex:
            self._cache = {}

    def load(self, fname):
        logger = logging.getLogger(__name__ + "." + self.load.__name__)

        if fname not in self._cache:
            with self._mutex:
                self._cache[fname] = {}
        if self._load_key not in self._cache[fname]:
            logger.debug(
                f"No dataset found for file '{fname}' with key '{self._load_key}', reading into cache...")
            with self._mutex:
                ds = yt.load(fname)
                ds.parameters["format_revision"] = 2

                self._cache[fname][self._load_key] = ds

        return self._cache[fname][self._load_key]

    def all_data(self, fname):
        logger = logging.getLogger(__name__ + "." + self.all_data.__name__)

        if fname not in self._cache:
            with self._mutex:
                self._cache[fname] = {}

        if self._all_data_key not in self._cache[fname]:
            logger.debug(
                f"All data missing in cache for data set '{fname}', reading...")

            data_set = self.load(fname)
            with self._mutex:
                self._cache[fname][self._all_data_key] = data_set.all_data()

        return self._cache[fname][self._all_data_key]

    def sphere(self, fname, centre, radius):
        logger = logging.getLogger(__name__ + "." + self.sphere.__name__)

        if type(centre) is unyt.unyt_array:
            centre = tuple(centre.v)
        if type(radius) is unyt.unyt_quantity:
            radius = float(radius.v)

        if fname not in self._cache:
            with self._mutex:
                self._cache[fname] = {}

        if self._sphere_key not in self._cache[fname]:
            with self._mutex:
                self._cache[fname][self._sphere_key] = {}

        if radius not in self._cache[fname][self._sphere_key]:
            with self._mutex:
                self._cache[fname][self._sphere_key][radius] = {}

        if centre not in self._cache[fname][self._sphere_key][radius]:
            logger.debug(
                f"Sphere data missing for dataset '{fname}' @ ({centre[0]}, {centre[1]}, {centre[2]}) for radius {radius}, calculating...")
            ds = self.load(fname)
            sp = ds.sphere(centre, radius)
            with self._mutex:
                self._cache[fname][self._sphere_key][radius][centre] = sp

        return self._cache[fname][self._sphere_key][radius][centre]

    def save(self):
        logger = logging.getLogger(__name__ + "." + self.save.__name__)
        logger.debug(f"Saving cache to '{self._save_path}'")

        with self._mutex:
            # with open(self._save_path, "wb") as f:
                # TODO: make this work??
                # np.save(f, self._cache, allow_pickle=False)
            return

