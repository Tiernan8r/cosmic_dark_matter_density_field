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
        ds = self.load(fname)
        return ds.sphere(centre, radius)
