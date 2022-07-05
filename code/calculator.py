import abc

import configuration
import dataset_cacher
import caching


class Calculator(abc.ABC):

    def __init__(self, config: configuration.Configuration, dataset_cache: dataset_cacher.CachedDataSet):
        self._config = config
        self._dataset_cache = dataset_cache


class CachedCalculator(Calculator, abc.ABC):

    def __init__(self,
                 config: configuration.Configuration,
                 dataset_cache: dataset_cacher.CachedDataSet,
                 cache: caching.Cache,
                 sim_name: str = None):
        super().__init__(config, dataset_cache)
        self._cache = cache
        self._sim_name = sim_name

    def set_sim_name(self, sim_name):
        self._sim_name = sim_name

    def get_sim_name(self):
        return self._sim_name
