from .json_serialization import JSONSerializableBasic


class MoveType(JSONSerializableBasic):
    """Class for non-level requirements."""

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__,
            self.name
        )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def to_JSON(self):
        literal = {
            '__type__': self.__class__.__name__,
            'name': self.name,
        }

        return literal
