import types
from typing import Tuple

from src.cache import caching, dataset


class Data:

    def __init__(self,
                 config: types.SimpleNamespace,
                 dataset_cache: dataset.CachedDataSet,
                 cache: caching.Cache,
                 sim_name: str = None):
        self._config = config
        self._dataset_cache = dataset_cache
        self._cache = cache
        self._sim_name = sim_name

    def compile(self) -> Tuple[
            types.SimpleNamespace,
            dataset.CachedDataSet,
            caching.Cache, str]:
        return self._config, self._dataset_cache, self._cache, self._sim_name

    @property
    def sim_name(self):
        return self._sim_name

    @sim_name.setter
    def sim_name(self, name):
        self._sim_name = name

    @property
    def config(self):
        return self._config

    @property
    def dataset_cache(self):
        return self._dataset_cache

    @property
    def cache(self):
        return self._cache
