import logging
import os
import pickle
from typing import Any, Dict


class Cacher:

    def __init__(self, cache_name: str):
        self._path = cache_name
        self._cache_loaded = False
        self._cache = self.get_cache()

    def get_cache(self) -> Dict[str, Any]:
        logger = logging.getLogger(__name__ + "." + self.get_cache.__name__)

        if not self._cache_loaded:
            logger.debug(
                f"Cache not loaded for '{self._path}', attempting to load...")

            if os.path.exists(self._path):
                with open(self._path, "rb") as f:
                    logger.debug("Found existing cache, reading...")
                    self._cache = pickle.load(f)
            else:
                logger.debug("Found no existing cache, creating empty dict")
                self._cache = {}

            self._cache_loaded = True

        return self._cache

    def save_cache(self):
        logger = logging.getLogger(self.save_cache.__name__)
        with open(self._path, "wb") as f:
            logger.debug(f"Saving cache to '{self._path}'")
            pickle.dump(self._cache, f)

    def __getitem__(self, key: str):
        if key in self._cache:
            return self._cache[key]

    def __setitem__(self, key: str, val):
        self._cache[key] = val

    def __contains__(self, key: str):
        return key in self._cache
