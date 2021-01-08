"""Dueturn Battle Engine

Python Version Required: Python 3.8

Footnote 1: Update these class attributes every time a new counter
is introduced (same for new stats)

Footnote 2: `self_applied` is not a used variable in status effect application
since self-applied moves are not properly designed.

Footnote 3: Preferably, these print statements should be placed outside
of the move() code.
"""
# pylint: disable=bad-whitespace
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=undefined-variable

# Typing Classes
# Any: Use when a type is unknown or too dynamic
#     unknown: Any
# Callable: Use for callable objects, specifying the input types.
#     sum: Callable[Iterable]
# Dict: Use for a dictionary, specifying the types of the keys and values
#     dictionary: Dict[int, str]
# Generator: Use when a function is a generator.
#     def one_range(x: int) -> Generator[int]
# Iterable: Use for objects that are iterable.
# Iterator: Use for iterators.
# List: Use for a list, specifying the types of each value.
#     nums: List[int]
# Literal: Use when something has to equal a certain object(s).
#     file_mode: Literal['r', 'rb', 'w', 'wb']
# Mapping: Use for dictionary-like objects.
#     char_to_num: Mapping[str, int]
# Optional: Use when a value could be None.
#     def foo(optional: Optional[int] = 0):
# Sequence: Use for objects that support the sequence protocol.
# Set: Use for sets.
#     Note: FrozenSet has a different type.
# Tuple: Use for tuples, specifying the type of each element.
#     name_and_coords: Tuple[str, int, int]
# Union: Use when something could be one of a few types
#     int_or_str: Union[int, str]

from . import util
from . import json_handler
from .battle_env import BattleEnvironment
from .booldetailed import BoolDetailed
from .bound import Bound
from .data import fighter_stats
from .fighter import Fighter
from .item import Item
from .move import Move
from .movetype import MoveType
from .skill import Skill
from .stat import Stat, StatInfo
from .status_effect import StatusEffect
from src import logs
from src.textio import (
    ColoramaCodes, cr, format_color, input_color, print_color,
    input_boolean
)

__copyright__ = """
    Dueturn - A text-based two-player battle engine.
    Copyright (C) 2020  thegamecracks

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__all__ = [
    util, fighter_stats, json_handler,
    BattleEnvironment, BoolDetailed, Bound, Fighter, Item, Move,
    MoveType, Skill, Stat, StatInfo, StatusEffect,
    ColoramaCodes, cr, format_color, input_color, print_color,
    input_boolean
]

# Set up logger
logger = logs.get_logger()
logger.info('Starting Dueturn engine')

moveTemplate = [
    Move({
        'name': '',
        'movetypes': ([MoveType('Physical')],),
        'description': '',
        'skillRequired': ([],),
        'itemRequired': ([
            {
                'name': '',
                'count': 0
            },
            ],),
        'moveMessage': """\
{sender} attacks {target} for {-hpValue} damage, costed {-stCost}""",

        'hpValue': Bound(-0, -0),
        'stValue': Bound(-0, -0),
        'mpValue': Bound(-0, -0),
        'hpCost': Bound(-0, -0),
        'stCost': Bound(-0, -0),
        'mpCost': Bound(-0, -0),

        'effects': [
            StatusEffect({
                'name': '',
                'description': '',

                'target': 'target',
                'chances': ((0, 'uncountered'),),
                'duration': 0,

                'receiveMessage': '{self}',
                'applyMessage': '{self} {-hpValue} {hp.ext_full}',
                'wearoffMessage': '{self}',

                'hpValue': Bound(-0, -0),
                'stValue': Bound(-0, -0),
                'mpValue': Bound(-0, -0),
                'noMove': '{self} cannot move',
                'noCounter': '{self} cannot counter',
            }),
        ],

        'speed': 0,
        'fastMessage': """\
{move:hp neg}""",

        'blockChance': 0,
        'blockHPValue': Bound(-0, -0),
        'blockSTValue': Bound(-0, -0),
        'blockMPValue': Bound(-0, -0),
        'blockFailHPValue': Bound(-0, -0),
        'blockFailSTValue': Bound(-0, -0),
        'blockFailMPValue': Bound(-0, -0),
        'blockMessage': """\
{-hpValue}""",
        'blockFailMessage': """\
{-hpValue}""",

        'evadeChance': 0,
        'evadeHPValue': 0,
        'evadeSTValue': 0,
        'evadeMPValue': 0,
        'evadeFailHPValue': Bound(-0, -0),
        'evadeFailSTValue': Bound(-0, -0),
        'evadeFailMPValue': Bound(-0, -0),
        'evadeMessage': """\
{-hpValue}""",
        'evadeFailMessage': """\
{-hpValue}""",

        'criticalChance': 0,
        'criticalHPValue': Bound(-0, -0),
        'criticalSTValue': Bound(-0, -0),
        'criticalMPValue': Bound(-0, -0),
        'blockFailCriticalHPValue': Bound(-0, -0),
        'blockFailCriticalSTValue': Bound(-0, -0),
        'blockFailCriticalMPValue': Bound(-0, -0),
        'evadeFailCriticalHPValue': Bound(-0, -0),
        'evadeFailCriticalSTValue': Bound(-0, -0),
        'evadeFailCriticalMPValue': Bound(-0, -0),
        'criticalMessage': """\
{-hpValue}""",
        'fastCriticalMessage': """\
{-hpValue}""",
        'blockFailCriticalMessage': """\
{-hpValue}""",
        'evadeFailCriticalMessage': """\
{-hpValue}""",

        'failureChance': 0,
        'failureHPValue': Bound(-0, -0),
        'failureSTValue': Bound(-0, -0),
        'failureMPValue': Bound(-0, -0),
        'failureMessage': """\
{-hpValue}""",
        }
    ),
]
noneMove = Move({
    'name': 'None',
    'description': 'Do nothing.'
})
