from .json_serialization import JSONSerializableValues


class StatusEffect(JSONSerializableValues):
    """A status effect that goes into Fighter().status_effects.

    Moves should store this in Move()['status_effects'].

    When a move applies a StatusEffect, it should be copied onto
    the affected Fighter.

    Args:
        values (Dict[str, Any]): A dictionary of values.
            Common values include:
            'name': 'Name of status effect',
            'description': 'Description of the effect',

            'target': 'sender' or 'target',
            'chances': (
                (40,),
                # Applies to any situation only if no other conditions
                # were satisfied and move doesn't fail
                (0, 'failure'),
                # Applies to sender if they fail
                (70, 'fast'),
                # Applies to target on fast attack
                (100, 'critical'),
                # Applies to target on critical regardless of counter
                (40, 'block'),
                # Applies to target if block was attempted
                # Note: any counter name in Fighter.allCounters can be used
                (0, 'blockSuccess'),
                # Applies to target if successful block
                (0, 'blockFailure')
                # Applies to target if block failed
                (50, 'uncountered'),
                # Applies to target if no counters were successful
            ),
            'duration': 5,

            'receiveMessage': '{self} has been affected!',
            'applyMessage': '{self} takes {-hpValue} damage '
                            'but receives {stValue} {st.ext_full}!',
                            # {st.ext_full} is the placeholder for stamina
            'wearoffMessage': "{self}'s effect has worn off.",

            'hpValue': Bound(-1, -3),
            'stValue': Bound(1, 3),
            'mpValue': Bound(1, 3),
            'noMove': '{self} cannot move!',
            'noCounter': '{self} cannot counter!',

    """

    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.values)

    def __str__(self):
        return self['name']

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __iter__(self):
        return iter(self.values)

    def __contains__(self, key):
        return key in self.values

    def copy(self):
        values = self.values.copy()
        for k, v in values.items():
            if hasattr(v, 'copy'):
                values[k] = v.copy()
        return self.__class__(values)
