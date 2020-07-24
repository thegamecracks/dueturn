class BoolDetailed:

    def __init__(self, boolean, name, description, *other):
        if not isinstance(boolean, bool):
            raise TypeError(
                f'Expected bool for boolean, received object of type {type(boolean)}')
        self.boolean = boolean
        self.name = name
        self.description = description
        self.other = other

    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(
            self.__class__.__name__, self.boolean,
            repr(self.name), repr(self.description),
            repr(self.other)
            )

    def __str__(self):
        return self.description

    def __bool__(self):
        return self.boolean
