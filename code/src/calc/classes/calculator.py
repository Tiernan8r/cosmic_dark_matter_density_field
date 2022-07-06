import abc

from src.cache import caching, dataset
from src.init import conf


class Calculator(abc.ABC):

    def __init__(self,
                 config: conf.Configuration,
                 dataset_cache: dataset.CachedDataSet,
                 cache: caching.Cache,
                 sim_name: str = None):
        self._config = config
        self._dataset_cache = dataset_cache
        self._cache = cache
        self._sim_name = sim_name

    def set_sim_name(self, sim_name):
        self._sim_name = sim_name

    def get_sim_name(self):
        return self._sim_name
