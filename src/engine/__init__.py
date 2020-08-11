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

import random
import time
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
from src.utility import exception_message, collect_and_log_garbage

__all__ = [
    util, fighter_stats, json_handler,
    BattleEnvironment, BoolDetailed, Bound, Fighter, Item, Move,
    MoveType, Skill, Stat, StatInfo, StatusEffect,
    ColoramaCodes, cr, format_color, input_color, print_color,
    input_boolean
]

# Set up logger
logger = logs.get_logger()
logger.info('Starting dueturn.py')

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


def startup_procedures():
    """Do procedures at the start of main()."""


def main():
    data = {
        'randomize_moves_A': (6, 8),
        'randomize_moves_B': (6, 8),
        # Union[bool, int, Tuple[int, int]] = (6, 8)
        # If 1 or greater, or a tuple of endpoints for random size,
        # pick a random set of moves for each fighter
        # (noneMove is excluded from the count as it will always be added).
        # Examples:
        #     10      # Pick at most 10 usable moves from the move set
        #     (4, 6)  # Pick at most 4-6 usable moves from the move set
        # Disable by removing this key. Setting the key's value to False
        # also works but is not recommended.
        'sort_moves': True,
        # Sort the fighters' move set before
        # starting the battle.
        # Disable by removing this key.
    }

    logger.debug('Reading src/engine/data/moves.json')
    moveList = json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

    try:
        startup_procedures()

        logger.info('Starting game loop')

        while True:
            with BattleEnvironment(
                        random_player_names={
                            'abc', 'def', 'ghi', 'ned', 'led', 'med', 'red',
                            'ked', 'sed', 'ped', 'ben'
                        },
                        gamemode=None, AI=None,  # Prompt for gamemode and AI
                        data=data
                    ) as battle:
                # User Setup
                firstPlayer, secondPlayer, autoplay = \
                    battle.get_players_and_autoplay()

                # Generate Settings
                firstPlayerSettings, secondPlayerSettings = \
                    battle.player_create_default_settings()

                # Add player names
                battle.player_update_names(
                    firstPlayerSettings, secondPlayerSettings,
                    firstPlayer, secondPlayer
                )

                # Create the Fighters
                firstPlayer, secondPlayer = battle.player_create_fighters(
                    firstPlayerSettings, secondPlayerSettings,
                    firstPlayer, secondPlayer
                )

                # Post-fighter creation settings
                def sample_moves(fighter, amount):
                    """Randomize a fighter's moves by removing some from their
                    move set."""
                    if isinstance(amount, tuple):
                        # Range given; pick a random amount
                        # between the range
                        amount = random.randint(*amount)

                    moves = [noneMove]  # Always have noneMove

                    # Filter out only moves that the fighter can use
                    moveListFilter = [
                        m for m in moveList
                        if fighter.available_move(m)
                        and m['name'] != 'None'
                    ]

                    # Sample some of the moves
                    moves += random.sample(
                        moveListFilter,
                        min(len(moveListFilter), amount))

                    # Finalize the moves onto the fighter
                    fighter.moves = moves

                # Randomization of moves
                randomize_moves_A = battle.data.get('randomize_moves_A')
                randomize_moves_B = battle.data.get('randomize_moves_B')
                if randomize_moves_A:
                    sample_moves(firstPlayer, randomize_moves_A)
                if randomize_moves_B:
                    sample_moves(secondPlayer, randomize_moves_B)

                # If enabled, sort moves from each fighter by name
                if 'sort_moves' in battle.data:
                    key = lambda x: x['name']
                    firstPlayer.moves = sorted(
                        firstPlayer.moves, key=key)
                    secondPlayer.moves = sorted(
                        secondPlayer.moves, key=key)

                # Fight
                end_message = battle.begin_battle(
                    firstPlayer, secondPlayer, autoplay=autoplay)
                battle.print_end_message(end_message)

            # Wait for player to start another game
            input()
            print()
    except Exception:
        msg = exception_message(
            header='RUNTIME ERROR', log_handler=logger)
        msg += '\n\nSee the log for more details.'

        # Print message in red
        print_color('{RA}{FLred}', end='')
        print_color(msg, do_not_format=True)
        time.sleep(2)
        input()

        logger.info('Restarting game loop')
    except SystemExit:
        logger.info('SysExit')
    finally:
        collect_and_log_garbage(logger)
        logger.info('Ending game loop')


if __name__ == '__main__':
    while True:
        main()
