import abc

from src import data, enum
from src.const.constants import DEFAULT_SIMNAME


class Interface(data.Data, abc.ABC):

    def __init__(self, d: data.Data, type: enum.DataType = enum.DataType.ROCKSTAR, sim_name: str = DEFAULT_SIMNAME):
        self._type = type
        self._sim_name = sim_name
        super().__init__(d.config, d.dataset_cache, d.cache)

    @property
    def type(self) -> enum.DataType:
        return self._type

    @type.setter
    def type(self, t):
        self._type = t

    @property
    def sim_name(self):
        return self._sim_name

    @sim_name.setter
    def sim_name(self, name):
        self._sim_name = name
