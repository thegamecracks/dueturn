from .json_serialization import JSONSerializableValues


class Item(JSONSerializableValues):
    """An item which can be stacked.

    Common values include:
        'name': 'Name of item',
        'description': 'Description of the item',

        'count': 1,  # Amount of the current item.
        'maxCount': 64,  # Maximum amount that can be stacked

    Args:
        values (dict): A dictionary of values.

    """
    def __init__(self, values: dict):
        self.values = values

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.values == other.values
        return NotImplemented

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.values
        )

    def __str__(self):
        return self['name']

    def __len__(self):
        """Return the amount of the item."""
        return self['count']

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __iter__(self):
        return iter(self.values)

    def __contains__(self, key):
        return key in self.values

    def copy(self):
        return self.__class__(self.values.copy())
