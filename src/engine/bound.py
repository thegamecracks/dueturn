import random

from .json_serialization import JSONSerializableBasic


class Bound(JSONSerializableBasic):
    """A bound that is used for generating random numbers.

    Note: The way this class was done, using `randNum` as a way
        of sharing numbers, is not a recommended idea, since if
        there were two Fighters using the same Bound object and
        concurrently interacted with this object, the shared values
        can conflict. It is recommended this class be revamped to
        no longer store values, and have value sharing be done by
        the Fighter itself.

    Using int() will return its previously generated randNum.
    Using str() will generate a new randNum and return the integer as a string.
    The generator will always return a float number.
    If one of the bounds is of type float, a uniform number will be generated:
        Bound(1).random()      --> 1.0
        Bound(0, 1).random()   --> 0.0 or 1.0
        Bound(0, 1.0).random() ~~> 0.18550168219619667
    str(Bound())       --> Generate random float as a string
    int(str(Bound()))  --> Generate random truncated float
    float(Bound())      --> Return last generated float
    str(float(Bound())) --> Return last generated float as a string

    Args:
        lower (Union[int, float]): The lower bound.
        upper (Optional[Union[int, float]]): The upper bound.
            If None, will be set to the lower bound.

    """

    __slots__ = ['lower', 'upper']

    def __init__(self, lower, upper=None):
        if upper is None:
            upper = lower
        else:
            # Sort lower and upper so lower < upper
            lower, upper = (lower, upper) if lower < upper else (upper, lower)

        self.lower = lower
        self.upper = upper

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.lower == other.lower
                and self.upper == other.upper
            )
        return NotImplemented

    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self.lower,
            self.upper
        )

    def random(self):
        """Pick a number between its own endpoints (inclusive).

        Returns:
            int: A random integer; both endpoints are integers.
            float: A random uniform number; one or both endpoints are floats.

        """
        use_uniform = (isinstance(self.lower, float)
                       or isinstance(self.upper, float))

        if use_uniform:
            return random.uniform(self.lower, self.upper)
        return float(random.randint(self.lower, self.upper))

    def average(self) -> float:
        """Return the mean average between the two endpoints.

        Returns:
            float: The average between self.lower and self.upper.

        """
        return (self.lower + self.upper) / 2

    @staticmethod
    def call_random(obj):
        """Call the random() method on an object if available."""
        if hasattr(obj, 'random'):
            return obj.random()
        return obj

    def clamp(self, value):
        """Clamps a value to between the lower and upper bounds."""
        return max(self.lower, min(value, self.upper))

    def copy(self):
        """Return a new instance with the same lower and upper bounds."""
        return self.__class__(self.lower, self.upper)

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {
            '__type__': self.__class__.__name__,
            'lower': self.lower,
            'upper': self.upper
        }

        return literal
