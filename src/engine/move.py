from .json_serialization import JSONSerializableValues
from src.utility import dict_copy


class Move(JSONSerializableValues):
    """A move that can be used by a Fighter.

    Args:
        values (Dict[str, Any]): A dictionary of values.
            Common values include:
            'name': 'Name of move',
            'movetypes': ([MoveType('Physical')],),
            # MoveType requirements (see skillRequired for explanation)
            'description': 'Description of the move',
            'skillRequired': ([SKOneSkill(1)],
                              [SKFirstSkill(2), SKSecondSkill(3)]),
                Skills inside lists are combinations.
                In this example you can use the attack if you have
                SKOneSkill with level 1, or you have both SKFirstSkill
                and SKSecondSkill with levels 2 and 3 respectively.
            'itemRequired': ([('Object1', 1)],),
                Behaves like skillRequired, except each object is a tuple
                containing the item's name and the amount of the item
                that will be consumed.
            'moveMessage': 'Attack Message',

            'hpValue': Bound(-10, -15),
            'stValue': Bound(-10),
            'mpValue': Bound(5),
            # Stat cost required to use the move
            'hpCost': Bound(-10, -20),
            'stCost': Bound(-10, -20),
            'mpCost': Bound(-20, -30),
            # Optional message to customize insufficient stats
            'insufficientStatMessage': '{self} tried using {move} '
                                       'but the {ext_full} cost was {-cost}.',

            'speed': 40,  # Chance of attack being uncounterable
            'fastMessage': 'Uncounterable Attack',

            'blockChance': 70,  # Chance of successfully blocking
            'blockHPValue': Bound(-6, -15),
            'blockSTValue': Bound(-6, -15),
            'blockMPValue': Bound(-6, -15),
            'blockFailHPValue': Bound(-10, -25),
            'blockFailSTValue': Bound(-10, -25),
            'blockFailMPValue': Bound(-10, -25),
            'blockMessage': 'Blocked Attack',
            'blockFailMessage': 'Attack after failing an block',

            'evadeChance': 70,  # Chance of successfully evading
            'evadeHPValue': Bound(0),
            'evadeSTValue': Bound(0),
            'evadeMPValue': Bound(0),
            'evadeFailHPValue': Bound(-10, -25),
            'evadeFailSTValue': Bound(-10, -25),
            'evadeFailMPValue': Bound(-10, -25),
            'evadeMessage': 'Evaded Attack',
            'evadeFailMessage': 'Attack after failing an evade',

            'criticalChance': 10,
            'criticalHPValue': Bound(-30, -75),
            'criticalSTValue': Bound(-30, -75),
            'criticalMPValue': Bound(-30, -75),
            'blockFailCriticalHPValue': Bound(-30, -75),
            'blockFailCriticalSTValue': Bound(-30, -75),
            'blockFailCriticalMPValue': Bound(-30, -75),
            'evadeFailCriticalHPValue': Bound(-30, -75),
            'evadeFailCriticalSTValue': Bound(-30, -75),
            'evadeFailCriticalMPValue': Bound(-30, -75),
            'criticalMessage': 'Critical Attack',
            'fastCriticalMessage': 'Uncounterable Critical Attack',
            'blockFailCriticalMessage': 'Critical after failing a block',
            'evadeFailCriticalMessage': 'Critical after failing an evade',

            'failureChance': 20,
            'failureHPValue': Bound(-5, -10),
            'failureSTValue': Bound(-5, -10),
            'failureMPValue': Bound(-5, -10),
            'failureMessage': 'Failed attack',

    """

    def __init__(self, values):
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

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __iter__(self):
        return iter(self.values)

    def __contains__(self, key):
        return key in self.values

    def __format__(self, format):
        return self['name']

    def average_values(self, fighter, key_format):
        """Calculate the average move values with stats.

        If the value is a Bound, will use average of the Bound.

        Variables provided for key_format:
            stat - The current stat being iterated through

        Example:
            moveObj.average_values('{stat}Value')

        """
        total = []
        # BUG: Does not use a Fighter's stats to allow custom stats
        # to be recognized
        for stat in fighter.stats:
            key = key_format.format(stat=stat)
            value = self.values.get(key)
            if value is not None:
                if hasattr(value, 'average'):
                    total.append(value.average())
                else:
                    total.append(value)
        if (len_total := len(total)) == 0:
            # Return 0 for no values found
            return 0
        return sum(total) / len_total

    def copy(self):
        return self.__class__(dict_copy(self.values))

    @staticmethod
    def parse_unsatisfactories(unsatisfactories):
        """Generate a string explaining why a move could not be used.

        Args:
            unsatisfactories (Iterable[BoolDetailed]): This should come
                from the output of src.engine.dueturn.Fighter.find_move
                where the argument showUnsatisfactories = True.

        Returns:
            str: The explanation.

        """
        reasonMessageList = []
        for reason in unsatisfactories:
            if reason.name == 'MISSINGMOVETYPE':
                for moveType in reason.other[0]:
                    reasonMessageList.append(
                        f'\n"{moveType.name}" Move Type required')
            elif reason.name == 'MISSINGSKILL':
                for skill in reason.other[0]:
                    name = skill.name
                    level = skill.level

                    reasonMessageList.append(
                        f'\nLevel {level} "{name}" Skill required')
            elif reason.name == 'MISSINGITEM':
                for item_req in reason.other[0]:
                    name = item_req['name']
                    count = item_req['count'] if 'count' in item_req else None

                    if count is None:
                        count_msg = 'Item'
                    else:
                        plur = 's' if count != 1 else ''
                        count_msg = f'{count:,} of item{plur}'

                    reasonMessageList.append(
                        f'\n{count_msg} "{name}" required')

        reasonMessageList = ', '.join(reasonMessageList)

        return reasonMessageList

    def search_items(self, sub) -> dict:
        """Search through the move's items and return a dictionary of all
        key-value pairs if the key is a superset of sub."""
        return {k: v for k, v in self if sub in k}

    def search_keys(self, sub) -> list:
        """Search through the move's keys and return a list of all keys
        that is a superset of sub."""
        return [k for k in self if sub in k]

    def search_values(self, sub) -> list:
        """Search through the move's items and return a list of all values
        if the corresponding key is a superset of sub."""
        return [v for k, v in self if sub in k]
