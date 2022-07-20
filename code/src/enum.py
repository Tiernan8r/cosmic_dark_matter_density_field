import enum
import re

from src.const.constants import (DATA, ROCKSTAR, groups_regex, rockstar_regex,
                                 rockstar_root_regex, snapshots_regex)


class DataType(enum.Enum):

    GROUP = "groups"
    ROCKSTAR = "rockstar"
    SNAPSHOT = "snapshots"

    def _index(self):
        if self is DataType.GROUP:
            return "Group", "GroupMass"
        elif self is DataType.ROCKSTAR:
            return "halos", "particle_mass"
        elif self is DataType.SNAPSHOT:
            # or ("PartType1", "Masses") or ("nbody", "Masses") ??
            return "all", "Masses"

        return "", ""

    def coord_index_x(self):
        if self is DataType.GROUP:
            return "Group", "GroupPos_0"
        elif self is DataType.ROCKSTAR:
            return "halos", "particle_position_x"
        elif self is DataType.SNAPSHOT:
            return "all", "Coordinates"

        return "", ""

    def coord_index_y(self):
        if self is DataType.GROUP:
            return "Group", "GroupPos_1"
        elif self is DataType.ROCKSTAR:
            return "halos", "particle_position_y"
        elif self is DataType.SNAPSHOT:
            return "all", "Coordinates"

        return "", ""

    def coord_index_z(self):
        if self is DataType.GROUP:
            return "Group", "GroupPos_2"
        elif self is DataType.ROCKSTAR:
            return "halos", "particle_position_z"
        elif self is DataType.SNAPSHOT:
            return "all", "Coordinates"

        return "", ""

    def virial_radii(self):
        if self is DataType.ROCKSTAR:
            return "halos", "virial_radius"

        return "", ""

    @property
    def index(self):
        return self._index()

    def get_regex(self) -> re.Pattern:
        if self is DataType.GROUP:
            return groups_regex
        elif self is DataType.ROCKSTAR:
            return rockstar_regex
        elif self is DataType.SNAPSHOT:
            return snapshots_regex

        return None

    def get_root_regex(self) -> re.Pattern:
        if self is DataType.ROCKSTAR:
            return rockstar_root_regex

        return None

    def data(self) -> str:
        if self is DataType.ROCKSTAR:
            return ROCKSTAR

        return DATA
