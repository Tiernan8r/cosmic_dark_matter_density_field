import logging
import os
import threading

import yt
import yt.extensions.legacy
from src.cache.faux_rockstar import FauxRockstar
from src.util import units as u

_existing_instance = None


def new():
    global _existing_instance
    if _existing_instance is None:
        _existing_instance = CachedDataSet()

    return _existing_instance


class CachedDataSet:

    _load_key = "dataset"
    _all_data_key = "all_data"

    def __init__(self):
        self._mutex = threading.Lock()
        with self._mutex:
            self._cache = {}

    def clear(self):
        with self._mutex:
            self._cache = {}

    def load(self, fname):
        logger = logging.getLogger(__name__ + "." + self.load.__name__)

        dirname = os.path.dirname(fname)
        basename = os.path.basename(fname)
        _, ext = os.path.splitext(basename)

        if fname not in self._cache:
            with self._mutex:
                self._cache[fname] = {}

        if self._load_key not in self._cache[fname]:
            logger.debug(
                f"No dataset found for file '{fname}' with key '{self._load_key}', reading into cache...")  # noqa: E501

            with self._mutex:
                args = []
                kwargs = {}

                if "snapdir" in dirname:
                    kwargs = {
                        "unit_base": u.unit_base()
                    }

                ds = yt.load(fname, *args, **kwargs)

                if "rockstar" in dirname:
                    ds.parameters["format_revision"] = 2
                    ds = FauxRockstar(ds, fname)

                self._cache[fname][self._load_key] = ds

        return self._cache[fname][self._load_key]

    def all_data(self, fname):
        logger = logging.getLogger(__name__ + "." + self.all_data.__name__)

        if fname not in self._cache:
            with self._mutex:
                self._cache[fname] = {}

        if self._all_data_key not in self._cache[fname]:
            logger.debug(
                f"All data missing in cache for data set '{fname}', reading...")  # noqa: E501

            data_set = self.load(fname)
            with self._mutex:
                self._cache[fname][self._all_data_key] = data_set.all_data()

        return self._cache[fname][self._all_data_key]

    def sphere(self, fname, centre, radius):
        ds = self.load(fname)
        return ds.sphere(centre, radius)