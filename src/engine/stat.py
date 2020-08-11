from . import util
from .bound import Bound
from .json_serialization import JSONSerializableBasic
from src.textio import ColoramaCodes
from src.utility import assert_type


class StatInfo(JSONSerializableBasic):
    """Information about a stat.

    Stats have four forms:
        int_short
        int_full
        ext_short
        ext_full
    The "int" prefix means internal, and "ext" means external.
    The external forms are used for printing. These can be freely changed
    to customize appearance.
    The internal forms are used in code. int_short is used in variables,
    and int_full is used in constants.

    Args:
        int_short (str): The internal shortened name.
        int_full (str): The internal full name.
        ext_short (str): The external short name.
        ext_full (str): The external full name.
        color_fore (str): A foreground color attribute name from ColoramaCodes.
            Ex. 'FLyell' -> ColoramaCodes.FLyell

    """

    __slots__ = [
        'int_short', 'int_full', 'ext_short', 'ext_full', '_color_fore'
    ]

    def __init__(self, int_short, int_full, ext_short, ext_full,
                 color_fore):
        self.int_short = int_short
        self.int_full = int_full
        self.ext_short = ext_short
        self.ext_full = ext_full
        self._color_fore = color_fore

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.int_short == other.int_short
                and self.int_full == other.int_full
                and self.ext_short == other.ext_short
                and self.ext_full == other.ext_full
                and self._color_fore == other._color_fore
            )
        return NotImplemented

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                [
                    repr(x) for x in (
                       self.int_short,
                       self.int_full,
                       self.ext_short,
                       self.ext_full,
                       self._color_fore
                    )
                ]
            )
        )

    @property
    def color_fore(self):
        """Automatically format color_fore with ColoramaCodes."""
        return getattr(ColoramaCodes, self._color_fore)

    @color_fore.setter
    def color_fore(self, value):
        self._color_fore = value

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {
            '__type__': self.__class__.__name__,
            'int_short': self.int_short,
            'int_full': self.int_full,
            'ext_short': self.ext_short,
            'ext_full': self.ext_full,
            'color_fore': self._color_fore
        }

        return literal

    def to_stat(self, value, bound, rate):
        return Stat.from_stat_info(self, value, bound, rate)


class Stat(JSONSerializableBasic):
    """A stat class containing a value, its bounds, a rate of change,
    and information about itself.

    Args:
        int_short (str): The internal shortened name.
        int_full (str): The internal full name.
        ext_short (str): The external short name.
        ext_full (str): The external full name.
        color_fore (str): The foreground color of the stat
            selected from ColoramaCodes.
            Ex. ColoramaCodes.FLyell
        value (int): The value of the stat.
        bound (.bound.Bound): The limits of the value.
        rate (int): The value's rate of change. Apply onto stat
            using the update() method.

    """

    __slots__ = [
        'int_short', 'int_full', 'ext_short', 'ext_full', '_color_fore',
        '_value', 'bound', 'rate'
    ]

    def __init__(self, int_short, int_full, ext_short, ext_full,
                 color_fore, value, bound, rate):
        self.int_short = int_short
        self.int_full = int_full
        self.ext_short = ext_short
        self.ext_full = ext_full
        self._color_fore = color_fore

        self._value = value
        self.bound = assert_type(bound, Bound)
        self.rate = rate

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                [
                    repr(x) for x in (
                        self.int_short,
                        self.int_full,
                        self.ext_short,
                        self.ext_full,
                        self._color_fore,
                        self._value,
                        self.bound,
                        self.rate
                    )
                ]
            )
        )

    @property
    def color_fore(self):
        """Automatically format color_fore with ColoramaCodes."""
        return getattr(ColoramaCodes, self._color_fore)

    @color_fore.setter
    def color_fore(self, value):
        self._color_fore = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.bound.clamp(value)

    def copy(self, new_value=None, new_bound=None, new_rate=None):
        """Return a new copy of this object and optionally change
        the stat's value, bound, and rate."""
        value = new_value if new_value is not None else self._value
        bound = new_bound if new_bound is not None else self.bound.copy()
        rate = new_rate if new_rate is not None else self.rate
        return self.__class__(
            self.int_short,
            self.int_full,
            self.ext_short,
            self.ext_full,
            self._color_fore,
            value,
            bound,
            rate
        )

    @classmethod
    def from_stat_info(cls, stat_info, value, bound, rate):
        return cls(
            stat_info.int_short,
            stat_info.int_full,
            stat_info.ext_short,
            stat_info.ext_full,
            stat_info._color_fore,
            value, bound, rate
        )

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {
            '__type__': self.__class__.__name__,
            'int_short': self.int_short,
            'int_full': self.int_full,
            'ext_short': self.ext_short,
            'ext_full': self.ext_full,
            'color_fore': self._color_fore,
            'value': self._value,
            'bound': self.bound,
            'rate': self.rate
        }

        return literal

    def to_stat_info(self):
        """Create a StatInfo object from self."""
        return StatInfo(
            self.int_short,
            self.int_full,
            self.ext_short,
            self.ext_full,
            self._color_fore
        )

    def update(self):
        self.value += self.rate
