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
        left (Union[int, float]): The left bound.
        right (Optional[Union[int, float]]): The right bound.
            If None, will be set to the left bound.

    """

    __slots__ = ['left', 'right', 'randNum']

    def __init__(self, left, right=None):
        self.left = left
        if right is None:
            self.right = self.left
        else:
            self.right = right
        self.randNum = 0.0

    def __float__(self):
        """Returns self.randNum as a float."""
        return float(self.randNum)

    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self.left,
            self.right
        )

    def random(self):
        """Pick a number between its own endpoints (inclusive).

        Returns:
            int: A random integer; both endpoints are integers.
            float: A random uniform number; one or both endpoints are floats.

        """
        if self.left < self.right:
            if isinstance(self.left, float) or isinstance(self.right, float):
                self.randNum = random.uniform(self.left, self.right)
            else:
                self.randNum = float(random.randint(self.left, self.right))
        else:
            if isinstance(self.left, float) or isinstance(self.right, float):
                self.randNum = random.uniform(self.right, self.left)
            else:
                self.randNum = float(random.randint(self.right, self.left))
        return self.randNum

    def average(self) -> float:
        """Return the mean average between the two endpoints.

        Returns:
            float: The average between self.left and self.right.

        """
        return (self.left + self.right) / 2

    @staticmethod
    def call_random(obj):
        """Call the random() method on an object if available."""
        if hasattr(obj, 'random'):
            return obj.random()
        return obj

    @staticmethod
    def call_average(obj):
        """Call the average() method on an object if available."""
        if hasattr(obj, 'average'):
            return obj.average()
        return obj

    def clamp(self, value):
        """Clamps a value to between the left and right bounds."""
        return max(self.left, min(value, self.right))

    def copy(self):
        """Return a new instance with the same left and right bounds."""
        return self.__class__(self.left, self.right)

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {
            '__type__': self.__class__.__name__,
            'left': self.left,
            'right': self.right
        }

        return literal
