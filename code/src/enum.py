import enum


class DataType(enum.Enum):

    GROUP = enum.auto()
    ROCKSTAR = enum.auto()
    SNAPSHOT = enum.auto()

    def _index(self):
        if self is DataType.GROUP:
            return "Group", "GroupMass"
        elif self is DataType.ROCKSTAR:
            return "halos", "particle_mass"
        elif self is DataType.SNAPSHOT:
            # or ("PartType1", "Masses") or ("nbody", "Masses") ??
            return "all", "Masses"

        return "", ""

    @property
    def index(self):
        return self._index()
