from .util import *
from .json_serialization import JSONSerializableValues


class Move(JSONSerializableValues):
    """A move that can be used by a Fighter.

    Args:
        values (Dict[str, Any]): A dictionary of values.
            Common values include:
            'name': 'Name of move',
            'moveTypes': ([MoveType('Physical')],),
            # MoveType requirements (see skillRequired for explanation)
            'description': 'Description of the move',
            'skillRequired': ([SKOneSkill(1)],
                              [SKFirstSkill(2), SKSecondSkill(3)]),
                Skills inside lists are combinations.
                In this example you can use the attack if you have
                SKOneSkill with level 1, or you have both
                SKFirstSkill and SKSecondSkill with levels 2 and 3 respectively.
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
        format = format.split()
        message = []
        if len(format) == 0:
            return self['name']
        elif format[0] == 'hp':
            message.append(str(num(float(self['hpValue']))))
        elif format[0] == 'st':
            message.append(str(num(float(self['stValue']))))
        elif format[0] == 'mp':
            message.append(str(num(float(self['mpValue']))))
        elif format[0] == 'hpF':
            message.append(str(num(float(self['failureHPValue']))))
        elif format[0] == 'stF':
            message.append(str(num(float(self['failureSTValue']))))
        elif format[0] == 'mpF':
            message.append(str(num(float(self['failureMPValue']))))
        elif format[0] == 'hpCrit':
            message.append(str(num(float(self['criticalHPValue']))))
        elif format[0] == 'stCrit':
            message.append(str(num(float(self['criticalSTValue']))))
        elif format[0] == 'mpCrit':
            message.append(str(num(float(self['criticalMPValue']))))
        elif format[0] == 'hpC':
            message.append(str(num(float(self['hpCost']))))
        elif format[0] == 'stC':
            message.append(str(num(float(self['stCost']))))
        elif format[0] == 'mpC':
            message.append(str(num(float(self['mpCost']))))
        elif format[0] == 'hpBlock':
            message.append(str(num(float(self['blockHPValue']))))
        elif format[0] == 'stBlock':
            message.append(str(num(float(self['blockSTValue']))))
        elif format[0] == 'mpBlock':
            message.append(str(num(float(self['blockMPValue']))))
        elif format[0] == 'hpBlockF':
            message.append(str(num(float(self['blockFailHPValue']))))
        elif format[0] == 'stBlockF':
            message.append(str(num(float(self['blockFailSTValue']))))
        elif format[0] == 'mpBlockF':
            message.append(str(num(float(self['blockFailMPValue']))))
        elif format[0] == 'hpBlockFCrit':
            message.append(str(num(float(self['blockFailCriticalHPValue']))))
        elif format[0] == 'stBlockFCrit':
            message.append(str(num(float(self['blockFailCriticalSTValue']))))
        elif format[0] == 'mpBlockFCrit':
            message.append(str(num(float(self['blockFailCriticalMPValue']))))
        elif format[0] == 'hpEvade':
            message.append(str(num(float(self['evadeHPValue']))))
        elif format[0] == 'stEvade':
            message.append(str(num(float(self['evadeSTValue']))))
        elif format[0] == 'mpEvade':
            message.append(str(num(float(self['evadeMPValue']))))
        elif format[0] == 'hpEvadeF':
            message.append(str(num(float(self['evadeFailHPValue']))))
        elif format[0] == 'stEvadeF':
            message.append(str(num(float(self['evadeFailSTValue']))))
        elif format[0] == 'mpEvadeF':
            message.append(str(num(float(self['evadeFailMPValue']))))
        elif format[0] == 'hpEvadeFCrit':
            message.append(str(num(float(self['evadeFailCriticalHPValue']))))
        elif format[0] == 'stEvadeFCrit':
            message.append(str(num(float(self['evadeFailCriticalSTValue']))))
        elif format[0] == 'mpEvadeFCrit':
            message.append(str(num(float(self['evadeFailCriticalMPValue']))))
        elif format[0] == 'speed':
            message.append(str(num(float(self['speed']))))
        elif format[0] == 'blockChan':
            message.append(str(num(float(self['blockChance']))))
        elif format[0] == 'evadeChan':
            message.append(str(num(float(self['evadeChance']))))
        elif format[0] == 'failChan':
            message.append(str(num(float(self['failureChance']))))
        else:
            raise ValueError(
                'Tried formatting a move with non-existent argument(s) '
                f'{format}'
            )

        message = ''.join(message)
        if format[-1] == 'abs':
            message = str(abs(num(message)))
        elif format[-1] == 'neg':
            message = str(-num(message))
        return message

    def averageValues(self, key_format):
        """Calculate the average move values with stats.

        If the value is a Bound, will use average of the Bound.

        Variables provided for key_format:
            stat - The current stat being iterated through

        Example:
            moveObj.averageValues('{stat}Value')

        """
        total = []
        for stat in Fighter.allStats:
            key = eval("f'''" + key_format + "'''")
            if key in self:
                if isinstance(self[key], Bound):
                    total.append(self[key].average())
                else:
                    total.append(self[key])
        if (len_total := len(total)) == 0:
            # Return 0 for no values found
            return 0
        return sum(total) / len_total

    def fmt(self, format) -> str:
        """A shorter version of the __format__ method.

        Intended for use in moves to shorten messages.

        """
        return self.__format__(format)

    @staticmethod
    def parse_unsatisfactories(unsatisfactories):
        """Generate a string explaining why a move could not be used.

        Args:
            unsatisfactories (Iterable[BoolDetailed]): This should come
                from the output of src.engine.dueturn.Fighter.findMove
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

    def searchItems(self, sub) -> dict:
        """Search through the move's items and return a dictionary of all
        key-value pairs if the key is a superset of sub."""
        return {k: v for k, v in self if sub in k}

    def searchKeys(self, sub) -> list:
        """Search through the move's keys and return a list of all keys
        that is a superset of sub."""
        return [k for k in self if sub in k]

    def searchValues(self, sub) -> list:
        """Search through the move's items and return a list of all values
        if the corresponding key is a superset of sub."""
        return [v for k, v in self if sub in k]
