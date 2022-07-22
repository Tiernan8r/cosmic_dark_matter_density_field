import logging
import os
import pickle
from typing import Dict, Sequence

from src.const.constants import sim_regex


class Cache:

    def __init__(self, caches_dir: str = "../data/"):
        self._dir = caches_dir
        self._cache: Dict[tuple, CacheEntry] = {}

    def reset(self):
        logger = logging.getLogger(__name__ + "." + self.reset.__name__)
        logger.debug("Resetting cache...")

        self._cache = {}

    def _parse_keys(self, keys: Sequence) -> tuple:
        if not isinstance(keys, Sequence):
            return keys

        key_copy = list(keys)

        for i in range(len(key_copy)):
            key = str(key_copy[i])

            # Simplify the path to data files to just the data set type
            m = sim_regex.match(key)
            if m:
                key = m.group(1)
            key_copy[i] = key

        return tuple(key_copy)

    def __getitem__(self, keys: tuple):
        keys = self._parse_keys(keys)

        if keys not in self._cache:
            self._cache[keys] = CacheEntry(self._dir, keys)

        return self._cache[keys]

    def __setitem__(self, keys: str, val):
        keys = self._parse_keys(keys)

        cache_entry = self[keys]
        cache_entry.val = val

    def __contains__(self, keys: str):
        keys = self._parse_keys(keys)

        return keys in self._cache


class CacheEntry:

    def __init__(self, dir: str, keys: tuple):
        self._dir = dir
        self._keys = keys
        self._path, self._fname = self._compile_path()
        self._cached_val = None

    def _compile_path(self):
        nkeys = len(self._keys)

        fname = ""
        for i in range(nkeys):
            fname += str(self._keys[i])
            if i < nkeys - 1:
                fname += "/"

        fname += ".pickle"

        full_path = os.path.join(self._dir, fname)

        return os.path.split(full_path)

    def _load(self):
        if self._cached_val is not None:
            return self._cached_val

        logger = logging.getLogger(
            __name__ + "." +
            self.__class__.__name__ + "." +
            self._load.__name__)

        pth = os.path.join(self._path, self._fname)
        if os.path.exists(pth):
            logger.debug(f"Opening existing cache at '{pth}'")

            with open(pth, "rb") as f:
                self._cached_val = pickle.load(f)
        else:
            logger.debug(
                f"Cache doesn't exist for '{pth}'!")

        return self._cached_val

    def _save(self, val):
        self._cached_val = val
        logger = logging.getLogger(
            __name__ + "." +
            self.__class__.__name__ + "." +
            self._save.__name__)

        pth = os.path.join(self._path, self._fname)
        logger.debug(f"Saving cache to '{pth}'")

        try:
            if not os.path.exists(self._path):
                os.makedirs(self._path)
        except FileExistsError as fee:
            logger.error(fee)

        with open(pth, "wb") as f:
            pickle.dump(val, f)

    @property
    def val(self):
        return self._load()

    @val.setter
    def val(self, v):
        self._save(v)
