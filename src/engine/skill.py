from .json_serialization import JSONSerializableBasic


class Skill(JSONSerializableBasic):
    """Class for level-based requirements."""

    def __init__(self, name, level):
        self.name = name
        self.level = level

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__,
            self.name,
            self.level
        )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level == other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level != other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level > other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level < other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level >= other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.level <= other.level
        elif isinstance(other, int):
            return self.level == other
        return NotImplemented

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {
            '__type__': self.__class__.__name__,
            'name': self.name,
            'level': self.level
        }

        return literal
