import types
from typing import Tuple

from src.cache import caching, dataset


class Data:

    def __init__(self,
                 config: types.SimpleNamespace,
                 dataset_cache: dataset.CachedDataSet,
                 cache: caching.Cache):
        self._config = config
        self._dataset_cache = dataset_cache
        self._cache = cache

    @property
    def config(self):
        return self._config

    @property
    def dataset_cache(self):
        return self._dataset_cache

    @property
    def cache(self):
        return self._cache
