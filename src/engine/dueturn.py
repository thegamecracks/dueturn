"""Dueturn Battle Engine

Python Version Required: Python 3.8.x

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


# Unconditional imports (should always be available)
import cmd          # Player's User Interface
import collections  # Useful classes
import gc           # End-of-game garbage collection
import itertools    # Useful iteration functions
import platform     # OS identification
import pprint       # Pretty-format objects for logging
import random       # Random Number Generator
import sys          # Startup detection, Capturing error tracebacks
import traceback    # Parsing tracebacks
import time         # Time and pausing
from typing import Any, Callable, Dict, Generator, Iterable, Iterator, List, \
     Literal, Mapping, Optional, Sequence, Set, Tuple, Union
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

from src.ai import goapy
from src import logs  # Creating logs
from src.textio import (  # Color I/O
    ColoramaCodes, cr, format_color, input_color, print_color
)


# Specify types
RealNum = Union[int, float]

# Game Settings 1/1
playernamelist = {'abc', 'def', 'ghi', 'ned', 'led', 'med', 'red',
                  'ked', 'sed', 'ped', 'ben'}
# Name list for auto-selecting names

GAME_INPUT_MOVE_EXACT_SEARCH: bool = False              # False
# Disable auto-completing move names.

GAME_AI_ANALYSE_MOVE_RANDOM_TIMES: int = 10             # 10
# The amount of times FighterAIGeneric will randomly sample a move from its
# user's moveset before picking the lowest costing move.

GAME_AUTOPLAY_NORMAL_DELAY: RealNum = 1      # 1
# RealNum: How long to wait when AI is automatically moving
GAME_AUTOPLAY_AI_DELAY: RealNum = 2                     ## 1.5
# How long to pause when two AIs are fighting each other.

GAME_DISPLAY_AUTOCOMPLETE_KEY: str = 'tab'              # 'tab'
# The key to press for auto-completing commands.
GAME_DISPLAY_PRINT_MOVES: bool = False                  # False
# Automatically display moves for the player that is moving.
GAME_DISPLAY_SHOW_STAT_DIFFERENCE: bool = True          # True
# Show difference in stats from previous move
#     instead of just stat regeneration.
GAME_DISPLAY_SPEED: RealNum = 1               # 1
# The speed multiplier for pauses.
GAME_DISPLAY_STAT_GAP: int = 9                          ## 4
# The least amount of characters the fighters should be spaced apart.
GAME_DISPLAY_STATS_COLOR_MODE: Literal[0, 1, 2] = 1     # 1
# The color mode when displaying stats.
# 0 = No colours on stats
# 1 = Colour the stat number
# 2 = Colour the line
GAME_DISPLAY_STATS_SHIFT: int = 8                       ## 4
# The amount of leading spaces when displaying the battle.
GAME_DISPLAY_TAB_LENGTH: int = 4                        # 8 console, 4 Discord
# Length of tabs for when replacing spaces.
GAME_DISPLAY_USE_TABS: bool = False                      # False
# Replace spaces with tabs when printing.
INDENT: str = '\t' if GAME_DISPLAY_USE_TABS \
    else ' ' * GAME_DISPLAY_TAB_LENGTH
# The standard indentation to use for printing.

GAME_SETUP_INPUT_COLOR = '{FLcyan}'
# The color to use when prompting at the start of a game.


# Set up logger
logger = logs.get_logger()
logger.info('Starting game_battleplayervsAI.py')


# Conditional imports
try:
    if platform.system() == 'Windows':
        # For Windows, do this instead of just import readline;
        # it screws with colours on prompting
        import pyreadline as readline
    else:
        import readline
except ModuleNotFoundError:
    readline = None
    if platform.system() == 'Windows':
        logger.info('Missing readline module, auto-completion not available; '
                    'install "pyreadline" module to resolve')
    else:
        logger.info('Missing readline module, auto-completion not available')


# Define main functions
def exception_message(
        exc_type=None, exc_value=None, exc_traceback=None,
        header: str = '', log_handler=None) -> str:
    """Create a message out of the last exception handled by try/except.

    Args:
        header (Optional[str]): The header to place above the message.
        log_handler (Optional): The logger to run the exception() method on.

    Returns:
        str: The string containing the exception message.

    """
    if exc_type is None and exc_value is None and exc_traceback is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
    elif exc_type is None or exc_value is None or exc_traceback is None:
        raise ValueError('An exception type/value/traceback was passed '
                         'but is missing the other values')

    # Header message with padded border
    msg = ''
    if header:
        msg = '{:=^{length}}\n'.format(
            header, length=len(header) * 2 + len(header) % 2)

    if log_handler is not None:
        # Log the exception; doesn't require creating a message
        logger.exception(msg)

    # Create the message to return, containing the traceback and exception
    for frame in traceback.extract_tb(exc_traceback):
        msg += f'Frame {frame.name!r}\n'
        # Show only the file name instead of the full location
        filename = frame.filename[::-1]
        filename = filename[:filename.find('\\') + 1] + '..'
        filename = filename[::-1]

        msg += f'Within file "{filename}"\n'
        msg += f'at line number {frame.lineno}:\n'
        msg += f'   {frame.line}\n'
    msg += f'\n{exc_type.__name__}: {exc_value}'

    return msg


def plural(n, pluralString='s', naturalOnly=False):
    """Return a plural suffix if a number should be read as plural.

    Args:
        n (RealNum): The number to check.
        pluralString (str): The plural suffix to return
            if `n` should be a pluralized quantity.
        naturalOnly (bool): If True, return plural if n != 1.
            Otherwise, return plural if abs(n) != 1.

    Returns:
        str

    """
    if naturalOnly and n == 1:
        return ''
    elif abs(n) == 1:
        return ''
    return pluralString


def pause(sleep=None, printNewline=0):
    """When not given a number, will block current thread with input().
    Otherwise, will use time.sleep() for the specified time.

    Args:
        sleep (Optional[RealNum]): The time to sleep for.
            If None, will call input().
        printNewline (Literal[0, 1, 2]):
            When using time.sleep (sleep is not None),
            if 1, then a newline is printed before calling time.sleep(sleep);
            if 2, then it is printed after the call.
            For no newline, set to 0.

    """
    if sleep is None:
        input()
    else:
        if printNewline == 1:
            print()
        time.sleep(sleep)
        if printNewline == 2:
            print()


class InputAdvanced:
    def __init__(self, input_func=input):
        self.input_func = input_func

    def __call__(
            self, prompt, loopIfEquals: Iterable[str] = {''},
            loopPrompt: Optional = None, breakString: str = 'exit') -> str:
        if loopPrompt is None:
            loopPrompt = prompt

        message = True
        while message != breakString:
            message = self.input_func(prompt)

            if message == breakString:
                return None
            elif message in loopIfEquals:
                print_color(loopPrompt)
                continue

            return message


class PromptBoolean:
    def __init__(self, input_func=input):
        self.input_func = input_func

    def __call__(
            self,
            message: str = 'Type {true} to confirm: ',
            true: Tuple = ('yes', 'y'),
            false: Optional[Tuple] = None,
            repeatMessage: str = 'Could not determine your answer; '
                                 'type again: ',
            showoptioncount: int = 1) -> bool:
        """Invokes input with a variable message, checks if it matches a
        given list of true/false statements, and returns a boolean.

        Ex. >>> PromptBoolean()(message='Type {true} to confirm.',
                    true=('yes','y'),
                    false=('no', 'n'),
                    showoptioncount=2)
        'Type yes/y to confirm.'\

        """
        # Checks that the arguments can be converted into the required types
        try:
            message = str(message)
            true = tuple(true)
            if not isinstance(false, (type(None), tuple)):
                raise TypeError('false must be None or a tuple')
            showoptioncount = int(showoptioncount)
        except TypeError as e:
            raise TypeError('Invalid argument type given') from e
        if showoptioncount > 0:
            # Substitute in true ('yes, y') and false ('no', 'n') if available
            messageTrue = '/'.join(true[:showoptioncount])
            if false is not None:
                messageFalse = '/'.join(false[:showoptioncount])
            else:
                messageFalse = None
            # Format colors and true/false options
            message = format_color(
                message,
                namespace={'true': messageTrue, 'false': messageFalse}
            )
        else:
            message = format_color(message)
        # Run input function
        inputmessage = self.input_func(message).lower()
        # Check input to see if one of the options
        if inputmessage in true:
            return True
        elif false is None:
            return False
        elif inputmessage in false:
            return False
        else:
            while True:
                inputmessage = self.input_func(repeatMessage).lower()
                if inputmessage in true:
                    return True
                elif inputmessage in false:
                    return False


def divi_zero(n, m, raiseIfZero=False, failValue=0, mode=0):
    """Division function with tweakable settings.

    Args:
        n (Real): Dividend
        m (Real): Divisor
        raiseIfZero (bool):
            If True, return failValue if the denominator is 0.
        failValue (Real):
            Value to return if n == 0 or m == 0 and not raiseIfZero.
        mode (Literal[-1, 0, 1]):
            0 for normal division
            -1 for floor division
            1 for ceil division

    """
    if n == 0:
        return failValue
    if m == 0:
        if raiseIfZero:
            raise ZeroDivisionError(f'{n!r} / {m!r}')
        return failValue

    if mode == 0:
        return n / m
    elif mode == -1:
        return n // m
    elif mode == 1:
        return (n + m - 1) // m
    else:
        raise ValueError(f'Invalid mode parameter ({mode})')


# def mean(iterable):
#     return sum(args) / len(args)


def num(x) -> Union[int, float, complex]:
    """Convert an object into either a int, float, or complex in that order."""
    try:
        if hasattr(x, 'is_integer') and not x.is_integer():
            raise ValueError
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            n = complex(x)
            if n.imag == 0:
                return num(n.real)
            return complex(num(n.real), num(n.imag))


def list_copy(items: Iterable) -> List:
    """Run the 'copy' method on each item if available and return a list."""
    return [item.copy() if hasattr(item, 'copy') else item
            for item in items]


# class Singleton(type):
#     _instances = {}
#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


class Dice:
    """An object that can generate random numbers between its given boundaries.

    Cannot specify its own seed for the Random generator (Mersenne Twister).

    """

    def __init__(self, a=1, b=100):
        self.num = None
        self.a = a
        self.b = b

    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self.a,
            self.b)

    def __str__(self):
        return str(self.num)

    def __call__(self, a=None, b=None, gen_float=False):
        a = self.a if a is None else a
        b = self.b if b is None else b
        if gen_float:
            self.num = random.uniform(a, b)
        else:
            self.num = random.randint(a, b)
        return self.num


class Bound:
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

    """

    def __init__(self, left: RealNum,
                 right: Optional[RealNum] = None):
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
            self.right)

    def random(self) -> RealNum:
        """Pick a number between the endpoints (inclusive).

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

    def copy(self):
        """Return a new instance with the same left and right bounds."""
        return self.__class__(self.left, self.right)

    @staticmethod
    def callRandom(obj):
        """Call the random() method on an object if available and return it."""
        if hasattr(obj, 'random'):
            return obj.random()
        return obj

    @staticmethod
    def callAverage(obj):
        """Call the average() method on an object if available."""
        if hasattr(obj, 'average'):
            return obj.average()
        return obj


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


# Initialize Move Types
class MoveType(type):
    """Base class for all move types.
Note: Representation of this cannot work."""

    # def __repr__(self):  # Cannot repr a class
    #     return '{}()'.format(
    #         self.__class__.__name__)


class MTPhysical(MoveType):
    'Move type for physical moves.'
    name = 'Physical'


class MTMagical(MoveType):
    'Move type for magical moves.'
    name = 'Magical'


class MTFootsies(MoveType):
    'Move type for the Footsies Gamemode.'
    name = 'Footsies'


class MTTest(MoveType):
    'Move type for test moves, used in debugging.'
    name = 'Test'


class MTKirby(MoveType):
    'Move type for all kirby moves.'
    name = 'Kirby'


class MTBender(MoveType):
    'Move type for A:TLA Benders.'
    name = 'Bender'


# Initialize Skills
class Skill:
    """Base class for all skill types."""

    def __init__(self, level):
        self.level = level

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.level)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.level == other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.level != other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.level > other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.level < other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.level >= other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.level <= other.level
        elif isinstance(other, int):
            return self.level == other
        else:
            return NotImplemented


class SKAcrobatics(Skill):
    'Acrobatics Skill, required for complex movement.'
    name = 'Acrobatics'

    def __init__(self, level):
        super().__init__(level)


class SKKnifeHandling(Skill):
    'Acrobatics Skill, required for complex movement.'
    name = 'Knife Handling'

    def __init__(self, level):
        super().__init__(level)


class SKBowHandling(Skill):
    'Acrobatics Skill, required for complex movement.'
    name = 'Bow Handling'

    def __init__(self, level):
        super().__init__(level)


class SKEarthBending(Skill):
    'Earthbending, required for earthbending moves.'
    name = 'Earthbending'

    def __init__(self, level):
        super().__init__(level)


class SKWaterBending(Skill):
    'Waterbending, required for waterbending moves.'
    name = 'Waterbending'

    def __init__(self, level):
        super().__init__(level)


class SKFireBending(Skill):
    'Firebending, required for Firebending moves.'
    name = 'Firebending'

    def __init__(self, level):
        super().__init__(level)


class SKAirBending(Skill):
    'Airbending, required for Airbending moves.'
    name = 'Airbending'

    def __init__(self, level):
        super().__init__(level)


# Initialize Items and Moves
class Item:
    """A item that can be used by a Fighter.
values - A dictionary of values.
    Common values include:
    'name': 'Name of item',
    'description': 'Description of the item',

    'count': 1  # Amount of the current item.
    'maxCount': 64  # Maximum amount that can be stacked"""

    def __init__(self, values: dict):
        self.values = values

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.values)

    def __str__(self):
        return self['name']

    def __len__(self):
        """Return the amount of the item."""
        return len(self['count'])

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


class Move:
    """A move that can be used by a Fighter.

    Args:
        values (Dict[str, Any]): A dictionary of values.
            Common values include:
            'name': 'Name of move',
            'moveTypes': ([MTPhysical],),
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

    def __init__(self, values: Dict[str, Any]):
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
                f'Tried formatting a move with non-existent argument(s) \
{format})')

        message = ''.join(message)
        if format[-1] == 'abs':
            message = str(abs(num(message)))
        elif format[-1] == 'neg':
            message = str(-num(message))
        return message

    def fmt(self, format) -> str:
        """A shorter version of the __format__ method.

        Intended for use in moves to shorten messages.

        """
        return self.__format__(format)

    def averageValues(self, keyFormat) -> RealNum:
        """Calculate the average move values with stats.

        If the value is a Bound, will use average of the Bound.

        Variables provided for keyFormat:
            stat - The current stat being iterated through

        Example:
            moveObj.averageValues('{stat}Value')

        """
        total = []
        for stat in Fighter.allStats:
            key = eval("f'''" + keyFormat + "'''")
            if key in self:
                if isinstance(self[key], Bound):
                    total.append(self[key].average())
                else:
                    total.append(self[key])
        if (len_total := len(total)) == 0:
            # Return 0 for no values found
            return 0
        return sum(total) / len_total

    def info(self) -> str:
        """Return an informational string about the move.

        The description will be formatted with an environment containing:
            hp, st, mp: The respective StatInfo objects from Fighter.
            self: The instance of Move that the description is in.
        It will also have color placeholders formatted with `format_color`.

        """
        hp = Fighter.allStats['hp']
        st = Fighter.allStats['st']
        mp = Fighter.allStats['mp']
        return format_color(self['description'], namespace=locals())

    @staticmethod
    def parseUnsatisfactories(unsatisfactories):
        """Generate a string explaining why a move could not be used.

        Args:
            unsatisfactories: This should come from the output of
                Fighter.findMove where showUnsatisfactories = True.

        Returns:
            str: The explanation."""
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
                for item in reason.other[0]:
                    name = item['name']
                    count = item['count'] if 'count' in item else None

                    if count is None:
                        countMsg = 'Item'
                    else:
                        plur = 's' if count != 1 else ''
                        countMsg = f'{count:,} of item{plur}'

                    reasonMessageList.append(
                        f'\n{countMsg} "{name}" required')

        reasonMessageList = ', '.join(reasonMessageList)

        return reasonMessageList

    def searchKeys(self, sub) -> List[str]:
        """Search through the move's keys and return a list of all keys
that is a superset of sub."""
        return [k for k in self if sub in k]

    def searchValues(self, sub) -> List:
        """Search through the move's items and return a list of all values
if the corresponding key is a superset of sub."""
        return [v for k, v in self if sub in k]

    def searchItems(self, sub) -> Dict:
        """Search through the move's items and return a dictionary of all
key-value pairs if the key is a superset of sub."""
        return {k: v for k, v in self if sub in k}

    # def averageCounterMoveValues(self, counter):
    #     """Calculate the average move values for a counter."""
    #     return sum(
    #         [move[f'{counter}{stat.upper()}Value']
    #             for stat in Fighter.allStats
    #             if f'{counter}{stat.upper()}Value' in move
    #             ]
    #         )

    # def averageCounterMoveFailValues(self, counter):
    #     """Calculate the average move fail values for a counter.
    # Ignores criticals."""
    #     return sum(
    #         [move[f'{counter}Fail{stat.upper()}Value']
    #             for stat in Fighter.allStats
    #             if f'{counter}Fail{stat.upper()}Value' in move
    #             ]
    #         )


class StatusEffect:
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

    def __init__(self, values: Dict[str, Any]):
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


# Game Settings Handler 1/1
# Convert text color placeholders into color codes
GAME_SETUP_INPUT_COLOR = format_color(GAME_SETUP_INPUT_COLOR)


# Initialize Fighter Interactive Shells
class FighterBattleShell:
    """To be inherited by other battle shells along with cmd.Cmd."""
    intro = ''  # Message when shell is opened
    prompt_default = '> '
    prompt = prompt_default  # Input prompt

    ruler = '='  # Used for help message headers
    doc_leader = ''  # Printed before the documentation headers
    doc_header = 'Commands (type help <command>):'
    misc_header = 'Help topics (type help <topic>):'
    # undoc_header should not show up because all commands
    # should have documentation
    undoc_header = 'Undocumented commands'
    nohelp = 'There is no information on "%s".'

    cmdqueue = None  # A list of command inputs to run
    lastcmd = None   # The previous command input

    def __init__(self, fighter, opponent, namespace, cmdqueue=None,
                 *, completekey='tab', stdin=None, stdout=None):
        """Initialize the shell.

        Args:
            fighter (Fighter):
                The fighter that the shell is interfacing with.
            opponent (Fighter):
                The opponent of the fighter in the 1v1 battle.
            namespace (dict):
                A dictionary to store outputs from the shell.
                Required for receiving outputs from the shell.
            cmdqueue (Optional[list]):
                An optional list of commands to run.
            completekey (str):
                The key that is used to auto-complete commands.
                See `cmd.Cmd` and `readline` for more details.

        """
        super().__init__(completekey, stdin, stdout)
        self.fighter = fighter
        self.opponent = opponent
        self.namespace = namespace
        if cmdqueue is None:
            self.cmdqueue = []
        else:
            self.cmdqueue = cmdqueue

        # Change documentation of built-in methods
        self.do_help.__func__.__doc__ = """\
List available commands or get detailed information about a command/topic.
Usage: help [cmd/topic]
Usage: ?[cmd/topic]"""

    # ----- Command Handlers -----
    def default(self, line):
        """Called when a command prefix is not recognized."""
        print_color('{Fyello}Unknown command')

    def emptyline(self):
        """Called when an empty line is entered.

        If this method is not overridden, it repeats the last
        non-empty command entered.

        """

    # ----- Commands -----
    # def do_debug(self, arg):
    #     """Activate the python debugger within the shell."""
    #     breakpoint()

    # ----- Internal methods -----
    def exit(self):
        """Helper method to self-document exiting the shell.

        Usage: return self.exit()

        """
        # When a command returns True, it should exit the shell
        return True

    def namespaceUpdateCmdQueue(self, namespace):
        """Update the command queue if given in a shell namespace.

        This method should be called right after a sub-shell is used.
        Usage: self.namespaceUpdateCmdQueue(namespace)

        """
        if 'shell_cmdqueue' in namespace:
            self.cmdqueue.append(namespace['shell_cmdqueue'])

    # def onecmd(self, str):
    #     This command reads a string as if it was typed into the shell.

    def updateCmdqueue(self, arg):
        """Helper command to update the command queue from a string.

        When a command does not need any arguments,
        use this to parse any given arguments as future commands.
        If the arg is False (empty string), it will not be appended.

        Use this over appending to cmdqueue for self-documentation.
        Usage: self.updateCmdqueue(arg)

        """
        if arg:
            self.cmdqueue.append(arg)

    def precmd(self, line):
        """Called before the line is interpreted.

        This should return the line, either passed through or modified.

        """
        return line

    # ----- Command Loop -----
    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.

        This command should return stop.
        onecmd() will return the return value here.

        Args:
            stop (bool): A flag indicating if execution will be terminated.
                Should be the return value of the method.
                If the method returns a false value, cmdloop will continue.
            line (str): The command that was interpreted.

        """
        return stop

    def preloop(self):
        """Called before cmdloop() runs."""

    def postloop(self):
        """Called right before cmdloop() returns."""


class FighterBattleMainShell(FighterBattleShell, cmd.Cmd):
    'The main battle interface.'
    # ----- Command Handlers -----

    # ----- Commands -----
    def do_move(self, arg):
        """Go into the Move Interface or run commands from it and return.
Usage: move [future commands]"""
        if 'shellFirstTime' in self.namespace:
            # Special first time interaction for showing help message
            # without kicking back into Main Interface on second opening
            namespace = dict()
        elif arg:
            # Command was executed with arguments; return to
            # Main Interface afterwards
            namespace = {'returnTo': True}
        else:
            namespace = dict()

        move_shell = FighterBattleMoveShell(
            self.fighter, self.opponent, namespace, [arg],
            completekey=GAME_DISPLAY_AUTOCOMPLETE_KEY)
        move_shell.cmdloop()
        self.namespaceUpdateCmdQueue(namespace)

        shell_result = namespace['shell_result']
        if isinstance(shell_result, Move):
            logger.debug(f'Player used move "{shell_result}"')
            # Pass data from Move Interface so code outside the main shell
            # can see the namespace
            for k, v in namespace.items():
                self.namespace[k] = v
            return self.exit()
        elif shell_result is None:
            # User went back into Main Interface
            if 'shellFirstTime' in self.namespace:
                # Remove 'shellFirstTime' to allow failed searches
                # done in Main Interface to redirect back to Main
                del self.namespace['shellFirstTime']
        elif shell_result is False:
            # Search failed
            pass

    def do_item(self, arg):
        """Go into the Item Interface or run commands from it and return.
Usage: item [future commands]"""
        print('This feature is currently unavailable.\n')

    def do_stats(self, arg):
        """View your current stats.
Usage: stats [future commands]"""
        print_color(
            BattleEnvironment.fightChartOne(
                self.fighter, color=GAME_DISPLAY_STATS_COLOR_MODE
            )[0]
        )
        print()

        self.updateCmdqueue(arg)

    def do_display(self, arg):
        """Display the current battle.
Usage: display [future commands]"""
        print_color(BattleEnvironment.fightChartTwo(
            self.fighter, self.opponent,
            topMessage='<--', tabs=GAME_DISPLAY_USE_TABS,
            color_mode=GAME_DISPLAY_STATS_COLOR_MODE)
        )
        print()

        self.updateCmdqueue(arg)

    # ----- Command Loop -----
    def preloop(self):
        """Called before cmdloop() runs."""
        logger.debug(f"{self.fighter.decoloredName}'s battle shell starting")
        if self.cmdqueue:
            if self.cmdqueue[0] == ['first_time']:
                # Special code for first time user start-up
                self.cmdqueue[0] = 'move help'
                self.namespace['shellFirstTime'] = True

    def postloop(self):
        """Called right before cmdloop() returns."""
        logger.debug(f"{self.fighter.decoloredName}'s battle shell exiting")


class FighterBattleMoveShellCommons(object):
    'Common attributes for the Move shell and its sub-shells.'

    # ----- Command Handlers -----
    def emptyline(self):
        """Called when an empty line is entered.

        If this shell was run from a super-shell without a command,
        stay in this shell.

        """
        if 'returnTo' in self.namespace:
            del self.namespace['returnTo']

    # ----- Commands -----
    def do_back(self, arg):
        """Go back to the Move Interface.
Usage: back [future commands]"""
        self.namespace['shell_result'] = None
        self.namespace['shell_cmdqueue'] = arg
        return self.exit()

    def do_list(self, arg):
        """List your current moves.
Usage: list [future commands]"""
        # Should be the same as in the Move shell
        print_color(self.fighter.formatMoves(
            ignoreSkills=True,
            ignoreItems=True)
        )
        print()

        self.updateCmdqueue(arg)


class FighterBattleMoveShell(
        FighterBattleMoveShellCommons, FighterBattleShell, cmd.Cmd):
    'The move interface.'
    prompt_default = 'Move: '
    prompt = prompt_default  # Input prompt

    def __init__(self, fighter, opponent, namespace, cmdqueue=None,
                 **kwargs):
        super().__init__(fighter, opponent, namespace, cmdqueue, **kwargs)

    # ----- Command Handlers -----
    def default(self, line):
        """Searches for the move."""
        inputMove = line.lower().title()

        moveFind, unsatisfactories = self.fighter.findMove(
            {'name': inputMove},
            ignoreSkills=True,
            ignoreItems=True,
            exactSearch=GAME_INPUT_MOVE_EXACT_SEARCH,
            detailedFail=True,
            showUnsatisfactories=True)

        # If search worked, check for unsatisfactories
        if not isinstance(moveFind, (type(None), BoolDetailed)):
            if unsatisfactories:
                # Missing dependencies; explain then request another move
                reasonMessage = f'Could not use {moveFind}; ' \
                                + moveFind.parseUnsatisfactories(
                                    unsatisfactories)
                if 'returnTo' in self.namespace:
                    print_color(reasonMessage)
                    self.namespace['shell_result'] = False
                    return self.exit()
                else:
                    self.prompt = reasonMessage + '\nPick another move: '
                    return

            else:
                # All dependencies satisfied; use the move
                self.namespace['shell_result'] = moveFind
                if 'returnTo' in self.namespace:
                    self.namespace['newMoveCMD'] = ''
                else:
                    self.namespace['newMoveCMD'] = 'move'
                return self.exit()

        # Else request for a move again
        elif moveFind is None:
            # Search failed (detailedFail=False)
            if 'returnTo' in self.namespace:
                print_color('Did not find move')
                self.namespace['shell_result'] = False
                return self.exit()
            else:
                self.prompt = 'Did not find move, type again: '
        elif isinstance(moveFind, BoolDetailed):
            # Search failed (detailedFail=True)
            if moveFind.name == 'TooManyResults':
                moveCount = int(moveFind.description.split()[1])
                message = f'Found {moveCount:,} different moves'
                if 'returnTo' in self.namespace:
                    print_color(message)
                    self.namespace['shell_result'] = False
                    return self.exit()
                else:
                    self.prompt = message + ', type again: '
            elif moveFind.name == 'NoResults':
                message = 'Did not find move'
                if 'returnTo' in self.namespace:
                    print_color(message)
                    self.namespace['shell_result'] = False
                    return self.exit()
                else:
                    self.prompt = message + ', type again: '
        else:
            raise RuntimeError('moveFind in playerTurnMove returned '
                               f'unknown object {moveFind!r}')

    # ----- Commands -----
    def do_info(self, arg):
        """Go into the Move Info Interface or run commands from it and return.
Usage: info [future commands]"""
        if arg or 'returnTo' in self.namespace:
            # Command was executed with arguments; return to
            # Move Interface afterwards
            namespace = {'returnTo': True}
        else:
            namespace = dict()
        info_shell = FighterBattleMoveInfoShell(
            self.fighter, self.opponent, namespace, [arg])
        info_shell.cmdloop()

        self.namespaceUpdateCmdQueue(namespace)

    # ----- Help Topic Commands -----
    def help_move(self):
        print_color("""
Type the move you want to use.
Use "list" to display your available moves.
""")

    # ----- Internal methods -----
    def precmd(self, line):
        """Called before the line is interpreted.
Resets the prompt to prompt_default."""
        self.prompt = self.prompt_default
        return line

    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.
Will check if 'returnTo' in self.namespace exists and if so, stop."""
        if not stop and 'returnTo' in self.namespace and not self.cmdqueue:
            self.namespace['shell_result'] = None
            return self.exit()
        return stop


class FighterBattleMoveInfoShell(
        FighterBattleMoveShellCommons, FighterBattleShell, cmd.Cmd):
    'The move info interface.'
    prompt_default = '(Info) Move: '
    prompt = prompt_default  # Input prompt

    def __init__(self, fighter, opponent, namespace, cmdqueue=None,
                 **kwargs):
        super().__init__(fighter, opponent, namespace, cmdqueue, **kwargs)

    # ----- Command Handlers -----
    def default(self, line):
        """Searches for the move."""
        inputMove = line.lower().title()

        moveFind = self.fighter.findMove(
            {'name': inputMove},
            ignoreMoveTypes=True,
            ignoreSkills=True,
            ignoreItems=True,
            exactSearch=GAME_INPUT_MOVE_EXACT_SEARCH,
            detailedFail=True)

        # If search worked, print info about the move
        if not isinstance(moveFind, (type(None), BoolDetailed)):
            print_color(moveFind.info())
            print()
            return

        # Else request for a move again
        elif moveFind is None:
            # Search failed (detailedFail=False)
            message = 'Did not find move'
            if 'returnTo' in self.namespace:
                print_color(message)
                return
            else:
                self.prompt = message + ', type again: '
        elif isinstance(moveFind, BoolDetailed):
            # Search failed (detailedFail=True)
            if moveFind.name == 'TooManyResults':
                moveCount = int(moveFind.description.split()[1])
                message = f'Found {moveCount:,} different moves'
                if 'returnTo' in self.namespace:
                    print_color(message)
                    return
                else:
                    self.prompt = message + ', type again: '
            elif moveFind.name == 'NoResults':
                message = 'Did not find move'
                if 'returnTo' in self.namespace:
                    print_color(message)
                    return
                else:
                    self.prompt = message + ', type again: '
        else:
            raise RuntimeError('MoveInfoShell from moveFind in playerTurnMove '
                               f'returned unknown object {moveFind!r}')

    # ----- Internal methods -----
    def precmd(self, line):
        """Called before the line is interpreted.
Resets the prompt to prompt_default."""
        self.prompt = self.prompt_default
        return line

    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.
Will check if 'returnTo' in self.namespace exists and if so, stop."""
        if not stop and 'returnTo' in self.namespace and not self.cmdqueue:
            return self.exit()
        return stop


# Initialize Fighters
class Fighter:

    StatInfo = collections.namedtuple(
        'StatInfo', [
            'int_short', 'int_full', 'ext_short', 'ext_full', 'color_fore'])
    allStats = {
        'hp': StatInfo('hp', 'health',
                       'HP', 'health',
                       ColoramaCodes.FLgree),
        'st': StatInfo('st', 'stamina',
                       'ST', 'stamina',
                       ColoramaCodes.FLyell),
        'mp': StatInfo('mp', 'mana',
                       'MP', 'mana',
                       ColoramaCodes.FLcyan)
        }
    allCounters = {  # Footnote 1
        'none': 'none',
        'block': 'block',
        'evade': 'evade'
        }

    def __init__(
            self, battle_env, name: str,
            hp: int, hpMax: int, hpRate: int,
            st: int, stMax: int, stRate: int,
            mp: int, mpMax: int, mpRate: int,
            status_effects: List[StatusEffect] = None,
            skills: List[Skill] = None,
            moveTypes: List[MoveType] = None,
            moves: List[Move] = None,
            counters: Dict[str, str] = None,
            inventory: List[Item] = None,
            isPlayer: bool = False,
            AI=None,
            battleShellDict=None):

        self.battle_env = battle_env

        self.name = name

        # Create attributes for each stat
        for stat in self.allStats:
            exec(f"""\
self._{stat} = {stat}
self.{stat}Max = {stat}Max
self.{stat}Rate = {stat}Rate""")

        # Status Effects default is an empty list
        if status_effects is None: self.status_effects = []
        else: self.status_effects = status_effects

        # Skills default is an empty list
        if skills is None: self.skills = []
        else: self.skills = skills

        # Move Type default is an empty list
        if moveTypes is None: self.moveTypes = []
        else: self.moveTypes = moveTypes

        # Counters default are all counters
        if counters is None: self.counters = self.allCounters.copy()
        else: self.counters = counters

        # Inventory default is an empty list
        if inventory is None: self.inventory = []
        else: self.inventory = inventory

        # Moves default is an empty list
        if moves is None: self.moves = []
        else: self.moves = moves

        # isPlayer default is False
        self.isPlayer = isPlayer

        # AI default is FighterAIGeneric()
        # Not default argument because AIs are created after this
        if AI is None: self.AI = FighterAIGeneric()
        else: self.AI = AI

        if battleShellDict is None:
            self.battleShellDict = {
                # Autorun on start of playerTurnMove Shell
                'moveCMD': ['first_time']
            }
        else:
            self.battleShellDict = battleShellDict

        logger.debug(
            'Created {}({}, \
{}, {}, {}, {}, {}, {}, {}, {}, {}, \
{}, {}, {}, {}, {}, {}, {})'.format(
    self.__class__.__name__, repr(name),
    hp, hpMax, hpRate, st, stMax, stRate, mp, mpMax, mpRate,
    skills, moveTypes, moves, counters, inventory,
    isPlayer, repr(AI)
    )
        )

    # Create properties for each stat created in __init__
    for stat in allStats:
        exec(f"""\
@property
def {stat}(self):
    if self._{stat} < 0:
        self._{stat} = 0
    if self._{stat} > self.{stat}Max:
        self._{stat} = self.{stat}Max
    return self._{stat}

@{stat}.setter
def {stat}(self, {stat}):
    self._{stat} = {stat}""")

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name!r}, \
{self.hp}, {self.hpMax}, {self.hpRate}, \
{self.st}, {self.stMax},{self.stRate}, \
{self.mp}, {self.mpMax},{self.mpRate}, \
{self.skills}, {self.moveTypes}, \
{self.moves}, {self.counters}, \
{self.inventory}, {self.isPlayer}, \
{self.AI!r})'

    def __str__(self):
        return format_color(self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self._decoloredName = format_color(name, no_color=True)

    @property
    def decoloredName(self):
        return self._decoloredName

    @decoloredName.setter
    def decoloredName(self, name):
        raise AttributeError(
            'This attribute cannot be changed directly; use self.name')

    def __bool__(self):
        return self.hp > 0

    def updateStatusEffectsDuration(self):
        """Update all durations and remove completed status effects.

        Returns:
            list: A list of wearoff messages.

        """
        effects = self.status_effects
        messages = []
        i = 0
        while i < len(effects):
            if effects[i]['duration'] <= 0:
                if 'wearoffMessage' in effects[i]:
                    messages.append((effects[i], 'wearoffMessage'))
                del effects[i]
            else:
                effects[i]['duration'] -= 1
                i += 1
        return messages

    def applyStatusEffectsValues(self, changeRandNum=True):
        """Apply status effect values."""
        messages = []
        for effect in self.status_effects:
            for stat, stat_info in self.allStats.items():
                key = f'{stat}Value'
                if key in effect and hasattr(self, stat):
                    statConstant = stat_info.int_full
                    value = Bound.callRandom(effect[key])
                    value *= (
                        self.battle_env.base_values_multiplier_percent / 100
                    )
                    value *= eval(
                        'self.battle_env.base_value_'
                        f'{statConstant}_multiplier_percent'
                    ) / 100
                    if changeRandNum and isinstance(effect[key], Bound):
                        effect[key].randNum = value
                    exec(f'self.{stat} += int({value})')
            if 'applyMessage' in effect:
                messages.append((effect, 'applyMessage'))
        return messages

    def printStatusEffectsMessages(self, messages, printDelay=0):
        for effect, message in messages:
            self.printStatusEffect(effect, message, end=None)
            pause(printDelay)

    def updateStats(self, stats=None):
        """Calls self.updateStat for each stat the Fighter has."""
        if stats is None:
            stats = self.allStats
        for stat in stats:
            # Update stat if available
            if hasattr(self, stat):
                self.updateStat(stat)

    def updateStat(self, stat):
        value = eval(f'self.{stat}Rate')

        value *= eval(f'self.battle_env.{stat}_rate_percent') / 100

        value *= self.battle_env.regen_rate_percent / 100

        value = round(value)

        exec(f'self.{stat} += {value}')

    @classmethod
    def printMove(cls, sender, target, move, message='moveMessage'):
        """Formats a move's message and prints it.

        An environment is provided to be used for formatting:
            sender: The Fighter sending the move.
            target: The Fighter receiving the move.
            move: The Move being used.
            hp, st, mp: The respective StatInfo objects.
        There are other variables available but are not intended for use:
            cls: The Fighter class.
            message: The message that was extracted from `move`.

        """
        hp = cls.allStats['hp']
        st = cls.allStats['st']
        mp = cls.allStats['mp']
        print_color(move[message], namespace=locals())

    def printStatusEffect(self, effect, message='applyMessage', **kwargs):
        """Formats a status effect's message and prints it.

        An environment is provided to be used for formatting:
            self: The Fighter receiving the effect.
            move: The Move being used.
            hp, st, mp: The respective StatInfo objects.
        If the status effect has a *Value, it will be available
        for formatting.
        There are other variables available but are not intended for use:
            message: The message that was extracted from `move`.

        """
        if message in effect:
            hp = self.allStats['hp']
            st = self.allStats['st']
            mp = self.allStats['mp']
            for stat in self.allStats:
                value = f'{stat}Value'
                if value in effect:
                    exec(f'{value} = num(float(effect[{value!r}]))')
            print_color(effect[message], namespace=locals(), **kwargs)

    @staticmethod
    def findDict(objectList, values: dict,
                 exactSearch=True, detailedFail=False):
        """Find the first matching object in a list of objects by values.

        objectList - A list of objects to search through.
        values - A dictionary of values to compare.
        exactSearch - If True, match strings exactly.
            When exactSearch is True:
                'foo' == 'foo'
                'foo' != 'foobar'
                'Foo' != 'foo'
            When exactSearch is False:
                'foo' in 'foo'
                'foo' in 'foobar'
                    'Foo'.casefold() in 'foo'.casefold()

        Note: Do not pass in an iterator for `objectList`;
        this function requires more than one iteration (logging message)
        and will silently fail with an iterator,
        returning no results.

        """
        logger.debug(f'Finding {values} in {[str(o) for o in objectList]}')
        if len(values) == 0:
            logger.debug(f'{values} is empty, returning objectList')
            return objectList
        results = []
        # resultsAreExact for unexact search
        # If a search returns an exact find, dump unexact results and look
        # for any other exact matches to confirm that there is only one
        resultsAreExact = False
        for obj in objectList:
            # Note: Cannot use dict().items() bitwise AND, doesn't work with
            # moves containing itemRequired or other values containing
            # a dictionary
            if exactSearch:
                for value in values.items():
                    if value not in obj.values.items():
                        logger.debug(
                            f'{obj} has no exact key-value pair {value}')
                        break  # Missing value; continue with next object
                else:
                    logger.debug(f'{obj} exactly matched {values}')
                    return obj  # Found all values; return object
            else:
                # Unexact search
                unexactMatchExists = False
                exactMatchExists = True
                for value in values.items():
                    # Do exact matching before unexact matching
                    if value in obj.values.items():
                        continue
                    else:
                        exactMatchExists = False
                    if value[0] in obj.values.keys():
                        # Do substring checking for strings
                        if isinstance(obj.values[value[0]], str):
                            if value[1].casefold() \
                                    in obj.values[value[0]].casefold():
                                unexactMatchExists = True
                            else:
                                logger.debug(f"{obj} doesn't have superstring "
                                             f"of {value}")
                                break  # Missing superstring; go to next object
                        # Do exact matching for non-string key-value pairs
                        elif value not in obj.values.items():
                            logger.debug(
                                f'{obj} has no exact key-value pair {value}')
                            break  # Missing value; continue with next object
                    else:
                        logger.debug(f'{obj} has no key-value pair {value}')
                        break  # Missing value; continue with next object
                else:
                    if exactMatchExists:
                        logger.debug(f'{obj} exactly matched {values}')
                        if not resultsAreExact:
                            results.clear()
                            resultsAreExact = True
                        results.append(obj)
                    elif unexactMatchExists and not resultsAreExact:
                        logger.debug(
                            f'{obj} unexactly matched {values}')
                        results.append(obj)
                    elif unexactMatchExists and resultsAreExact:
                        logger.debug(
                            f'{obj} unexactly matched {values} but already '
                            'found an exact(s) match')
                    else:
                        raise RuntimeError(f'Unknown results from search\n\
exactMatchExists = {exactMatchExists}\n\
unexactMatchExists = {unexactMatchExists}\n\
resultsAreExact = {resultsAreExact}')
        if (len_res := len(results)) == 1:
            # Found one object (unexact search)
            return results[0]
        if len_res == 0:
            # Ran through objects; found nothing
            if detailedFail:
                return BoolDetailed(
                    False,
                    'NoResults',
                    'Did not find any results')
            return None
        if len_res > 1:
            # Ran through objects; found too many results
            if detailedFail:
                return BoolDetailed(
                    False,
                    'TooManyResults',
                    f'Found {len_res} results')
            return None

    class findDict_Object:
        """Convert non-move like objects into move-like objects
that supports being searched by findDict."""

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


    def findItem(self, values, *,
                 raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching item in the Fighter's inventory.
values - A dictionary of values to compare."""
        item = self.findDict(
            self.inventory, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if item is None:
                raise ValueError(
                    f'{self} failed to find an item with values {values}')
            elif isinstance(move, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find an item with values {values}\n'
                    f'Details: {item!r}')

        logger.debug(f"{self.decoloredName}'s Item search "
                     f'returned "{item}"')
        return item

    def findMove(
            self, values: dict, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False,
            showUnsatisfactories=False, **kwargs) -> \
                Union[None, Move, BoolDetailed,
                      Tuple[Optional[Move], List[BoolDetailed]]]:
        """Find the first matching move in the Fighter's moves.

        Args:
            values (Dict): A dictionary of values to compare.
            raiseIfFail (bool): Raise ValueError if a move is not found.
            exactSearch (bool): Match strings exactly instead of by membership.
            detailedFail (bool): Return BoolDetailed when failing a search.
            showUnsatisfactories (bool): Return a tuple containing the search
                result and a list of BoolDetailed objects describing
                unsatisfactories.
                This should only be True when an ignore* keyword argument is
                passed to availableMoves(), and will raise a ValueError
                if it isn't.

        Returns:
            None: Failed to find a result and detailedFail is False.
            Move: A Move was found.
            BoolDetailed: Failed to find a result and detailedFail is True.
            Union[None, Move, BoolDetailed,
                  Tuple[Optional[Move], Optional[BoolDetailed]]]:
                showUnsatisfactories is True and is returning a tuple;
                it contains the search result and a list of
                BoolDetailed objects describing missing dependencies
                of the move. If there are no missing dependencies,
                the list will be empty.

        """
        if showUnsatisfactories:
            # Check if there's a valid reason to have this True
            for key in kwargs:
                if 'ignore' in key:
                    break
            else:
                raise ValueError(
                    'showUnsatisfactories is True but no ignore* keyword '
                    f'argument was passed into findMove ({kwargs!r})'
                )

        # Search for move
        move = self.findDict(
            self.availableMoves(**kwargs), values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if move is None:
                raise ValueError(
                    f'{self} failed to find a move with values {values}')
            elif isinstance(move, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find a move with values {values}\n'
                    f'Details: {move!r}')

        if showUnsatisfactories:
            unsatisfactories = []

        if showUnsatisfactories \
                and isinstance(move, Move):
            def req_plural(req, req_name):
                'Create the missing requirement message.'
                length = len(req[1])
                plur = 's are' if length != 1 else ' is'
                return f'{length} {req_name} requirement{plur} not satisfied'

            # Get search with all requirements
            MoveTypeReq = self.availableMoveCombinationMoveType(
                move, verbose=showUnsatisfactories)
            if MoveTypeReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGMOVETYPE',
                    req_plural(MoveTypeReq, 'MoveType'),
                    MoveTypeReq[1]
                ))
            SkillReq = self.availableMoveCombinationSkill(
                move, verbose=showUnsatisfactories)
            if SkillReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGSKILL',
                    req_plural(SkillReq, 'Skill'),
                    SkillReq[1]
                ))
            InventoryReq = self.availableMoveCombinationInventory(
                move, verbose=showUnsatisfactories)
            if InventoryReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGITEM',
                    req_plural(InventoryReq, 'Item'),
                    InventoryReq[1]
                ))

        logger.debug(f"{self.decoloredName}'s Move search "
                     f'returned "{move}"')
        if showUnsatisfactories:
            return move, unsatisfactories
        return move

    def findCounter(
            self, values, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching counter in the Fighter's counters.

values - A dictionary of values to compare.
raiseIfFail - If True, raise ValueError if a counter is not found.
exactSearch - If True, match strings exactly instead of by membership.
detailedFail - If True, return BoolDetailed when failing a search."""
        counters = [
            self.findDict_Object({'name': i}) for i in self.counters.values()]
        counter = self.findDict(
            counters, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if counter is None:
                raise ValueError(
                    f'{self} failed to find a counter with values {values}')
            elif isinstance(counter, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find a counter with values {values}\n'
                    f'Details: {counter!r}')

        logger.debug(f"{self.decoloredName}'s Counter search "
                     f'returned "{counter}"')
        return counter

    def formatCounters(self):
        """Return a string showing the available counters."""
        return ', '.join([str(c) for c in self.counters.values()])

    def formatMoves(self, **kwargs):
        """Return a string showing the available moves."""
        return ', '.join([str(move) for move in self.availableMoves(**kwargs)])

    def moveCost(self, move, stat, failMessage):
        """If possible, apply costs onto Fighter and return True."""
        if move['name'] == 'None':
            return None
        # If stat cost in move exists
        if f'{stat}Cost' in move:
            # If Fighter can pay stat cost
            if eval(f'self.{stat}') \
                    + self.genCost(move, stat, 'normal') >= 0:
                exec(f"self.{stat} += round(float(move['{stat}Cost']))")
                return True
            else:
                # Print not enough stat message
                int_short, int_full, \
                    ext_short, ext_full, \
                    color_fore, *_ = self.allStats[stat]
                print_color(failMessage, namespace=locals())
                return False
        # Stat cost doesn't exist: return None
        return None

    def useMoveItems(self, move_or_combination=None, display=True):
        """Find the combination of items to be used, and subtract them from
the Fighter's inventory. Will fail if no combination was found that worked.
move_or_combination
    Either a combination of items to use, or a move to automatically calculate
    the first requirements needed.
display - If True, will print out the items that are used and their new count.
"""
        if isinstance(move_or_combination, Move):
            combination = self.availableMoveCombinationInventory(move)
        else:
            combination = move_or_combination

        # Return detailed booleans if that was given
        if isinstance(combination, BoolDetailed):
            return combination
        # Raise TypeError if received invalid combination
        if not isinstance(combination, list):
            raise TypeError(f'\
Expected combination of type list, given object of type {type(combination)}')

        for itemDict in combination:
            invItem = self.findItem({'name': itemDict['name']})

            # If required, find item in inventory and subtract from it
            if 'count' in itemDict:
                invItem['count'] -= itemDict['count']

            # If invItem count is negative, something has gone terribly bad
            if invItem['count'] < 0:
                raise RuntimeError(f'Item {invItem} count '
                                   f"has gone negative: {invItem['count']}")

            # Else if item count is 0, delete it from inventory
            elif invItem['count'] == 0:
                index = self.inventory.index(invItem)
                del self.inventory[index]

            # Conditionally print out the item used
            if display:
                name = invItem['name']
                if 'count' in itemDict:
                    used = itemDict.get('count', 0)
                    newCount = invItem['count']
                    print_color(f'{used:,} {name}{plural(used)} used '
                                f'({newCount:,} left)')
                else:
                    print_color(f'{name} used')

    def playerTurnMove(self, target, cmdqueue=None):
        """Obtains a move from the player."""
        logger.debug(f"{self.decoloredName} is moving")
        if cmdqueue is None:
            cmdqueue = [self.battleShellDict['moveCMD']]
        namespace = dict()
        FighterBattleMainShell(
            self, target, namespace, cmdqueue,
            completekey=GAME_DISPLAY_AUTOCOMPLETE_KEY).cmdloop()
        self.battleShellDict['moveCMD'] = namespace['newMoveCMD']
        return namespace['shell_result']


    def playerCounter(self, move, sender):
        """Obtains a counter from the player.
Note: No counter shell has been created so the placeholder interface code
below is being used."""
        print_color(f'{INDENT}\
{sender} is using {move}, but {self} is able to use a counter!')

        countersMessage = self.formatCounters()

        prompt = (
            f'{INDENT}Counter to attempt performing '
            f'({countersMessage}): '
        )

        while True:
            user_input = input(prompt).lower().strip()

            if user_input == '':
                prompt = (
                    f'{INDENT}Type one of the counters '
                    f'({countersMessage}): '
                )
                continue

            search = self.findCounter(
                {'name': user_input},
                exactSearch=False, detailedFail=True)

            # If search worked, return the counter
            if not isinstance(search, (type(None), BoolDetailed)):
                # Return name since that's how counters work
                return search['name']

            # Else request for a counter again
            elif search is None:
                # Search failed (detailedFail=False)
                prompt = f'{INDENT}Did not find counter, type again: '
            elif isinstance(search, BoolDetailed):
                # Search failed (detailedFail=True)
                if search.name == 'TooManyResults':
                    counterCount = int(search.description.split()[1])
                    prompt = (
                        f'{INDENT}Found {counterCount:,} '
                        'different counters, type again: '
                    )
                elif search.name == 'NoResults':
                    prompt = f'{INDENT}Did not find counter, type again: '

    def move(self, target, move=None):
        logger.debug(f'{self.decoloredName} is moving against {target}')

        # Don't move if an effect has noMove
        for effect in self.status_effects:
            if 'noMove' in effect:
                self.printStatusEffect(effect, 'noMove')
                return

        # If a move is not given, give control to AI/player
        if not move:
            if not self.isPlayer:
                logger.debug(f"{self.decoloredName}'s AI {self.AI} "
                             'is choosing a move')
                move = self.AI.analyseMove(self, target)
            else:
                move = self.playerTurnMove(target)

        logger.debug(f'{self.decoloredName} chose the move "{move}"')

        if move['name'] == 'None':
            print_color(f'{self} did not move.')
            logger.debug(f'{self.decoloredName} sent "{move}" to {target}')
            target.moveReceive(move, sender=self)
            return

        # Combinations available to use move
        if not self.availableMoveCombinationSkill(move):
            logger.debug(f'{self.decoloredName} failed to move; '
                         'lack of skills')
            print_color(f'\
{self} tried using {move} but did not have the needed skills.')
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    target, move, self, info=('senderFail', 'missingSkills'))
            return
        itemRequirements = self.availableMoveCombinationInventory(move)
        if not itemRequirements:
            logger.debug(f'{self.decoloredName} failed to move; '
                         'lack of items')
            print_color(f'\
{self} tried using {move} but did not have the needed items.')
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    target, move, self, info=('senderFail', 'missingItems'))
            return

        # Stat Costs
        for int_short, *_ in self.allStats.values():
            # If move failed due to low stats, stop
            if self.moveCost(
                    move, int_short, '{self} tried using {move} '
                    'but the {ext_full} cost was {move:{int_short}C neg}.') \
                    is False:
                logger.debug(f'{self.decoloredName} failed to move; '
                             'lack of {int_short}')
                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        target, move, self, info=(
                            'senderFail', 'lowStats', int_short))
                return

        # Use any items and display the usage if Fighter is a player
        self.useMoveItems(itemRequirements, display=self.isPlayer)
        # Finished, send move
        logger.debug(f'{self.decoloredName} sent "{move}" to {target}')
        target.moveReceive(move, sender=self)

    def receiveEffect(self, effect, stackDuration=True):
        """Receive a StatusEffect.

        If the name of `effect` matches the name of another effect,
        that current effect is replaced with the new effect.

        Args:
            effect (StatusEffect): The effect to add.
            stackDuration (bool): If there is another effect
                with the same name, replace that effect but add its duration
                onto the new `effect`.

        """
        for i, current_effect in enumerate(self.status_effects):
            if str(current_effect) == str(effect):
                if stackDuration:
                    effect['duration'] += self.status_effects[i]['duration']
                self.status_effects[i] = effect
                break
        else:
            self.status_effects.append(effect)

        if 'receiveMessage' in effect and self.hp > 0:
            # Print receive message so long as the fighter has enough health
            # Footnote 3
            self.printStatusEffect(effect, 'receiveMessage')

    def moveReceiveEffects(self, move, info=None, sender=None):
        logger.debug(f'{self} receiving effects from {move}')
        def apply_effect(target, effect):
            logger.debug(f'Applying effect {effect}')

            def chance_to_apply(chance):
                result = (
                    Dice()(gen_float=True) <= chance
                    * self.battle_env.base_status_effects_chance_multiplier
                    / 100
                )
                if result:
                    target.receiveEffect(effect.copy())
                return result

            def check_uncountered():
                if chance[1] == 'uncountered':
                    # Conditional syntax: If move was not countered
                    # (100, 'uncountered')
                    result = False
                    if 'normal' in info or 'critical' in info \
                            or 'fail' in info:
                        result = chance_to_apply(chance[0])
                    return {'applied': result}

            default_chance = None

            for chance in effect['chances']:
                logger.debug(f'Effect chance {chance}')
                if len(chance) == 1:
                    # Default; triggers only if all other chances failed
                    # and the move itself did not fail
                    # (100,)
                    default_chance = chance[0]
                elif check_uncountered():
                    return
                elif chance[1] == 'failure':
                    # If move failed
                    if 'senderFail' in info and chance_to_apply(chance[0]):
                        return
                elif chance[1] == 'fast':
                    # If move was fast
                    if 'fast' in info and chance_to_apply(chance[0]):
                        return
                elif chance[1] == 'critical':
                    # If move was critical
                    if 'critical' in info and chance_to_apply(chance[0]):
                        return
                else:
                    # Counters
                    situation_found = False
                    for counter in self.allCounters:
                        if chance[1] == counter and counter in info:
                            # If counter was attempted
                            logger.debug(f'{counter} attempted chance '
                                         f'of {chance[0]}')
                            if chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                        elif chance[1] == f'{counter}Success':
                            # If counter was successful
                            logger.debug(f'{counter}Success chance '
                                         f'of {chance[0]}')
                            if counter in info and 'success' in info \
                                    and chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                        elif chance[1] == f'{counter}Failure':
                            # If counter failed
                            logger.debug(f'{counter}Failure chance '
                                         f'of {chance[0]}')
                            if counter in info and (
                                        'fail' in info or 'critical' in info
                                    ) and chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                    if situation_found:
                        # Found correct situation for counter
                        # but chance_to_apply failed
                        continue
                    else:
                        raise ValueError(
                            f'Unknown chance format {chance!r}')

            if default_chance is not None and not 'senderFail' in info:
                chance_to_apply(default_chance)

        if 'effects' in move:
            default = None
            for effect in move['effects']:
                if effect['target'] == 'target':
                    apply_effect(self, effect)
                elif effect['target'] == 'sender' and sender is not None:
                    apply_effect(sender, effect)

    def moveReceive(self, move, sender=None):
        logger.debug(f'{self.decoloredName} is receiving "{move}" '
                     f'from {sender.decoloredName}')
        if move['name'] == 'None':
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=('noneMove',))
            return
        # If move fails by chance
        if Dice()(gen_float=True) <= self.genChance(move, 'failure'):
            logger.debug(f'"{move}" failed against {self.decoloredName}')
            if sender is not None:
                logger.debug(f'{sender.decoloredName} is receiving '
                             'failure values')
                sender.genFailureValues(move)
                self.printMove(sender, self, move, 'failureMessage')
                sender._moveReceive(move, values='failure')

                info = ('senderFail', 'chance')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
                return
        # If move counter is possible
        if sender is not None \
                and Dice()(gen_float=True) <= self.genChance(move, 'speed'):
            # Don't counter if an effect has noCounter
            def hasNoCounterStatusEffect():
                for effect in self.status_effects:
                    if 'noCounter' in effect:
                        logger.debug(f'{self.decoloredName} has noCounter '
                                     f'status effect from "{effect}"')
                        # Footnote 3
                        self.printStatusEffect(effect, 'noCounter')
                        return True
                return False

            if hasNoCounterStatusEffect():
                counter = 'none'
            elif not self.isPlayer:
                logger.debug(f"{self.decoloredName}'s AI {self.AI} "
                             f'is countering "{move}"')
                counter = self.AI.analyseMoveCounter(self, move, sender)
            else:
                logger.debug(f"{self.decoloredName}'s player "
                             f'is countering "{move}"')
                counter = self.playerCounter(move, sender)

        # If move counter failed
        else:
            if sender is not None:
                logger.debug(f'{self.decoloredName} cannot counter the move')
            counter = False

        logger.debug(f'{self.decoloredName} is using counter {counter!r}')

        # Counter System
        if counter == 'block':
            self.moveReceiveCounterBlock(move, sender)
        elif counter == 'evade':
            self.moveReceiveCounterEvade(move, sender)
        elif counter == 'none':
            self.moveReceiveCounterNone(move, sender)
        elif counter is False:
            self.moveReceiveCounterFalse(move, sender)
        else:
            raise RuntimeError(
                'During moveReceive while countering, '
                f'an unknown counter was given: {counter!r}')

    def moveReceiveCounterNone(self, move, sender):
        # If move is critical
        if Dice()(gen_float=True) <= self.genChance(move, 'critical'):
            logger.debug(f'"{move}" against {self.decoloredName} '
                         'is a critical')
            self.genValues(move)
            self.genCriticalValues(move)
            self.printMove(sender, self, move, 'criticalMessage')
            self._moveReceive(move, values='critical')
            # Apply status effects
            info = ('none', 'critical')
            self.moveReceiveEffects(move, info, sender)
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.decoloredName} is normal')
            self.genValues(move)
            self.printMove(sender, self, move)
            self._moveReceive(move, values='none')

            info = ('none', 'normal')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)

    def moveReceiveCounterFalse(self, move, sender):
        # If move is critical
        if Dice()(gen_float=True) <= self.genChance(move, 'critical'):
            logger.debug(f'"{move}" against {self.decoloredName} '
                         'is a fast critical')
            self.genCriticalValues(move)
            self.printMove(sender, self, move, 'fastCriticalMessage')
            self._moveReceive(move, values='critical')

            info = ('fast', 'critical')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.decoloredName} is fast')
            self.genValues(move)
            self.printMove(sender, self, move, 'fastMessage')
            self._moveReceive(move, values='none')

            info = ('fast', 'normal')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)

    def moveReceiveCounterBlock(self, move, sender):
        # If move is blocked
        if Dice()(gen_float=True) <= self.genChance(move, 'block'):
            logger.debug(f'"{move}" against {self.decoloredName} is blocked')
            self.genCounterValues(move, 'block')
            self.printMove(sender, self, move, 'blockMessage')
            self._moveReceive(move, values='block')

            info = ('block', 'success')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed block
            if Dice()(gen_float=True) <= self.genChance(move, 'critical'):
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed block critical')
                self.genCounterFailCriticalValues(move, 'block')
                self.printMove(sender, self, move, 'blockFailCriticalMessage')
                self._moveReceive(move, values='blockFailCritical')

                info = ('block', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed block')
                self.genCounterFailValues(move, 'block')
                self.printMove(sender, self, move, 'blockFailMessage')
                self._moveReceive(move, values='blockFail')

                info = ('block', 'fail')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)

    def moveReceiveCounterEvade(self, move, sender):
        # If move is evaded
        if Dice()(gen_float=True) <= self.genChance(move, 'evade'):
            logger.debug(f'"{move}" against {self.decoloredName} is evaded')
            self.genCounterValues(move, 'evade')
            self.printMove(sender, self, move, 'evadeMessage')
            self._moveReceive(move, values='evade')

            info = ('evade', 'success')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed evade
            if Dice()(gen_float=True) <= self.genChance(move, 'critical'):
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed evade critical')
                self.genCounterFailCriticalValues(move, 'evade')
                self.printMove(sender, self, move, 'evadeFailCriticalMessage')
                self._moveReceive(move, values='evadeFailCritical')

                info = ('evade', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed evade')
                self.genCounterFailValues(move, 'evade')
                self.printMove(sender, self, move, 'evadeFailMessage')
                self._moveReceive(move, values='evadeFail')

                info = ('evade', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)

    def _moveReceive(self, move,
                     values='none',
                     sender=None):
        """Private method for applying a move onto Fighter.
Pass in a tuple of stats to apply their corresponding values."""
        logger.debug(f'{self.decoloredName} is receiving values {values}')

        originalValues = values
        # If 'failure' is given, use all failure stats
        if values == 'none':
            values = [f'{stat}Value' for stat in self.allStats]
        elif values == 'failure':
            values = [f'failure{stat.upper()}Value' for stat in self.allStats]
        # If 'critical' is given, use all critical stats
        elif values == 'critical':
            values = [f'critical{stat.upper()}Value' for stat in self.allStats]
        else:
            for counter in self.allCounters:
                # If a counter is given, use all counter stats
                if values == counter:
                    values = [
                        f'{counter}{stat.upper()}Value'
                        for stat in self.allStats]
                # If a counter + 'Fail' is given,
                # use all counter fail stats
                elif values == counter + 'Fail':
                    values = [
                        f'{counter}Fail{stat.upper()}Value'
                        for stat in self.allStats]
                # If a counter + 'FailCritical' is given,
                # use all counter fail critical stats
                elif values == counter + 'FailCritical':
                    values = [
                        f'{counter}FailCritical{stat.upper()}Value'
                        for stat in self.allStats]
        if not isinstance(values, (tuple, list)):
            raise ValueError(
                f'Received {originalValues} but could not parse it')

        logger.debug(f'Parsed {originalValues!r} as {values}')

        for stat in self.allStats:
            statUpper = stat.upper()
            value = stat + 'Value'
            criticalValue = 'critical' + statUpper + 'Value'
            failValue = 'failure' + statUpper + 'Value'

            for counter in self.allCounters:
                cVal = counter + statUpper + 'Value'
                cFailVal = counter + 'Fail' + statUpper + 'Value'
                cFailCritVal = counter + 'FailCritical' + statUpper + 'Value'
                if cVal in values and cVal in move:
                    exec(f'self.{stat} += round(float(move[cVal]))')
                if cFailVal in values and cFailVal in move:
                    exec(f'self.{stat} += round(float(move[cFailVal]))')
                if cFailCritVal in values and cFailCritVal in move:
                    exec(f'self.{stat} += round(float(move[cFailCritVal]))')
            if value in values and value in move:
                exec(f'self.{stat} += round(float(move[value]))')
            if criticalValue in values and criticalValue in move:
                exec(f'self.{stat} += round(float(move[criticalValue]))')
            if failValue in values and failValue in move:
                exec(f'self.{stat} += round(float(move[failValue]))')
        if 'failureValue' in values and 'failureValue' in move:
            self.hp += round(float(move['failureValue']))

    @staticmethod
    def availableMoveCombination(move, requirement, objectList,
                                 membership_func=None, verbose=False):
        """Returns True if objectList has the requirements for a move.

        When no combination is required or the move is NoneMove,
        True is returned.
        When the first available combination is found, it is returned.
        If no combinations match, False is returned.
        Note: Returned booleans are of type BoolDetailed.

        Args:
            move (Move): The move to check.
            requirement:
                The requirements key from move to check in objectList.
            objectList:
                The container of prerequisites.
            membership_func (Optional[Callable]): The function to use to
                determine if an object in objectList matches the requirement.
                Takes the objectList and an object in a combination
                from requirement.

                def membership_func(objectList, obj):
                    ...

                If None, will use `obj in objectList`.
            verbose (bool): For moves with one combination of requirements, if
                items are missing, show them in the BoolDetailed description.

        Returns:
            BoolDetailed:
            Tuple[BoolDetailed, List]: verbose is True and there is only
                one combination of requirements, so a tuple is returned
                with the BoolDetailed and a list of the objects that were not
                in the objectList, if there were any.
            Tuple[BoolDetailed, None]: verbose is True but there is more than
                one combination of requirements, so no missing objects are
                returned. This could be programmed in to map the missing
                objects to each combination.

        """
        missing = []

        if move['name'] == 'None':
            result = BoolDetailed(
                True, 'NONEMOVE',
                'NoneMove was given.')
            if verbose:
                return result, missing
            return result

        if requirement in move:
            requirements = move[requirement]
            for combination in requirements:
                for obj in combination:
                    if membership_func is not None:
                        if membership_func(objectList, obj):
                            continue  # Object matched, continue combination
                    # No membership_func was given, test for membership
                    elif obj in objectList:
                        continue  # Object matched, continue combination

                    if verbose and len(requirements) == 1:
                        # Store the missing objects for verbose
                        missing.append(obj)
                        continue
                    else:
                        break  # Skip combination, object missing
                else:
                    if verbose:
                        return combination, missing
                    return combination
            else:
                result = BoolDetailed(
                    False, 'NOCOMBINATIONFOUND',
                    'Did not find any matching combination.')
                if verbose:
                    return result, missing
                return result
        else:
            result = BoolDetailed(
                True, 'NOREQUIREMENTS',
                'No requirements found.')
            if verbose:
                return result, missing
            return result

    def availableMoveCombinationMoveType(self, move, verbose=False):
        """Returns True if Fighter has the MoveType requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        return self.availableMoveCombination(
            move, 'moveTypes', self.moveTypes, verbose=verbose)

    def availableMoveCombinationSkill(self, move, verbose=False):
        """Returns True if Fighter has the Skill requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        def membership_func(objectList, combSkill):
            return any(
                selfSkill >= combSkill
                if type(selfSkill) == type(combSkill) else False
                for selfSkill in objectList
            )

        return self.availableMoveCombination(
            move, 'skillRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def availableMoveCombinationInventory(self, move, verbose=False):
        """Returns True if Fighter has the Item requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        def membership_func(objectList, itemDict):
            search = self.findItem({'name': itemDict['name']})
            if search is None:
                # Item not found
                return False
            if 'count' in itemDict:
                # Item needs to be depleted
                if search['count'] >= itemDict['count']:
                    # Item can be depleted
                    return True
                else:
                    # Item cannot be depleted
                    return False
            else:
                # Item doesn't need to be depleted
                return True

        return self.availableMoveCombination(
            move, 'itemRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def availableMove(
            self, move, *,
            ignoreMoveTypes=False, ignoreSkills=False, ignoreItems=False):
        """Returns True if a move can be available in the Fighter's moveset.

        The attributes that can influence this search are:
            self.moveTypes
            self.skills
            self.inventory

        Args:
            move (Move): The move to verify usability.
            ignoreMoveTypes (bool): Ignore checking for MoveTypes.
            ignoreSkills (bool): Ignore checking for Skills.
            ignoreItems (bool): Ignore checking for Items.

        """
        # MoveType Check
        if not ignoreMoveTypes \
                and not self.availableMoveCombinationMoveType(move):
            return BoolDetailed(
                False, 'MISSINGMOVETYPE',
                'Missing required move types.')
        # Skill Check
        if not ignoreSkills \
                and not self.availableMoveCombinationSkill(move):
            return BoolDetailed(
                False, 'MISSINGSKILL',
                'Missing required skills.')
        # Item Check
        if not ignoreItems \
                and not self.availableMoveCombinationInventory(move):
            return BoolDetailed(
                False, 'MISSINGINVENTORY',
                'Missing required items.')

        return True

    def availableMoves(self, moves=None, **kwargs):
        """Returns a list of available moves from a list of moves.
moves - The list to filter. If None, will use self.moves."""
        if moves is None:
            moves = self.moves
        return [move for move in moves if self.availableMove(
            move, **kwargs)]

    # Value Generators
    def genValue(self, move, stat, changeRandNum=True):
        """Generate a Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")
        statName = stat + 'Value'
        constantName = self.allStats[stat].int_full

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= eval(
            f'self.battle_env.base_value_{constantName}_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genValues(self, move, changeRandNum=True):
        """Generate values for every stat in a move.
Returns None if there is no value for a stat."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genValue(
                move, stat, changeRandNum)

        return values

    # Cost Generators
    def genCost(self, move, stat, case, changeRandNum=True):
        """Generate a Cost from a move.
move - The move to generate/extract the cost from.
stat - The stat cost that is being generated/extracted.
case - The situation that the failure value is being taken from.
    failure - When failing the move.
changeRandNum - If True, change the move's randNum
    to the generated cost if available."""
        cases = ('normal', 'failure')
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")
        if case not in cases:
            raise ValueError(
                f'{case} is not a valid situation '
                f"({', '.join([repr(c) for c in cases])})")

        statConstant = self.allStats[stat].int_full

        # Parse case into statName
        if case == 'normal':
            statName = stat + 'Cost'
        elif case == 'failure':
            statName = 'failure' + stat.upper() + 'Cost'
        else:
            raise RuntimeError(
                f'Could not parse case {case!r}, possibly no switch case')

        if statName not in move:
            return None

        cost = Bound.callRandom(move[statName])

        cost *= self.battle_env.base_energies_cost_multiplier_percent / 100
        cost *= eval(
            'self.battle_env.base_energy_cost_'
            f'{statConstant}_multiplier_percent'
        ) / 100

        cost = round(cost)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = cost

        return cost

    def genChance(self, move, chanceType):
        """Generate a chance from a move.
move - The move to extract chance from.
chanceType - The type of the chance to extract.
    Accepts counter names, 'speed', 'failure', and 'critical'."""
        validChancesNonCounter = ['speed', 'failure', 'critical']
        validChancesCounter = [counter for counter in self.allCounters]
        validChances = validChancesNonCounter + validChancesCounter
        if chanceType not in validChances:
            raise ValueError(
                f'{chanceType} is not a valid chance '
                f"({', '.join([repr(s) for s in validChances])})")

        chanceName = chanceType + 'Chance'

        if chanceType == 'speed':
            chance = 100 - move['speed']

            chance = divi_zero(
                chance, self.battle_env.base_speed_multiplier_percent / 100)

            return chance

        elif chanceType in validChancesNonCounter:
            chance = Bound.callRandom(move[chanceName])

            chance *= eval(
                f'self.battle_env.base_{chanceType}_chance_percent') / 100

            return chance

        elif chanceType in validChancesCounter:
            chanceConstant = self.allCounters[chanceType]

            chance = Bound.callRandom(move[chanceName])

            chance *= eval(
                f'self.battle_env.base_{chanceConstant}_chance_percent') / 100

            return chance

        else:
            raise RuntimeError(f'Failed to parse chanceType {chanceType}.')

    # Critical Generators
    def genCriticalValue(self, move, stat, changeRandNum=True):
        """Generate a Value from a move affected by its critical multiplier.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")

        statName = 'critical' + stat.upper() + 'Value'
        statConstant = self.allStats[stat].int_full

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= eval(
            f'self.battle_env.base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCriticalValues(self, move, changeRandNum=True):
        """Generate critical values for every stat in a move.
Returns None if there is no critical value for a stat."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genCriticalValue(
                move, stat, changeRandNum)

        return values

    # Counter Generators

    def genCounterValue(self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
counter - The counter's fail value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + stat.upper() + 'Value'
        statConstant = self.allStats[stat].int_full
        counterConstant = self.allCounters[counter]

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= eval(
            f'self.battle_env.base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= eval(
            f'self.battle_env.base_{counterConstant}_values_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterValues(self, move, counter, changeRandNum=True):
        """Generate counter values for every stat in a move.
Returns None if there is no counter value for a stat."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genCounterValue(
                move, stat, counter, changeRandNum)

        return values

    def genCounterFailValue(self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Fail Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
counter - The counter's fail value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + 'Fail' + stat.upper() + 'Value'
        statConstant = self.allStats[stat].int_full
        counterConstant = self.allCounters[counter]

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= eval(
            f'self.battle_env.base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= eval(
            f'self.battle_env.base_{counterConstant}'
            '_fail_value_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterFailValues(self, move, counter, changeRandNum=True):
        """Generate counter failure values for every stat in a move.
Returns None if there is no failure value for a stat."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genCounterFailValue(
                move, stat, counter, changeRandNum)

        return values

    def genCounterFailCriticalValue(
            self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Fail Value from a move affected by
its critical multiplier.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + 'FailCritical' + stat.upper() + 'Value'
        statConstant = self.allStats[stat].int_full

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= eval(
            f'self.battle_env.base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterFailCriticalValues(self, move, counter, changeRandNum=True):
        """Generate critical values for every stat in a move.
Returns None if there is no critical value for a stat."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genCounterFailCriticalValue(
                move, stat, counter, changeRandNum)

        return values

    def genFailureValue(self, move, stat, changeRandNum=True):
        """Generate a failure value from a move.
move - The move to generate/extract failureValue from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's failureValue.randNum
    to the generated failureValue if available."""
        if stat not in self.allStats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.allStats])})")

        statName = 'failure' + stat.upper() + 'Value'

        if statName not in move:
            return None

        value = Bound.callRandom(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= self.battle_env.base_failure_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    # Failure Generator
    def genFailureValues(self, move, changeRandNum=True):
        """Generate failure values for every stat in a move.
Returns None if there is no failure value for a stat.
move - The move to generate/extract failureValue from.
changeRandNum - If True, change the move's failure values' randNum
    to the generated value if available."""
        values = dict()
        for stat in self.allStats:
            values[stat] = self.genFailureValue(
                move, stat, changeRandNum)

        return values


class FighterAIGeneric:
    """Base Fighter AI.
state - The current AI's state. Utility is similar to a Finite State Machine.
stateNumber - A register storing a number for use in phases.
data - A dictionary for storing any values either for future computation
    or calculations in another function. If None, will use defaultData."""

    defaultData = {
        'hpValueBias': 1,  # Utilized for weighted value calculations
        'stValueBias': 1,
        'mpValueBias': 1,
        'counterSelectionMargin': 5,  # Determines selection of best counters
        'counterWeightData': dict(),

        'lastTargetMove': Move({'name': 'None'})
    }

    def __init__(self, state=None, stateNumber=None, data=None):
        logger.debug(f'Initialized AI: {self.__class__.__name__}')
        if state is None:
            self.state = ''
        else:
            self.state = state
        if stateNumber is None:
            self.stateNumber = 0
        else:
            self.stateNumber = stateNumber
        self.data = self.defaultData.copy()
        if data is not None:
            self.data.update(data)

    def __repr__(self):
        return (
                '{}(state={state}, stateNumber={stateNumber}, '
                'data={data})'
        ).format(
            self.__class__.__name__,
            state=self.state,
            stateNumber=self.stateNumber,
            data=self.data
        )

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def moveCostAverage(move, stat):
        """Return the average of a move stat cost.
If the cost is a Bound, returns the average of the left and right parameters.
Otherwise, returns the cost as is."""
        return Bound.callAverage(move[f'{stat}Cost'])

    @classmethod
    def analyseMoveCostBoolean(cls, user, move, stats=None):
        """Return True if a user has enough stat to use a move.
user - The Fighter using the move.
move - The move to analyse.
stats - An iterable of stats to check. If None, defaults to user.allStats."""
        if stats is None:
            stats = user.allStats
        # For each stat
        for stat in stats:
            # If stat cost exists for move
            if f'{stat}Cost' in move:
                # If user has more stat than the average
                # Note: Because average is middle of left and right Bound,
                # there's a 50% chance that the MP value generated will
                # be too expensive.
                if eval(f'user.{stat}') + cls.moveCostAverage(move, stat) > 0:
                    continue
                else:
                    return False

        # All stats can be paid for, return True
        return True

    @classmethod
    def analyseMoveCostValue(cls, user, move, stats=None):
        """Return a number based on the user and cost, using an algorithm.
user - The Fighter using the move.
move - The move to analyse.
stats - An iterable of stats to check. If None, defaults to user.allStats."""
        if stats is None:
            stats = user.allStats

        totalCost = 0

        for stat in stats:
            if f'{stat}Cost' in move:
                # In case a move explictly states a cost of 0:
                # If the stat's cost is 0, skip calculations
                if move[f'{stat}Cost'] == 0:
                    continue
                # If move is impossible to use
                if eval(f'user.{stat}Max') == 0:
                    return False

                # Cost starts at average move stat cost to stat ratio
                cost = divi_zero(
                    -cls.moveCostAverage(move, stat), eval(f'user.{stat}'),
                    True, -cls.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to statMax percent ratio
                cost *= divi_zero(
                    eval(f'user.{stat}') * 100, eval(f'user.{stat}Max'),
                    True, -cls.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to rate ratio
                cost *= divi_zero(
                    eval(f'user.{stat}'), eval(f'user.{stat}Rate'),
                    True, -cls.moveCostAverage(move, stat) * 2)

                totalCost += cost

        logger.debug(
            f'Returned non-weighted cost of {move} at {cost}')
        return totalCost

    def analyseMoveCostValueWeighted(self, user, move, stats=None):
        """Return a number based on the user, algorithmic cost, and affect
the total by the calculated weight of each cost.
user - The Fighter using the move.
move - The move to analyse.
stats - An iterable of stats to check. If None, defaults to user.allStats."""
        if stats is None:
            stats = user.allStats

        totalCost = 0

        for stat in stats:
            if f'{stat}Cost' in move:
                # If the move explictly states a cost of 0, skip calculations
                if move[f'{stat}Cost'] == 0:
                    continue
                # If user cannot ever pay for the stat, return False
                if isinstance(move[f'{stat}Cost'], Bound):
                    if eval(f'user.{stat}Max') < move[f'{stat}Cost'].left:
                        logger.debug(f"""\
Returned False for {stat} in {move};
user maximum {stat} is {eval(f'user.{stat}Max')}, and minimum move cost \
({move[f'{stat}Cost'].__class__.__name__}) is move[f'{stat}Cost'].left""")
                        return False
                elif eval(f'user.{stat}Max') < move[f'{stat}Cost']:
                    logger.debug(f"""\
Returned False for {stat} in {move};
user maximum {stat} is {eval(f'user.{stat}Max')}, and minimum move cost \
({move[f'{stat}Cost'].__class__.__name__}) is move[f'{stat}Cost']""")
                    return False

                # Cost starts at average move stat cost to stat ratio
                # If the result is 0, use 100 times the average cost
                cost = divi_zero(
                    -self.moveCostAverage(move, stat), eval(f'user.{stat}'),
                    True, -self.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat * 100 to statMax percent ratio
                # If the result is 0, multiply instead
                # by 100 times the average cost
                cost *= divi_zero(
                    eval(f'user.{stat}') * 100, eval(f'user.{stat}Max'),
                    True, -self.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to rate ratio porportional to
                # the amount of stat used
                # If the result is 0, multiply instead
                # by 2 times the average cost
                cost *= divi_zero(
                    eval(f'user.{stat}'), eval(f'user.{stat}Rate'),
                    True, (
                        -self.moveCostAverage(move, stat) * 2
                        * (1 - eval(f'user.{stat}')
                           / eval(f'user.{stat}Max')
                        )
                    )
                ) + 1

                logger.debug(
                    f'Calculated non-weighted {stat} cost of {move} at {cost}')

                # Multiply cost by weight
                cost *= self.analyseValueWeighted(user, cost, stat)

                totalCost += cost

        logger.debug(f'Returned weighted total cost of {move} at {totalCost}')
        return totalCost

    @classmethod
    def analyseLowestCostingMove(cls, user, moves=None):
        """Analyses and determines the cheapest move to use."""
        if moves is None:
            moves = user.availableMoves()
        move = cls.returnNoneMove(user)
        cost = None
        for m in moves:
            mCost = cls.analyseMoveCostValue(user, m)
            if mCost is False:
                # False = Unusable
                continue
            # Else if there is no move/cost, replace with new move
            # Should trigger only at the start
            if move['name'] == 'None' or cost is None:
                move, cost = m, int(mCost)
            # If current move cost is lower than current move cost
            elif mCost < cost:
                move, cost = m, int(mCost)

        return move

    @classmethod
    def noMove(cls, user):
        move = user.findMove({'name': 'None'})
        if isinstance(move, Move):
            return move
        else:
            return BoolDetailed(
                False, 'NoneNotAvailable', f'{user} has no None move')

    def analyseLowestCostingMoveWeighted(self, user, moves=None):
        """Analyses and determines the cheapest move to use with AI weights."""
        if moves is None:
            moves = user.availableMoves()
        move = self.returnNoneMove(user)
        cost = None
        for m in moves:
            mCost = self.analyseMoveCostValueWeighted(user, m)
            if mCost is False:
                # False means move is unusable for the user
                continue
            # Else if there is no move/cost, replace with new move
            # Should trigger only for the first accepted move
            if move['name'] == 'None' or cost is None:
                move, cost = m, int(mCost)
            # If current move cost is lower than current move cost
            elif mCost < cost:
                move, cost = m, int(mCost)

        return move

    @classmethod
    def returnNoneMove(cls, user):
        """Returns the None move if available or otherwise a random move."""
        move = cls.noMove(user)
        if isinstance(move, Move):
            return move
        else:
            return random.choice(user.availableMoves())

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        moves = user.availableMoves()

        # Randomly choose a move and test if it's likely to work
        if len(moves) == 0:
            # No moves to use
            return self.returnNoneMove(user)
        for _ in range(GAME_AI_ANALYSE_MOVE_RANDOM_TIMES):
            # If no moves left from popping, trigger for-else statement
            if (len_moves_forloop := len(moves)) == 0:
                continue
            move = moves.pop(random.randint(0, len_moves_forloop - 1))
            # Skip None move
            if move['name'] == 'None':
                continue
            # Use move if possible
            if self.analyseMoveCostBoolean(user, move):
                logger.debug(f'{self} randomly picked {move}')
                break
            continue
        else:
            # Finding lowest costing move should be a last resort
            # Lowest costing move is typically the weakest, and if it's
            # possible to use a stronger attack, that should be used
            move = self.analyseLowestCostingMoveWeighted(user, moves)

            # If move is still unlikely to work (<50% average cost), do nothing
            if move is not None:
                if not self.analyseMoveCostBoolean(user, move):
                    move = self.returnNoneMove(user)

        return move

    def avgMoveValuesWeighted(self, user, move, keyFormat):
        """Calculates the average value for each stat in a set of key values
found by move.averageValues(keySubstring), scales them by the internal
AI data values, and returns the sum.
Variables provided for keyFormat:
    stat - The current stat being iterated through
Example usage: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')"""
        total = 0
        for stat in user.allStats:
            key = eval("f'''" + keyFormat + "'''")
            if key in move:
                # Obtain value, and get average if it is a Bound
                value = move[key]
                if isinstance(value, Bound):
                    value = value.average()
                total += value * self.data[f'{stat}ValueBias']

        return total

    def analyseValueWeighted(self, user, value, stat):
        """Calculates the average value for each stat in a set of key values
found by move.averageValues(keySubstring), scales them by the internal
AI data values modified by an algorithm, and returns the value.
user - The user receiving this value.
value - The value being modified.
stat - The stat of the value. Used in algorithm to decide computations."""
        if stat == 'hp':
            hp, hpMax = user.hp, user.hpMax
            hpRatio = (1 - hp / hpMax) * 100
            # Ratio Graph
            # 25.6                #
            #                    #
            #                   #
            #                  #
            #                 #
            #               #
            #            #
            #       #
            #1# # # # # # # # # # # max - stat
            weight = divi_zero(10, hpMax * (hpRatio / 25) ** 4) + 1
            weight *= self.data[f'{stat}ValueBias']
            logger.debug(
                f"{value} is of stat 'hp', multiplying by {weight:05f}")

            newValue = value * weight
        elif stat == 'st':
            st, stMax = user.st, user.stMax
            stRatio = (1 - st / stMax) * 100
            # Ratio Graph
            # 4.85                #
            #                    #
            #                   #
            #                 #
            #               #
            #             #
            #          #
            #     #
            #1# # # # # # # # # # # max - stat
            weight = divi_zero(10, stMax * (stRatio / 25) ** 2.8) + 1
            weight *= self.data[f'{stat}ValueBias']
            logger.debug(
                f"{value} is of stat 'st', multiplying by {weight:05f}")

            newValue = value * weight
        elif stat == 'mp':
            mp, mpMax = user.mp, user.mpMax
            mpRatio = (1 - mp / mpMax) * 100
            # Ratio Graph
            # 4.85                #
            #                    #
            #                   #
            #                 #
            #               #
            #             #
            #          #
            #     #
            #1# # # # # # # # # # # max - stat
            weight = divi_zero(10, mpMax * (mpRatio / 25) ** 2.8) + 1
            weight *= self.data[f'{stat}ValueBias']
            logger.debug(
                f"{value} is of stat 'mp', multiplying by {weight:05f}")

            newValue = value * weight
        else:
            newValue = value * self.data[f'{stat}ValueBias']

        logger.debug(
            f'Analysed value {value} of stat {stat!r} '
            f'for {user.decoloredName}, returning {newValue}')
        return newValue

    def analyseMoveValuesWeighted(self, user, move, keyFormat):
        """Calculates the average value for each stat in a set of key values
found by move.averageValues(keySubstring), scales them by the internal
AI data values modified by an algorithm, and returns the sum.
Variables provided for keyFormat:
    stat - The current stat being iterated through
Example usage: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')"""
        total = 0
        for stat in user.allStats:
            key = eval("f'''" + keyFormat + "'''")
            if key in move:
                # Obtain value, and get average if it is a Bound
                value = move[key]
                if isinstance(value, Bound):
                    value = value.average()
                total += self.analyseValueWeighted(user, value, stat)

        logger.debug(
            f'Analysed weighted values for {user.decoloredName} '
            f'against "{move}", returning a total of {total}')
        return total

    def analyseCounter(self, user, move):
        """Select a user counter by weighing each counter based on the move's
data. Any counter weights within the highest weight by a margin of
self.data['counterSelctionMargin'] will be a potential counter.
Currently considers:
    Average normal values (not countered)
    Chance of counter succeeding
    Average counter values
    Average failed counter values
    Average failed critical counter values
        Chance of critical
    Internal data"""
        logger.debug(f'{self}: Analysing counter for '
                     f'{user.decoloredName} against "{move}".')

        # Generate counter from previous calculated weights if available
        if id(move) in self.data['counterWeightData']:
            data = self.data['counterWeightData'][id(move)]
            # counters = data  # for reusing data in calculations
            # If data is a tuple of counters and weights, parse and return
            # biased choice
            if isinstance(data, dict):
                counterSelection = list(data.keys())
                counterWeights = list(data.values())
                randomCounter = random.choices(
                    population=counterSelection,
                    weights=counterWeights,
                    k=1)[0]
                logger.debug(f"""{self} has previous data on {move},
with counters {counterSelection} and respective weights {counterWeights}.
Picked counter {randomCounter!r}""")
                return randomCounter
            else:
                logger.debug(
                    f'{self} has previous data on {move}, using {data!r}')
                return data
        # Create score for all counters
        else:
            counters = collections.OrderedDict({
                counter: 0 for counter in user.counters if counter != 'none'})

        normalDamage = self.analyseMoveValuesWeighted(
            user, move, '{stat}Value')
        criticalDamage = self.analyseMoveValuesWeighted(
            user, move, 'critical{stat.upper()}Value')

        logger.debug(
            f'Normal Damage: {normalDamage}, '
            f'Critical Damage: {criticalDamage}')

        totals = dict.fromkeys(
            ['cCritChance', 'cChance', 'cDamage', 'cFailDamage',
             'cFailCritDamage', 'c_damage_reduction', 'c_fail', 'c_fail_crit'],
            0)
        for counter in counters:
            criticalChance = move.values['criticalChance']
            counterChance = move.values.get(f'{counter}Chance', 0)
            counterDamage = self.analyseMoveValuesWeighted(
                user, move, counter + '{stat.upper()}Value')
            counterFailDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'Fail{stat.upper()}Value')
            counterFailCritDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'FailCritical{stat.upper()}Value')

            # Generate damage reduction for use in totals and avg
            counter_damage_reduction = -(normalDamage - counterDamage)
            # Increase confidence of using counters when low on health
            counter_damage_reduction *= divi_zero(
                user.hpMax - user.hp, 25)
            # Decrease score if the the counter has high negative
            # consequences for failing, porportional to the chance of
            # the move failing
            counter_fail_consequences = (
                - abs(counterFailDamage - counterDamage)
                * (100 - counterChance)
                / 100
            )
            counters[counter] += counter_fail_consequences
            # Decrease score if the the counter has high negative
            # consequences for failing with critical, porportional to
            # the chance of the move failing and the chance of critical
            counter_fail_crit_consequences = (
                - abs(counterFailCritDamage - counterDamage)
                * (100 - counterChance)
                * criticalChance
                / 10000
            )
            counters[counter] += counter_fail_crit_consequences

            logger.debug(
                f'{counter}: '
                f'Counter Damage: {counterDamage}, '
                f'Counter Fail Damage: {counterFailDamage}'
            )

            totals['cChance'] += counterChance
            totals['cCritChance'] += criticalChance
            totals['cDamage'] += counterDamage
            totals['cFailDamage'] += counterFailDamage
            totals['cFailCritDamage'] += counterFailCritDamage
            totals['c_damage_reduction'] += counter_damage_reduction
            totals['c_fail'] += counter_fail_consequences
            totals['c_fail_crit'] += counter_fail_crit_consequences

        logger.debug(f'Total values:\n{pprint.pformat(totals)}')

        len_counters = len(counters)
        avg = {k: v / len_counters
               for k, v in totals.items()}

        logger.debug(f'Average values:\n{pprint.pformat(avg)}')

        for counter in counters:
            criticalChance = move.values['criticalChance']
            counterChance = move.values.get(f'{counter}Chance', 0)
            counterDamage = self.analyseMoveValuesWeighted(
                user, move, counter + '{stat.upper()}Value')
            counterFailDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'Fail{stat.upper()}Value')
            counterFailCritDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'FailCritical{stat.upper()}Value')

            # Increase score by average damage reduction relative to
            # other counters, porportional to the chance of failing and
            # porportional to the difference between its own chance
            # and exclusive average counter chance
            average_damage_exclusive = \
                divi_zero(totals['cDamage'] - counterDamage,
                          len_counters - 1)
            average_chance_exclusive = divi_zero(
                totals['cChance'] - counterChance,
                len_counters - 1
            ) / 100
            # Relative to other counters
            average_damage_reduction = -(
                average_damage_exclusive - counterDamage)
            # Porportional to the chance of failing that is porportional
            # to the other counter chances
            chance_porportional = (100 - counterChance) / 100
            chance_porportional *= (
                average_chance_exclusive
                - (100 - counterChance)
                / 100
            )
            average_damage_reduction *= chance_porportional
            counters[counter] += average_damage_reduction

        if 'none' in user.counters:
            counters['none'] = 0
            counters.move_to_end('none', last=False)
            counters['none'] -= avg['c_damage_reduction']
            # Decrease score if not countering has high negative consequences
            # for failing, porportional to the chance of critical and
            # porportional to other counter chances
            none_fail_crit_consequences = (
                - abs(criticalDamage - normalDamage) \
                * move['criticalChance'] / 100 \
                * (100 - avg['cCritChance']) / 100
            )
            counters['none'] += none_fail_crit_consequences

        # Get the counter with the highest score
        bestCounter = max(
            [(k, v) for k, v in counters.items()],
            key=lambda x: x[1])
        # Randomly choose a counter within acceptable margins, weighted
        # by their scores
        counterSelection = [
            k for k, v in counters.items()
            if bestCounter[1] - v <= self.data['counterSelectionMargin']]
        # If only one counter is selected, return it
        if len(counterSelection) == 1:
            counterSelection = counterSelection[0]
            logger.debug(
                f"""{self} determined that {bestCounter[0]!r} is the \
best counter for "{move}" (margin={self.data['counterSelectionMargin']}).
Calculated scores:
{pprint.pformat(dict(counters))}""")
            # self.data['counterWeightData'][id(move)] = counterSelection
            return counterSelection

        counterWeights = [counters[k] for k in counterSelection]
        counterWeights = self.make_weights_relative(counterWeights)

        # # Store counter weights
        # self.data['counterWeightData'][id(move)] = {
        #     counter: weight
        #     for counter, weight in zip(counters, counterWeights)}
        # Choose counter
        randomCounter = random.choices(
            population=counterSelection,
            weights=counterWeights,
            k=1)[0]

        debugWeight = '\n'.join(
            f'({counter!r}: {weight})'
            for counter, weight in zip(counters, counterWeights))
        logger.debug(
            f"""{self} determined that {bestCounter[0]!r} is the best counter \
for "{move}", \
and the acceptable counters are {counterSelection} \
(margin={self.data['counterSelectionMargin']}).
Picked counter {randomCounter!r}
Calculated scores:
{pprint.pformat(dict(counters))}
Calculated weights:
{debugWeight}""")
        return randomCounter

    def analyseMoveReceive(self, user, move, sender=None, info=None):
        """Analyses the results of a received move."""
        self.data['lastTargetMove'] = move

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return self.analyseCounter(user, move)

    @staticmethod
    def make_weights_relative(iterable):
        # If a weight is negative, compensate by increasing all weights
        # and making the lowest weight equal 1, required to properly make
        # relative weights
        lowestWeight = min(iterable)
        if lowestWeight <= 0:
            iterable = [
                w - lowestWeight * 2 + 1
                for w in iterable]
        # Make weights relative
        weightSum = sum(iterable)
        weights = [
            divi_zero(w, weightSum) for w in iterable]
        return weights


class FighterAIDummy(FighterAIGeneric):
    """Fighter AI - Will not attack or counter."""

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        return self.returnNoneMove(user)

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return 'none'


class FighterAIMimic(FighterAIGeneric):
    """Fighter AI - Will not attack or counter."""

    def analyseRandomMove(self, user, target):
        """Analyses and returns a random move to use."""
        moves = user.availableMoves()

        # Randomly choose a move and test if it's likely to work
        if len(moves) == 0:
            # No moves to use
            return self.returnNoneMove(user)
        for _ in range(GAME_AI_ANALYSE_MOVE_RANDOM_TIMES):
            # If no moves left from popping, trigger for-else statement
            if (len_moves_forloop := len(moves)) == 0:
                continue
            move = moves.pop(random.randint(0, len_moves_forloop - 1))
            # Use move if possible
            if self.analyseMoveCostBoolean(user, move):
                logger.debug(f'{self} randomly picked {move}')
                break
            continue
        else:
            # Finding lowest costing move should be a last resort
            # Lowest costing move is typically the weakest, and if it's
            # possible to use a stronger attack, that should be used
            move = self.analyseLowestCostingMoveWeighted(user, moves)

            # If move is still unlikely to work (<50% average cost), do nothing
            if move is not None:
                if not self.analyseMoveCostBoolean(user, move):
                    move = self.returnNoneMove(user)

        return move

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        move = self.data['lastTargetMove']

        if move['name'] == 'None':
            # Target didn't move; pick a random move
            return self.analyseRandomMove(user, target)
        elif move not in (moves := user.availableMoves()):
            # Move is not available; pick a random move
            return self.analyseRandomMove(user, target)
        elif not self.analyseMoveCostBoolean(user, move):
            # Move is unlikely to work; pick a random move
            return self.analyseRandomMove(user, target)
        else:
            # Reuse the target's move
            return move


class FighterAISwordFirst(FighterAIGeneric):
    """Fighter AI - Uses the dominant strategy found in the early stages of
development."""

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        # Fire Ball as a panic attack
        moveFireBall = user.findMove({'name': 'Fire Ball'}, raiseIfFail=True)
        costFireBall = int(
            moveFireBall['mpCost'].right
            * user.battle_env.base_energies_cost_multiplier_percent
            * user.battle_env.base_energy_cost_mana_multiplier_percent
            / 10000)
        if user.hp <= 10 and user.mp >= -costFireBall and target.hp >= 20:
            return moveFireBall
        # Jab to finish off target if very low
        else:
            moveJab = user.findMove({'name': 'Jab'}, raiseIfFail=True)
            costJab = int(
                moveJab['stCost'].average()
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if target.hp <= 10 and user.st >= -costJab:
            return moveJab
        # Use sword if more than enough stamina available
        else:
            moveSword = user.findMove({'name': 'Sword'}, raiseIfFail=True)
            costSword = int(
                moveSword['stCost'].right
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if user.st >= -costSword:
            return moveSword
        # Use Kick as medium attack
        else:
            moveKick = user.findMove({'name': 'Kick'}, raiseIfFail=True)
            costKick = int(
                moveKick['stCost'].average()
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if user.st >= -costKick:
            return moveKick
        # Fire Ball to finish off target if low
        elif target.hp <= 20 and user.mp >= -costFireBall:
            return moveFireBall
        # Jab as last resort if possible
        elif user.st >= -costJab:
            return moveJab
        # Do nothing
        elif user.mp >= costFireBall:
            return moveFireBall
        else:
            return self.returnNoneMove(user)


class FighterAIFootsies(FighterAIGeneric):
    """Fighter AI - Designed for fighting in the Footsies gamemode."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        brain = goapy.Planner(
            'target_can_attack',
            'target_has_died',
            'has_energy',
            'low_on_health'
        )
        brain.set_goal_state(
            target_can_attack=False,
            target_has_died=True,
            low_on_health=False
        )

        actions = goapy.Action_List()
        actions.add_condition(
            'attack',
            has_energy=True
        )
        actions.add_reaction(
            'attack',
            target_has_died=True
        )
        actions.add_condition(
            'get_energy',
            has_energy=False
        )
        actions.add_reaction(
            'get_energy',
            has_energy=True
        )
        actions.add_condition(
            'retreat',
            target_can_attack=True
        )
        actions.add_reaction(
            'retreat',
            target_can_attack=False
        )
        actions.add_condition(
            'heal',
            low_on_health=True
        )
        actions.add_reaction(
            'heal',
            low_on_health=False
        )
        actions.set_weight('attack', 100)
        actions.set_weight('get_energy', 15)
        actions.set_weight('retreat', 100)
        actions.set_weight('heal', 100)

        brain.set_action_list(actions)

        self.brain = brain
        self.brain_actions = actions

    @classmethod
    def get_attacks(cls, user):
        attacks = []
        for move in user.moves:
            if 'hpValue' in move and Bound.callAverage(move['hpValue']) < 0:
                attacks.append(move)
        return attacks

    def get_available_attacks(self, user):
        """Get the user's attacks that the user has enough energy for.

        The returned list will be sorted by strongest move.

        """
        attacks = self.get_attacks(user)
        usable = []
        for move in attacks:
            if self.analyseMoveCostBoolean(user, move):
                usable.append(move)

        def sort_key(move):
            # Sort moves by their damage
            # NOTE: Moves that damage will have negative value, not positive
            return self.analyseMoveValuesWeighted(user, move, '{stat}Value')

        return sorted(usable, key=sort_key)

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        # Provide information to brain
        attacks = self.get_available_attacks(user)

        energy_percent = int(user.st / user.stMax * 100)
        target_health_float = target.hp / target.hpMax
        target_health_scalar = 0.3 + (target_health_float * 0.7)
        attack_weight = int((100 - energy_percent)
                            * target_health_scalar // 2)
        self.brain_actions.set_weight(
            'attack', attack_weight
        )
        self.brain_actions.set_weight(
            'get_energy', attack_weight
        )

        target_attacks = self.get_available_attacks(target)
        target_can_attack = bool(target_attacks)
        target_energy_float = target.st / target.stMax
        retreat_weight = 100 - int(target_energy_float * 100) + 15
        self.brain_actions.set_weight(
            'retreat', retreat_weight
        )

        has_energy = False
        if attacks and attack_weight < retreat_weight:
            has_energy = True

        low_on_health = user.hp < user.hpMax
        health_percent = int(user.hp / user.hpMax * 100)
        heal_weight = health_percent * max(1 - target_energy_float, 0.4)
        self.brain_actions.set_weight('heal', health_percent)

        self.brain.set_start_state(
            target_can_attack=target_can_attack,
            target_has_died=False,
            has_energy=has_energy,
            low_on_health=low_on_health
        )

        # Debug: displays weights
        logger.debug(
            'attack, retreat, and heal weights: {}'.format(
                ', '.join(
                    map(str, (attack_weight, retreat_weight, heal_weight))
                )
            )
        )

        # Get action
        plan = self.brain.calculate()
        action = plan[0]['name'] if plan else None

        # Debug: displays the calculated path and the costs
        debug_msg = []
        for a in plan:
            debug_msg.append(f"{a['name']}: {a['g']}")
        debug_msg = '\n'.join(debug_msg)
        logger.debug('Plan:\n{}'.format(debug_msg))
        print(debug_msg)

        # Execute action
        if action == 'attack':
            # Use strongest attack needed
            return attacks[0]
        elif action == 'get_energy':
            return user.findMove({'name': 'Advance'}, raiseIfFail=True)
        elif action == 'heal':
            return user.findMove({'name': 'Hold'}, raiseIfFail=True)
        elif action == 'retreat':
            return user.findMove({'name': 'Retreat'}, raiseIfFail=True)
        else:
            return self.returnNoneMove(user)
            # raise RuntimeError(
            #     f'unknown action in FighterAIFootsies: {action!r}')

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return 'none'


moveTemplate = [
    Move({
        'name': '',
        'moveTypes': ([MTPhysical],),
        'description': '',
        'skillRequired': ([],),
        'itemRequired': ([
            {
                'name': '',
                'count': 0
            },
            ],),
        'moveMessage': """\
{sender} attacks {target} for {move:hp neg} damage, costed {move:stC neg}""",

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
                'applyMessage': '{self} {hpValue} {hp.ext_full}',
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
{move:hpBlock neg}""",
        'blockFailMessage': """\
{move:hpBlockF neg}""",

        'evadeChance': 0,
        'evadeHPValue': 0,
        'evadeSTValue': 0,
        'evadeMPValue': 0,
        'evadeFailHPValue': Bound(-0, -0),
        'evadeFailSTValue': Bound(-0, -0),
        'evadeFailMPValue': Bound(-0, -0),
        'evadeMessage': """\
{move:hpEvade neg}""",
        'evadeFailMessage': """\
{move:hpEvadeF neg}""",

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
{move:hpCrit neg}""",
        'fastCriticalMessage': """\
{move:hpCrit neg}""",
        'blockFailCriticalMessage': """\
{move:hpBlockFCrit neg}""",
        'evadeFailCriticalMessage': """\
{move:hpEvadeFCrit neg}""",

        'failureChance': 0,
        'failureHPValue': Bound(-0, -0),
        'failureSTValue': Bound(-0, -0),
        'failureMPValue': Bound(-0, -0),
        'failureMessage': """\
{move:hpF neg}""",
        }
    ),
]
noneMove = Move({
    'name': 'None',
    'description': 'Do nothing.'
})
moveList = [
    noneMove,

    Move({
        'name': 'Kick',
        'moveTypes': ([MTPhysical],),
        'description': """A simple kick.
A basic medium-damage attack, with a 1:2 damage to cost ratio.""",
        'skillRequired': ([SKAcrobatics(1)],),
        'moveMessage': """\
{sender} kicks {target} for {move:hp neg} damage!""",

        'hpValue': Bound(-10, -15),
        'stCost': Bound(-20, -30),

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being kicked.',

                'target': 'target',
                'chances': ((15, 'uncountered'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 40,
        'fastMessage': """\
{sender} swiftly kicks {target} for {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-6, -9),
        'blockFailHPValue': Bound(-10, -20),
        'blockMessage': """\
{sender} attempts to kick {target} but {target} blocks it, \
taking {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} attempts to kick {target} and {target} fails to block it, \
taking {move:hpBlockF neg} damage!""",

        'evadeChance': 50,
        'evadeFailHPValue': Bound(-15, -25),
        'evadeMessage': """\
{sender} attempts to kick {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} attempts to kick {target} and {target} fails to evade it, \
taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-20, -30),
        'blockFailCriticalHPValue': Bound(-20, -40),
        'evadeFailCriticalHPValue': Bound(-30, -50),
        'criticalMessage': """\
A headshot!
{sender} kicks {target} for {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
A headshot!
{sender} swiftly kicks {target} for {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
A headshot!
{sender} attempts to kick {target} and {target} fails to block it, \
taking {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
A headshot!
{sender} attempts to kick {target} and {target} fails to evade it, \
taking {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 20,
        'failureHPValue': Bound(-5, -10),
        'failureMessage': """\
{sender} tries to kick {target} but falls on the ground \
and loses {move:hpF neg} {hp.ext_full}.""",
        }
    ),
    Move({
        'name': 'Jab',
        'moveTypes': ([MTPhysical],),
        'description': """A quick punch.
An easy low-damage attack, with a low chance of countering.""",
        'moveMessage': """\
{sender} jabs {target} for {move:hp neg} damage!""",

        'hpValue': Bound(-5, -10),
        'stCost': Bound(-15, -20),

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being punched.',

                'target': 'target',
                'chances': ((10, 'uncountered'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 70,
        'fastMessage': """\
{sender} swiftly jabs {target} for {move:hp neg} damage!""",

        'blockChance': 80,
        'blockHPValue': Bound(-1, -2),
        'blockFailHPValue': Bound(-8, -13),
        'blockMessage': """\
{sender} attempts to jab {target} but {target} blocks it, \
taking {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} attempts to jab {target} and {target} fails to block it, \
taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': Bound(-10, -20),
        'evadeMessage': """\
{sender} attempts to jab {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} attempts to jab {target} and {target} fails to evade it, \
taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 20,
        'criticalHPValue': Bound(-10, -20),
        'blockFailCriticalHPValue': Bound(-15, -25),
        'evadeFailCriticalHPValue': Bound(-20, -30),
        'criticalMessage': """\
A headshot!
{sender} jabs {target} for {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
A headshot!
{sender} swiftly jabs {target} for {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
A headshot!
{sender} attempts to jab {target} and {target} fails to block it, \
taking {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
A headshot!
{sender} attempts to jab {target} and {target} fails to evade it, \
taking {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 8,
        'failureMessage': """\
{sender} tries to jab {target} but misses.""",
        }
    ),
    Move({
        'name': 'Sword',
        'moveTypes': ([MTPhysical],),
        'description': """Slash with a sword.
A strong weapon with high {st.ext_full} costs but a slightly better damage
to cost ratio (1:2), and a small chance to deal a critical,
potentially one-shot blow.""",
        'itemRequired': ([{'name': 'Sword'}, ],),
        'moveMessage': """\
{sender} strikes {target} with a sword for {move:hp neg} damage!""",

        'hpValue': Bound(-15, -30),
        'stCost': Bound(-35, -50),

        'effects': [
            StatusEffect({
                'name': 'Bleeding',
                'description': 'Bleeding from a sword wound.',

                'target': 'target',
                'chances': ((30, 'uncountered'),),
                'duration': 3,

                'receiveMessage': '{self} is now bleeding!',
                'applyMessage': '{self} took {-hpValue} bleeding damage!',
                'wearoffMessage': '{self} has stopped bleeding.',

                'hpValue': Bound(-2, -4),
            }),
        ],

        'speed': 20,
        'fastMessage': """\
{sender} quickly strikes {target} with a sword for {move:hp neg} damage!""",

        'blockChance': 0,
        'blockHPValue': Bound(-3, -6),
        'blockFailHPValue': Bound(-20, -35),
        'blockMessage': """\
{sender} attempts to strike {target} with a sword but {target} blocks it, \
taking only {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} attempts to strike {target} with a sword and {target} fails to block,\
 taking {move:hpBlockF neg} damage!""",

        'evadeChance': 50,
        'evadeFailHPValue': Bound(-25, -40),
        'evadeMessage': """\
{sender} attempts to strike {target} with a sword but {target} dodges it!""",
        'evadeFailMessage': """\
{sender} attempts to strike {target} with a sword \
and {target} fails to dodge, taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 3,
        'criticalHPValue': Bound(-75, -150),
        'blockFailCriticalHPValue': Bound(-100, -175),
        'evadeFailCriticalHPValue': Bound(-125, -200),
        'criticalMessage': """\
{sender} pulls a Kingdom Come Deliverance and critically strikes {target} \
with a sword for {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
Too slow!
{sender} pulls a Kingdom Come Deliverance and critically strikes {target} \
with a sword for {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} pulls a Kingdom Come Deliverance and bypasses {target}'s \
block with a sword, critically striking them for \
{move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} pulls a Kingdom Come Deliverance and predicts {target}'s \
dodge, critically striking them for {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 15,
        'failureHPValue': Bound(-15, -30),
        'failureMessage': """\
{sender} tries to strike {target} with a sword but falls on the ground \
and hits themselves for {move:hpF neg} damage.""",
        }
    ),
    Move({
        'name': 'Fire Ball',
        'moveTypes': ([MTMagical],),
        'description': """Summon a fireball.
A standard, medium-damage attack that costs {mp.ext_full}.""",
        'moveMessage': """\
{sender} shoots a ball of fire at {target} for {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'mpCost': Bound(-25, -40),

        'effects': [
            StatusEffect({
                'name': 'Fire',
                'description': "You're on fire!",

                'target': 'target',
                'chances': ((30, 'uncountered'), (30, 'failure')),
                'duration': 2,

                'receiveMessage': '{self} is on fire!',
                'applyMessage': '{self} took {-hpValue} damage from fire!',
                'wearoffMessage': '{self} is no longer on fire.',

                'hpValue': Bound(-3, -6),
            }),
        ],

        'speed': 40,
        'fastMessage': """\
{sender} shoots a FAST ball of fire at {target} for {move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': Bound(-5, -15),
        'blockFailHPValue': Bound(-10, -20),
        'blockMessage': """\
{sender} shoots a ball of fire at {target} but {target} blocks it, taking \
{move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} shoots a ball of fire at {target} and {target} fails to block it, \
taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': Bound(-15, -30),
        'evadeMessage': """\
{sender} shoots a ball of fire at {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} shoots a ball of fire at {target} and {target} fails to evade it, \
taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 20,
        'criticalHPValue': Bound(-20, -40),
        'blockFailCriticalHPValue': Bound(-20, -40),
        'evadeFailCriticalHPValue': Bound(-30, -60),
        'criticalMessage': """\
{sender} shoots a DEADLY ball of fire at {target} for \
{move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} shoots a FAST AND DEADLY ball of fire at {target} \
for {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} shoots a DEADLY ball of fire at {target} and {target} fails to block \
it, taking {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} shoots a DEADLY ball of fire at {target} \
and {target} fails to evade it, taking {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 20,
        'failureHPValue': Bound(-15, -20),
        'failureMessage': """\
{sender} tries to shoot a ball of fire but it explodes in their face for \
{move:hpF neg} damage!""",
        },
    ),
    Move({
        'name': 'Slam',
        'moveTypes': ([MTPhysical],),
        'description': """Slam down on your foe.
A move with high variability in damage output but with luck,
offers 25 damage at 40 {st.ext_full} cost instead of 50 (1:2 ratio).""",
        'skillRequired': ([SKAcrobatics(1)],),
        'moveMessage': """\
{sender} jumps above {target} and slams down for {move:hp neg} damage!""",

        'hpValue': Bound(-15, -25),
        'stCost': Bound(-30, -40),

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being slammed on.',

                'target': 'target',
                'chances': ((30, 'uncountered'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 30,
        'fastMessage': """\
{sender} quickly jumps above {target} and slams down for \
{move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-8, -15),
        'blockFailHPValue': Bound(-20, -25),
        'blockMessage': """\
{sender} tries to slam down on {target} but {target} blocks it, \
taking only {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} tries to slam down on {target} and {target} fails to block it, \
taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': Bound(-25, -40),
        'evadeMessage': """\
{sender} tries to slam down on {target} but {target} dodges it!""",
        'evadeFailMessage': """\
{sender} tries to slam down on {target} and {target} fails to dodge it, \
taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-23, -38),
        'blockFailCriticalHPValue': Bound(-30, -38),
        'evadeFailCriticalHPValue': Bound(-38, -60),
        'criticalMessage': """\
{sender} slams down on {target} for {move:hpCrit neg} critical damage!""",
        'fastCriticalMessage': """\
{sender} quickly slams down on {target} for \
{move:hpCrit neg} critical damage!""",
        'blockFailCriticalMessage': """\
{sender} tries to slam down on {target} and {target} fails to block it, \
taking {move:hpBlockFCrit neg} critical damage!""",
        'evadeFailCriticalMessage': """\
{sender} tries to slam down on {target} and {target} fails to dodge it, \
taking {move:hpEvadeFCrit neg} critical damage!""",

        'failureChance': 15,
        'failureHPValue': Bound(-5, -10),
        'failureMessage': """\
{sender} tries to slam down on {target} but hits the ground, \
losing {move:hpF neg} {hp.ext_full}!""",
        }
    ),
    Move({
        'name': 'Knife',
        'moveTypes': ([MTPhysical],),
        'description': """Slash with a knife.
A medium-damage weapon that is dangerous to counter, and has a
relatively high critical chance.""",
        'skillRequired': ([SKKnifeHandling(1)],),
        'itemRequired': ([
            {'name': 'Knife'},
            ],),
        'moveMessage': """\
{sender} slashes {target} with a knife, dealing {move:hp neg} damage!""",

        'hpValue': Bound(-15, -20),
        'stCost': Bound(-30, -35),

        'effects': [
            StatusEffect({
                'name': 'Bleeding',
                'description': 'Bleeding from a knife wound.',

                'target': 'target',
                'chances': ((20, 'uncountered'),),
                'duration': 2,

                'receiveMessage': '{self} is now bleeding!',
                'applyMessage': '{self} took {-hpValue} bleeding damage!',
                'wearoffMessage': '{self} has stopped bleeding.',

                'hpValue': -2,
            }),
        ],

        'speed': 30,
        'fastMessage': """\
{sender} quickly slashes {target} with a knife, dealing \
{move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': Bound(-6, -12),
        'blockFailHPValue': Bound(-15, -25),
        'blockMessage': """\
{sender} tries slashing {target} with a knife but {target} blocks, \
dealing only {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} slashes {target} with a knife and {target} failed to block, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 45,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} tries slashing {target} with a knife but {target} dodged it!""",
        'evadeFailMessage': """\
{sender} slashes {target} with a knife and {target} failed to dodge, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 20,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-25, -35),
        'evadeFailCriticalHPValue': Bound(-30, -40),
        'criticalMessage': """\
A critical!
{sender} slashes {target} with a knife, dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
A critical!
{sender} swiftly slashes {target} with a knife, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
A critical!
{sender} slashes {target} with a knife and {target} failed to block, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
A critical!
{sender} slashes {target} with a knife and {target} failed to dodge, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 10,
        'failureHPValue': Bound(-10, -15),
        'failureMessage': """\
{sender} tries slashing {target} with a knife but hits themself, \
dealing {move:hpF neg} damage.""",
        }
    ),
    Move({
        'name': 'Throw Knife',
        'moveTypes': ([MTPhysical],),
        'description': """Throw a knife.
A medium-damage weapon, boasting a high critical chance,
but requires you to dispose a knife.
It is harder to block than to evade, but failing evasion is worse.""",
        'skillRequired': ([SKKnifeHandling(2)],),
        'itemRequired': ([
            {
                'name': 'Knife',
                'count': 1
            },
            ],),
        'moveMessage': """\
{sender} throws a knife at {target}, dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'stCost': Bound(-25, -30),

        'effects': [
            StatusEffect({
                'name': 'Bleeding',
                'description': 'Bleeding from a knife wound.',

                'target': 'target',
                'chances': ((30, 'uncountered'),),
                'duration': 2,

                'receiveMessage': '{self} is now bleeding!',
                'applyMessage': '{self} took {-hpValue} bleeding damage!',
                'wearoffMessage': '{self} has stopped bleeding.',

                'hpValue': -2,
            }),
        ],

        'speed': 30,
        'fastMessage': """\
{sender} swiftly throws a knife at {target}, dealing {move:hp neg} damage!""",

        'blockChance': 40,
        'blockHPValue': Bound(-6, -12),
        'blockFailHPValue': Bound(-15, -25),
        'blockMessage': """\
{sender} throws a knife at {target} who is blocking, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} throws a knife at {target} and {target} failed to block, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 60,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} throws a knife at {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} throws a knife at {target} and {target} failed to evade, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 30,
        'criticalHPValue': Bound(-20, -30),
        'blockFailCriticalHPValue': Bound(-25, -35),
        'evadeFailCriticalHPValue': Bound(-30, -40),
        'criticalMessage': """\
A critical!
{sender} throws a knife at {target}, dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
A critical!
{sender} swiftly throws a knife at {target}, dealing \
{move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
A critical!
{sender} throws a knife at {target} and {target} failed to block, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
A critical!
{sender} throws a knife at {target} and {target} failed to evade, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 10,
        'failureHPValue': Bound(-10, -15),
        'failureMessage': """\
{sender} tries to throw a knife at {target} but hits themself, \
dealing {move:hpF neg} damage.""",
        }
    ),
    Move({
        'name': 'Longbow',
        'moveTypes': ([MTPhysical],),
        'description': """Fire an arrow with a longbow.
A medium-damage weapon that requires a lot of {st.ext_full}, but will deal
moderate {st.ext_full} damage.""",
        'skillRequired': ([SKBowHandling(1)],),
        'itemRequired': ([
            {'name': 'Longbow'},
            {
                'name': 'Arrow',
                'count': 1
            },
            ],),
        'moveMessage': """\
{sender} shoots an arrow at {target}, dealing {move:hp neg} damage \
and draining {move:st neg} {st.ext_full}!""",

        'hpValue': Bound(-15, -25),
        'stValue': Bound(-15, -25),
        'stCost': Bound(-35, -50),

        'effects': [
            StatusEffect({
                'name': 'Bleeding',
                'description': 'Bleeding from an arrow wound.',

                'target': 'target',
                'chances': ((20, 'uncountered'),),
                'duration': 2,

                'receiveMessage': '{self} is now bleeding!',
                'applyMessage': '{self} took {-hpValue} bleeding damage!',
                'wearoffMessage': '{self} has stopped bleeding.',

                'hpValue': Bound(-2, -4),
            }),
        ],

        'speed': 40,
        'fastMessage': """\
{sender} quickly shoots an arrow at {target}, \
dealing {move:hp neg} damage and draining {move:st neg} {st.ext_full}!""",

        'blockChance': 70,
        'blockHPValue': Bound(-8, -13),
        'blockFailHPValue': Bound(-20, -30),
        'blockFailSTValue': Bound(-10, -20),
        'blockMessage': """\
{sender} shoots an arrow at {target} but {target} blocks it, \
only dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} shoots an arrow at {target} and {target} fails to block it, \
dealing {move:hpBlockF neg} damage and draining \
{move:stBlockF neg} {st.ext_full}!""",

        'evadeChance': 60,
        'evadeFailHPValue': Bound(-15, -30),
        'evadeFailSTValue': Bound(-10, -20),
        'evadeMessage': """\
{sender} shoots an arrow at {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} shoots an arrow at {target} and {target} fails to evade it, \
dealing {move:hpEvadeF neg} damage and draining \
{move:stEvadeF neg} {st.ext_full}!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-30, -40),
        'criticalSTValue': Bound(-10, -30),
        'blockFailCriticalHPValue': Bound(-30, -45),
        'blockFailCriticalSTValue': Bound(-20, -40),
        'evadeFailCriticalHPValue': Bound(-35, -45),
        'evadeFailCriticalSTValue': Bound(-25, -45),
        'criticalMessage': """\
{sender} critically strikes {target} with an arrow, \
dealing {move:hpCrit neg} damage and draining \
{move:stCrit neg} {st.ext_full}!""",
        'fastCriticalMessage': """\
{sender} critically and swiftly strikes {target} with an arrow, \
dealing {move:hpCrit neg} damage and draining \
{move:stCrit neg} {st.ext_full}!""",
        'blockFailCriticalMessage': """\
{target} fails to block and {sender} critically strikes {target} \
with an arrow, dealing {move:hpBlockFCrit neg} damage and \
draining {move:stBlockFCrit neg} {st.ext_full}!""",
        'evadeFailCriticalMessage': """\
{target} fails to evade and {sender} critically strikes {target} \
with an arrow, dealing {move:hpEvadeFCrit neg} damage and \
draining {move:stEvadeFCrit neg} {st.ext_full}!""",

        'failureChance': 20,
        'failureHPValue': Bound(-5, -10),
        'failureSTValue': Bound(-1, -5),
        'failureMessage': """\
{sender} tries to shoot an arrow at {target} but hits themself, \
losing {move:hpF neg} {hp.ext_full} and \
{move:stF neg} {st.ext_full}.""",
        }
    ),
    Move({
        'name': 'Equilibrium',
        'moveTypes': ([MTMagical],),
        'description': """Convert 25 {hp.ext_full} into magicka- {mp.ext_full}.
This move is uncounterable; the opponent cannot stop this process.
there is a 1/10 chance of failing, which takes away both {hp.ext_full}
and {mp.ext_full}.""",

        'hpCost': -25,
        'mpCost': 25,

        'speed': 100,
        'fastMessage': """\
{sender} uses Equilibrium, losing {move:hpC neg} {hp.ext_full} for \
{move:mpC} {mp.ext_full}!""",

        'criticalChance': 0,

        'failureChance': 10,
        'failureHPValue': Bound(-5, -15),
        'failureMPValue': Bound(-10, -25),
        'failureMessage': """\
{sender} tries using Equilibrium but it backfires, making {sender} lose \
{int(move.fmt('hpF neg')) + int(move.fmt('hpC neg'))} {hp.ext_full} \
and {move:mpF neg} {mp.ext_full}.""",
        }
    ),
    Move({
        'name': 'Bobomb',
        'moveTypes': ([MTPhysical],),
        'description': """Throw a bob-omb.
A bob-omb is hefty to throw, but is powerful and hard to evade.""",
        'itemRequired': ([
            {
                'name': 'Bob-omb',
                'count': 1
            },
            ],),
        'moveMessage': """\
{sender} throws a bob-omb at {target} and it explodes, dealing \
{move:hp neg} damage!""",

        'hpValue': Bound(-15, -35),
        'stCost': Bound(-25, -40),

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from a bob-omb explosion.',

                'target': 'target',
                'chances': ((20, 'uncountered'), (20, 'failure')),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 30,
        'fastMessage': """\
{sender} quickly throws a bob-omb at {target} and it explodes, dealing \
{move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-20, -35),
        'blockMessage': """\
{sender} throws a bob-omb at {target} but {target} blocks, dealing \
only {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} throws a bob-omb at {target} and {target} fails to block, dealing \
{move:hpBlockF neg} damage!""",

        'evadeChance': 35,
        'evadeFailHPValue': Bound(-25, -40),
        'evadeMessage': """\
{sender} throws a bob-omb at {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} throws a bob-omb at {target} and {target} fails to evade it, dealing \
{move:hpEvadeF neg} damage!""",

        'criticalChance': 15,
        'criticalHPValue': Bound(-25, -40),
        'blockFailCriticalHPValue': Bound(-25, -40),
        'evadeFailCriticalHPValue': Bound(-30, -45),
        'criticalMessage': """\
{sender} throws a bob-omb at {target} and it explodes right next to them, \
dealing {move:hpCrit neg} critical damage!""",
        'fastCriticalMessage': """\
{sender} quickly throws a bob-omb at {target} and it explodes right \
next to them, dealing {move:hpCrit neg} critical damage!""",
        'blockFailCriticalMessage': """\
{sender} throws a bob-omb right next to {target} and {target} fails to block, \
dealing {move:hpBlockFCrit neg} critical damage!""",
        'evadeFailCriticalMessage': """\
{sender} throws a bob-omb right next to {target} and {target} fails to evade, \
dealing {move:hpEvadeFCrit neg} critical damage!""",

        'failureChance': 6,
        'failureHPValue': Bound(-15, -25),
        'failureMessage': """\
{sender} tries to throw a bob-omb at {target} but the bob-omb explodes next \
to {sender}, dealing {move:hpF neg} damage!""",
        }
    ),
    Move({
        'name': 'Yeet',
        'moveTypes': ([MTPhysical],),
        'description': """Yeet your opponent.
A high-damage attack that puts the target in severe hitstun, \
but requires nearly all {st.ext_full} and {mp.ext_full} to execute.""",
        'moveMessage': """\
{sender} yeets {target}, dealing {move:hp neg} damage!""",

        'hpValue': Bound(-30, -49),
        'stCost': Bound(-90, -100),
        'mpCost': Bound(-90, -100),

        'effects': [
            StatusEffect({
                'name': 'Severe Hitstun',
                'description': 'Stun from being yeeted.',

                'target': 'target',
                'chances': ((100, 'uncountered'),),
                'duration': 2,

                'receiveMessage': '{self} is in severe hitstun!',
                'wearoffMessage': "{self}'s severe hitstun has worn off.",

                'noMove': '{self} cannot move due to severe hitstun!',
                'noCounter': '{self} cannot counter due to severe hitstun!',
            }),
        ],

        'speed': 10,
        'fastMessage': """\
{sender} quickly yeets {target}, dealing {move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': Bound(-25, -30),
        'blockFailHPValue': Bound(-35, -49),
        'blockMessage': """\
{sender} tries to yeet {target} but {target} blocks, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{target} fails to block and {sender} yeets {target}, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 45,
        'evadeFailHPValue': Bound(-40, -49),
        'evadeMessage': """\
{sender} tries to yeet {target} but {target} evades it!""",
        'evadeFailMessage': """\
{target} fails to evade {sender} and {sender} yeets {target}, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 5,
        'criticalHPValue': Bound(-50, -60),
        'blockFailCriticalHPValue': Bound(-50, -65),
        'evadeFailCriticalHPValue': Bound(-55, -65),
        'criticalMessage': """\
A critical!
{sender} SUPER yeets {target}, dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
A critical
{sender} quickly SUPER yeets {target}, dealing {move:hp neg} damage!!""",
        'blockFailCriticalMessage': """\
A critical!
{target} fails to block and {sender} SUPER yeets {target}, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
A critical!
{target} fails to evade {sender} and {sender} SUPER yeets {target}, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 10,
        'failureHPValue': Bound(-10, -15),
        'failureMessage': """\
{sender} tries to yeet {target} but fails, losing \
{move:hpF neg} {hp.ext_full}.""",
        }
    ),

    Move({
        'name': 'Star Spit',
        'moveTypes': ([MTKirby],),
        'description': 'Spit your opponent as a star.',
        'moveMessage': """\
{sender} inhales {target} and spits them out as a star, dealing \
{move:hp neg} damage!""",

        'hpValue': Bound(-15, -20),
        'stCost': Bound(-25, -30),
        'mpCost': Bound(-10, -20),

        'speed': 30,
        'fastMessage': """\
{sender} quickly inhales {target} and spits them out as a star, dealing \
{move:hp neg} damage!""",

        'blockChance': 30,
        'blockFailHPValue': Bound(-15, -25),
        'blockMessage': """\
{sender} tries to inhale {target} but {target} blocks it!""",
        'blockFailMessage': """\
{target} tries to block but {sender} inhales them and spits {target} \
out as a star, dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 20,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} tries to inhale {target} but {target} evades it!""",
        'evadeFailMessage': """\
{target} tries to evade but {sender} inhales them and spits {target} \
out as a star, dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-30, -40),
        'blockFailCriticalHPValue': Bound(-30, -40),
        'evadeFailCriticalHPValue': Bound(-30, -45),
        'criticalMessage': """\
{sender} inhales {target} and spits them out as a star, dealing \
{move:hpCrit neg} critical damage!""",
        'fastCriticalMessage': """\
{sender} quickly inhales {target} and spits them out as a star, dealing \
{move:hpCrit neg} critical damage!""",
        'blockFailCriticalMessage': """\
{target} tries to block but {sender} inhales them and spits {target} \
out as a star, dealing {move:hpBlockFCrit neg} critical damage!""",
        'evadeFailCriticalMessage': """\
{target} tries to evade but {sender} inhales them and spits {target} \
out as a star, dealing {move:hpEvadeFCrit neg} critical damage!""",

        'failureChance': 9,
        'failureMessage': """\
{sender} tries to inhale {target} but {target} was not sucked in.""",
        }
    ),
    Move({
        'name': 'Dash',
        'moveTypes': ([MTKirby],),
        'description': 'Dash towards your opponent in a spiraling blaze.',
        'moveMessage': """\
{sender} dashes towards {target} in a firey blaze, dealing \
{move:hp neg} damage and draining {move:st neg} {st.ext_full}!""",

        'hpValue': Bound(-15, -20),
        'stValue': Bound(-20, -30),
        'stCost': Bound(-30, -40),
        'mpCost': Bound(-30, -40),

        'effects': [
            StatusEffect({
                'name': 'Fire',
                'description': "You're on fire!",

                'target': 'target',
                'chances': ((30, 'uncountered'),),
                'duration': 2,

                'receiveMessage': '{self} is on fire!',
                'applyMessage': '{self} took {-hpValue} damage from fire!',
                'wearoffMessage': '{self} is no longer on fire.',

                'hpValue': Bound(-4, -9),
            }),
        ],

        'speed': 40,
        'fastMessage': """\
{sender} rapidly dashes towards {target} in a firey blaze, dealing \
{move:hp neg} damage and draining {move:st neg} {st.ext_full}!""",

        'blockChance': 50,
        'blockHPValue': Bound(-10, -15),
        'blockSTValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-15, -25),
        'blockFailSTValue': Bound(-20, -30),
        'blockMessage': """\
{sender} dashes towards {target} in a firey blaze but {target} blocks, \
dealing only {move:hpBlock neg} damage and \
{move:stBlock neg} {st.ext_full} drain!""",
        'blockFailMessage': """\
{sender} dashes towards {target} in a firey blaze and {target} \
fails to block, dealing {move:hpBlockF neg} damage and \
{move:stBlockF neg} {st.ext_full} drain!""",

        'evadeChance': 30,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeFailSTValue': Bound(-25, -35),
        'evadeMessage': """\
{sender} dashes towards {target} in a blaze but {target} evades it!""",
        'evadeFailMessage': """\
{sender} dashes towards {target} in a blaze and {target} \
fails to evade, dealing {move:hpEvadeF neg} damage and \
{move:stEvadeF neg} {st.ext_full} drain!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-20, -30),
        'criticalSTValue': Bound(-30, -40),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'blockFailCriticalSTValue': Bound(-30, -45),
        'evadeFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalSTValue': Bound(-30, -45),
        'criticalMessage': """\
{sender} dashes towards {target} in a scorching-hot blaze, critically dealing \
{move:hpCrit neg} damage and draining {move:stCrit neg} {st.ext_full}!""",
        'fastCriticalMessage': """\
{sender} quickly dashes towards {target} in a scorching-hot blaze, critically \
dealing {move:hpCrit neg} damage and draining \
{move:stCrit neg} {st.ext_full}!""",
        'blockFailCriticalMessage': """\
{sender} dashes towards {target} in a scorching-hot blaze and {target} \
fails to block, critically dealing {move:hpBlockFCrit neg} damage and \
{move:stBlockFCrit neg} {st.ext_full} drain!""",
        'evadeFailCriticalMessage': """\
{sender} dashes towards {target} in a scorching-hot blaze and {target} \
fails to evade, critically dealing {move:hpEvadeFCrit neg} damage and \
{move:stEvadeFCrit neg} {st.ext_full} drain!""",

        'failureChance': 8,
        'failureHPValue': Bound(-10, -15),
        'failureMessage': """\
{sender} tries to dash towards {target} but explodes into a ball of fire, \
losing {move:hpF neg} {hp.ext_full}, {move:stC neg} {st.ext_full}, and \
{move:mpC neg} {mp.ext_full}!""",
        }
    ),
    Move({
        'name': 'Hammer',
        'moveTypes': ([MTKirby],),
        'description': 'Charge up your hammer and smash down.',
        'itemRequired': ([
            {'name': 'Large Hammer'},
            ],),
        'moveMessage': """\
{sender} charges up their hammer and slams it down on {target}, dealing \
{move:hp neg} damage!""",

        'hpValue': Bound(-30, -40),
        'stCost': Bound(-61, -70),

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being hit by a hammer.',

                'target': 'target',
                'chances': ((20, 'uncountered'), (70, 'block'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 10,
        'fastMessage': """\
{sender} quickly charges up their hammer and slams it down on {target}, \
dealing {move:hp neg} damage!""",

        'blockChance': 80,
        'blockHPValue': Bound(-0, -10),
        'blockSTValue': Bound(-45, -80),
        'blockFailHPValue': Bound(-30, -35),
        'blockFailSTValue': Bound(-10, -20),
        'blockMessage': """\
{sender} charges up their hammer and {target} blocks, slamming down for \
{move:hpBlock neg} damage and {move:stBlock neg} {st.ext_full} drain!""",
        'blockFailMessage': """\
{sender} charges up their hammer and {target} fails to block, slamming down \
for {move:hpBlockF neg} damage and {move:stBlockF neg} {st.ext_full} drain!""",

        'evadeChance': 60,
        'evadeFailHPValue': Bound(-30, -45),
        'evadeFailSTValue': Bound(-10, -25),
        'evadeMessage': """\
{sender} charges up their hammer but {target} evades, making {sender} miss!""",
        'evadeFailMessage': """\
{sender} charges up their hammer and {target} fails to evade, slamming down \
for {move:hpEvadeF neg} damage and {move:stEvadeF neg} {st.ext_full} drain!""",

        'criticalChance': 5,
        'criticalHPValue': Bound(-35, -45),
        'blockFailCriticalHPValue': Bound(-35, -45),
        'blockFailCriticalSTValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-35, -50),
        'evadeFailCriticalSTValue': Bound(-20, -35),
        'criticalMessage': """\
{sender} charges up their hammer and SMASHES {target} with it, dealing \
{move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} charges up their hammer and SMASHES {target} with it, dealing \
{move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} charges up their hammer and SMASHES through {target}'s block, \
dealing {move:hpBlockFCrit neg} damage and \
{move:stBlockFCrit neg} {st.ext_full} drain!""",
        'evadeFailCriticalMessage': """\
{sender} charges up their hammer and {target} was too slow to evade, \
SMASHING {target} for {move:hpEvadeFCrit neg} damage and \
{move:stEvadeFCrit neg} {st.ext_full} drain!""",

        'failureChance': 10,
        'failureSTValue': Bound(40, 50),
        'failureMessage': """\
{sender} tries to charge their hammer but fails, losing \
{-(int(move.fmt('stC')) + int(move.fmt('stF')))} {st.ext_full}!""",
        }
    ),
    Move({
        'name': 'Inhale',
        'moveTypes': ([MTKirby],),
        'description': 'Take a deep breath.',

        'hpCost': Bound(1, 5),
        'stCost': Bound(15, 30),

        'speed': 100,
        'fastMessage': """\
{sender} takes a deep breath, regaining {move:hpC} {hp.ext_full} and \
{move:stC} {st.ext_full}.""",

        'blockChance': 0,
        'evadeChance': 0,
        'criticalChance': 0,

        'failureChance': 6,
        'failureSTValue': -14,
        'failureMessage': """\
{sender} tries to take a deep breath but only gains {move:hpC} {hp.ext_full} and \
{int(move.fmt('stC')) + int(move.fmt('stF'))} {st.ext_full}.""",
        }
    ),
    Move({
        'name': 'Throw',
        'moveTypes': ([MTKirby],),
        'description': 'Throw your opponent.',
        'moveMessage': """\
{sender} throws {target} forwards for {move:hp neg} damage!""",

        'hpValue': Bound(-10, -15),
        'stCost': Bound(-25, -35),

        'speed': 40,
        'fastMessage': """\
{sender} quickly throws {target} forwards for {move:hp neg} damage!""",

        'blockChance': 30,
        'blockFailHPValue': Bound(-12, -20),
        'blockMessage': """\
{sender} tries to throw {target} but {target} breaks free from \
{sender}'s grip!""",
        'blockFailMessage': """\
{sender} tries to throw {target} and {target} fails to break free, \
getting thrown for {move:hpBlockF neg} damage!""",

        'evadeChance': 55,
        'evadeFailHPValue': Bound(-16, -21),
        'evadeMessage': """\
{sender} tries to throw {target} but {target} evades it!""",
        'evadeFailMessage': """\
{sender} tries to throw {target} and {target} fails to evade it, \
getting thrown for {move:hpEvadeF neg} damage!""",

        'criticalChance': 12,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-17, -30),
        'evadeFailCriticalHPValue': Bound(-20, -30),
        'criticalMessage': """\
{sender} strongly throws {target} forwards for {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} strongly and quickly throws {target} forwards for \
{move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{target} fails to break free from {sender}'s grab and gets \
strongly thrown forwards for {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{target} fails to evade {sender}'s grab and gets strongly thrown forwards \
for {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 8,
        'failureMessage': """\
{sender} tries to throw {target} but couldn't lift {target} up.""",
        }
    ),


    Move({
        'name': 'Kick',
        'moveTypes': ([MTFootsies],),
        'description': """An expert kick.
Deals 50 damage for 70 {st.ext_full}.
Significant bonus damage when it fails to be countered.""",
        'moveMessage': """\
{sender} kicks {target} for {move:hp neg} damage!""",

        'hpValue': -50,
        'stCost': -70,

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being kicked.',

                'target': 'target',
                'chances': ((30, 'uncountered'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
            StatusEffect({
                'name': 'Blockstun',
                'description': 'Stun from blocking a kick.',

                'target': 'target',
                'chances': ((10, 'blockSuccess'),),
                'duration': 1,

                'receiveMessage': '{self} is in blockstun!',
                'wearoffMessage': "{self}'s blockstun has worn off.",

                'noMove': '{self} cannot move due to blockstun!',
            }),
        ],

        'speed': 30,
        'fastMessage': """\
{sender} swiftly kicks {target} for {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': -40,
        'blockFailHPValue': -60,
        'blockMessage': """\
{target} blocks {sender}'s kick, taking {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{target} fails to block {sender}'s kick, taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': -90,
        'evadeMessage': """\
{target} dodges and {sender}'s kick whiffs!""",
        'evadeFailMessage': """\
{target} fails to evade {sender}'s kick, taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 0,

        'failureChance': 5,
        'failureMessage': """\
{sender} attempts to kick {target} but whiffs.""",
        }
    ),
    Move({
        'name': 'Strike',
        'moveTypes': ([MTFootsies],),
        'description': """A precise dominant arm strike.
Deals 30 damage for 40 {st.ext_full}.
Significant bonus damage when it fails to be countered.""",
        'moveMessage': """\
{sender} strikes {target} for {move:hp neg} damage!""",

        'hpValue': -30,
        'stCost': -40,

        'effects': [
            StatusEffect({
                'name': 'Hitstun',
                'description': 'Stun from being strongly punched.',

                'target': 'target',
                'chances': ((20, 'uncountered'),),
                'duration': 1,

                'receiveMessage': '{self} is in hitstun!',
                'wearoffMessage': "{self}'s hitstun has worn off.",

                'noMove': '{self} cannot move due to hitstun!',
            }),
        ],

        'speed': 10,
        'fastMessage': """\
{sender} swiftly strikes {target} for {move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': -20,
        'blockFailHPValue': -40,
        'blockMessage': """\
{target} blocks {sender}'s strike, taking {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{target} fails to block {sender}'s strike, taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': -60,
        'evadeMessage': """\
{target} dodges and {sender}'s strike whiffs!""",
        'evadeFailMessage': """\
{target} fails to evade {sender}'s strike, \
taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 0,

        'failureChance': 5,
        'failureMessage': """\
{sender} attempts to strike {target} but whiffs.""",
        }
    ),
    Move({
        'name': 'Jab',
        'moveTypes': ([MTFootsies],),
        'description': """An expert punch.
Deals 20 damage for 30 {st.ext_full}.
Minor/Moderate bonus damage when it fails to be countered.""",
        'moveMessage': """\
{sender} jabs {target} for {move:hp neg} damage!""",

        'hpValue': -20,
        'stCost': -30,

        'speed': 70,
        'fastMessage': """\
{sender} swiftly jabs {target} for {move:hp neg} damage!""",

        'blockChance': 60,
        'blockHPValue': -10,
        'blockFailHPValue': -25,
        'blockMessage': """\
{target} blocks {sender}'s jab, taking {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{target} fails to block {sender}'s jab, taking {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': -40,
        'evadeMessage': """\
{target} dodges and {sender}'s jab whiffs!""",
        'evadeFailMessage': """\
{target} fails to evade {sender}'s jab, taking {move:hpEvadeF neg} damage!""",

        'criticalChance': 0,

        'failureChance': 5,
        'failureMessage': """\
{sender} tries to jab {target} but whiffs.""",
        }
    ),
    Move({
        'name': 'Advance',
        'moveTypes': ([MTFootsies],),
        'description': """Close the gap.
Gain 20 {st.ext_full}.""",

        'stCost': 20,

        'speed': 100,
        'fastMessage': """\
{sender} closes in on {target}, gaining {move:stC} {st.ext_full}.""",

        'criticalChance': 0,

        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Retreat',
        'moveTypes': ([MTFootsies],),
        'description': """Close the gap.
Decreases the opponent's {st.ext_full} by 10.""",

        'stValue': -10,

        'speed': 100,
        'fastMessage': """\
{sender} retreats and {target} loses {move:st neg} {st.ext_full}.""",

        'criticalChance': 0,

        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Hold',
        'moveTypes': ([MTFootsies],),
        'description': """Maintain ground.
Gain 10 {hp.ext_full}.""",

        'hpCost': 10,

        'speed': 100,
        'fastMessage': """\
{sender} holds, gaining {move:hpC} {hp.ext_full}.""",

        'criticalChance': 0,

        'failureChance': 0,
        }
    ),


    Move({
        'name': 'Test Main',
        'moveTypes': ([MTTest],),
        'description': '',
        'skillRequired': ([SKAcrobatics(1)],),
        'itemRequired': ([
            {'name': 'Knife'},
            ],),
        'moveMessage': '\
{sender} ran {move}, dealing {move:hp} HP, {move:st} ST, and {move:mp} MP \
to {target}. It costed {sender} {move:hpC} HP, {move:stC} ST, \
and {move:mpC} MP.',

        'hpValue': Bound(-1, -5),
        'stValue': Bound(-5),
        'mpValue': Bound(-5),
        'hpCost': Bound(-1, -5),
        'stCost': -5,
        'mpCost': Bound(-5),

        'speed': 0,
        'blockChance': 0,
        'blockFailHPValue': Bound(-1, -5),
        'blockFailSTValue': 1,
        'blockFailMPValue': Bound(-1, -5),
        'blockFailMessage': '\
{sender} ran {move} and {target} failed to block, \
taking {move:hpBlockF} HP, {move:stBlockF} ST, and {move:mpBlockF} MP.',
        'evadeChance': 100,
        'evadeMPValue': 10,
        'evadeMessage': '\
{sender} ran {move} and {target} evaded it, taking {move:mpEvade} .',
        'criticalChance': 0,
        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Test Fast',
        'moveTypes': ([MTTest],),
        'description': '',
        'moveMessage': '\
ERROR: {move} WAS COUNTERABLE',

        'hpValue': Bound(-1, -5),
        'stValue': Bound(-5),
        'mpValue': Bound(-5),
        'hpCost': Bound(-1, -5),
        'stCost': -5,
        'mpCost': Bound(-5),

        'speed': 100,
        'fastMessage': '\
{sender} ran {move}, dealing {move:hp} HP, {move:st} ST, and {move:mp} MP \
to {target}. It costed {sender} {move:hpC} HP, {move:stC} ST, \
and {move:mpC} MP.',

        'blockChance': 0,
        'evadeChance': 0,
        'criticalChance': 0,
        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Test Fail',
        'moveTypes': ([MTTest],),
        'description': '',

        'speed': 0,
        'blockChance': 0,
        'evadeChance': 0,
        'criticalChance': 0,

        'failureChance': 100,
        'failureHPValue': Bound(-5, -10),
        'failureSTValue': Bound(-5, -10),
        'failureMPValue': Bound(-5, -10),
        'failureMessage': '\
{sender} ran {move} and took {move:hpF} HP, {move:stF} ST, \
and {move:mpF} MP.',
        }
    ),
    Move({
        'name': 'Test Critical',
        'moveTypes': ([MTTest],),
        'description': '',

        'speed': 20,

        'blockChance': 50,
        'blockMessage': '\
{sender} used {move} and {target} blocked it.',

        'evadeChance': 50,
        'evadeMessage': '\
{sender} used {move} and {target} evaded it.',

        'criticalChance': 100,
        'criticalHPValue': -11,
        'criticalSTValue': -11,
        'criticalMPValue': -11,
        'blockFailCriticalHPValue': Bound(-1, -5),
        'blockFailCriticalSTValue': Bound(-1, -5),
        'blockFailCriticalMPValue': Bound(-1, -5),
        'evadeFailCriticalHPValue': Bound(-6, -10),
        'evadeFailCriticalSTValue': Bound(-6, -10),
        'evadeFailCriticalMPValue': Bound(-6, -10),
        'criticalMessage': '\
{sender} ran {move} and got a critical after no counter, dealing \
{move:hpCrit} HP, {move:stCrit} ST, and {move:mpCrit} MP to {target}.',
        'fastCriticalMessage': '\
{sender} ran {move} and got a fast critical, dealing \
{move:hpCrit} HP, {move:stCrit} ST, and {move:mpCrit} MP to {target}.',
        'blockFailCriticalMessage': '\
{sender} ran {move} and got a critical after a failed block, dealing \
{move:hpBlockFCrit} HP, {move:stBlockFCrit} ST, \
and {move:mpBlockFCrit} MP to {target}.',
        'evadeFailCriticalMessage': '\
{sender} ran {move} and got a critical after a failed evade, dealing \
{move:hpEvadeFCrit} HP, {move:stEvadeFCrit} ST, \
and {move:mpEvadeFCrit} MP to {target}.',

        'failureChance': 0,
        }
    ),


    Move({
        'name': 'ATLA Move Template',
        'moveTypes': ([MTBender],),
        'description': '',
        'skillRequired': ([SKAirBending(1)],),
        'itemRequired': ([
            {
                'name': '',
                'count': 0
            },
            ],),
        'moveMessage': """\
{move:hp neg}, {move:stC neg}""",

        'hpValue': Bound(-0, -0),
        'stValue': Bound(-0, -0),
        'mpValue': Bound(-0, -0),
        'hpCost': Bound(-0, -0),
        'stCost': Bound(-0, -0),
        'mpCost': Bound(-0, -0),

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
{move:hpBlock neg}""",
        'blockFailMessage': """\
{move:hpBlockF neg}""",

        'evadeChance': 0,
        'evadeHPValue': 0,
        'evadeSTValue': 0,
        'evadeMPValue': 0,
        'evadeFailHPValue': Bound(-0, -0),
        'evadeFailSTValue': Bound(-0, -0),
        'evadeFailMPValue': Bound(-0, -0),
        'evadeMessage': """\
{move:hpEvade neg}""",
        'evadeFailMessage': """\
{move:hpEvadeF neg}""",

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
{move:hpCrit neg}""",
        'fastCriticalMessage': """\
{move:hpCrit neg}""",
        'blockFailCriticalMessage': """\
{move:hpBlockFCrit neg}""",
        'evadeFailCriticalMessage': """\
{move:hpEvadeFCrit neg}""",

        'failureChance': 0,
        'failureHPValue': Bound(-0, -0),
        'failureSTValue': Bound(-0, -0),
        'failureMPValue': Bound(-0, -0),
        'failureMessage': """\
{move:hpF neg}""",
        }
    ),
    Move({
        'name': 'Tidal Wave',
        'moveTypes': ([MTBender],),
        'description': 'Summon a tidal wave.',
        'skillRequired': ([SKWaterBending(1)],),
        'moveMessage': """\
{sender} summons a tidal wave against {target}, \
dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -15),
        'stCost': Bound(-20, -30),
        'mpCost': Bound(-10, -20),

        'speed': 40,
        'fastMessage': """\
{sender} quickly summons a tidal wave against {target}, \
dealing {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-5, -15),
        'blockFailHPValue': Bound(-10, -20),
        'blockMessage': """\
{sender} summons a tidal wave and {target} blocks it, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} summons a tidal wave and {target} fails to block it, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 40,
        'evadeFailHPValue': Bound(-20, -25),
        'evadeMessage': """\
{sender} summons a tidal wave but {target} evades it!""",
        'evadeFailMessage': """\
{sender} summons a tidal wave and {target} fails to block it, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-16, -25),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-30, -35),
        'criticalMessage': """\
{sender} summons a SUPER tidal wave against {target}, \
dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} quickly summons a SUPER tidal wave against {target}, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} summons a SUPER tidal wave and {target} fails to block it, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} summons a SUPER tidal wave and {target} fails to evade it, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 5,
        'failureMessage': """\
{sender} fails to create a tidal wave towards {target}.""",
        }
    ),
    Move({
        'name': 'Ice Shards',
        'moveTypes': ([MTBender],),
        'description': 'Send a flurry of ice shards.',
        'skillRequired': ([SKWaterBending(1)],),
        'moveMessage': """\
{sender} shoots a flurry of ice shards at {target}, \
dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'stCost': Bound(-25, -35),
        'mpCost': Bound(-15, -20),

        'speed': 30,
        'fastMessage': """\
{sender} quickly shoots a flurry of ice shards at {target}, \
dealing {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-15, -30),
        'blockMessage': """\
{sender} shoots a flurry of ice shards and {target} blocks, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} shoots a flurry of ice shards and {target} fails to block, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 30,
        'evadeSTValue': Bound(-5, -15),
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} shoots a flurry of ice shards but {target} evades them \
for {move:stEvade neg} {st.ext_full}!""",
        'evadeFailMessage': """\
{sender} shoots a flurry of ice shards and {target} fails to evade, \
dealing {move:hp neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-25, -35),
        'criticalMessage': """\
{sender} shoots a MASSIVE flurry of ice shards, \
dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} quickly shoots a MASSIVE flurry of ice shards, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} shoots a MASSIVE flurry of ice shards and {target} fails to block, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} shoots a MASSIVE flurry of ice shards and {target} fails to evade, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 5,
        'failureMessage': """\
{sender} tries to shoot a flurry of ice shards but fails.""",
        }
    ),

    Move({
        'name': 'Pillar Strike',
        'moveTypes': ([MTBender],),
        'description': 'Send a column of rock at your opponent.',
        'skillRequired': ([SKEarthBending(1)],),
        'moveMessage': """\
{sender} strikes {target} with a column of rock, \
dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'stCost': Bound(-25, -35),
        'mpCost': Bound(-15, -20),

        'speed': 15,
        'fastMessage': """\
{sender} quickly strikes {target} with a column of rock, \
dealing {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-15, -30),
        'blockMessage': """\
{sender} sends a column of rock and {target} blocks, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} sends a column of rock and {target} fails to block, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 30,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} sends a column of rock but {target} evades it!""",
        'evadeFailMessage': """\
{sender} sends a column of rock and {target} fails to evade, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-25, -35),
        'criticalMessage': """\
{sender} quickly strikes {target} with a LARGE column of rock, \
dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} quickly strikes {target} with a LARGE column of rock, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} sends a LARGE column of rock and {target} fails to block, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} sends a LARGE column of rock and {target} fails to evade, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 5,
        'failureMessage': """\
{sender} tries to send a column of rock but fails.""",
        }
    ),

    Move({
        'name': 'Fire Blast',
        'moveTypes': ([MTBender],),
        'description': 'Throw a howitzer of flame.',
        'skillRequired': ([SKFireBending(1)],),
        'moveMessage': """\
{sender} blasts {target} with a meteor of flame, \
dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'stCost': Bound(-25, -35),
        'mpCost': Bound(-15, -20),

        'speed': 15,
        'fastMessage': """\
{sender} quickly blasts {target} with a meteor of flame, \
dealing {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-15, -30),
        'blockMessage': """\
{sender} shoots a meteor of flame and {target} blocks it, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} shoots a meteor of flame and {target} fails to block it, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 30,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} shoots a meteor of flame but {target} evades it!""",
        'evadeFailMessage': """\
{sender} shoots a meteor of flame and {target} fails to evade it, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-25, -35),
        'criticalMessage': """\
{sender} blasts {target} with a Sozin's Comet of flame, \
dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} quickly blasts {target} with a Sozin's Comet of flame, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} shoots a Sozin's Comet of flame and {target} fails to block it, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} shoots a Sozin's Comet of flame and {target} fails to evade it, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 5,
        'failureMessage': """\
{sender} tries to shoot a meteor of flame but fails.""",
        }
    ),

    Move({
        'name': 'Air Blast',
        'moveTypes': ([MTBender],),
        'description': 'Expel a blast of air.',
        'skillRequired': ([SKAirBending(1)],),
        'moveMessage': """\
{sender} blasts {target} back with a burst of air, \
dealing {move:hp neg} damage!""",

        'hpValue': Bound(-10, -20),
        'stCost': Bound(-25, -35),
        'mpCost': Bound(-15, -20),

        'speed': 30,
        'fastMessage': """\
{sender} quickly blasts {target} back with a burst of air, \
dealing {move:hp neg} damage!""",

        'blockChance': 70,
        'blockHPValue': Bound(-15, -25),
        'blockFailHPValue': Bound(-15, -30),
        'blockMessage': """\
{sender} blasts a burst of air at {target} who is blocking, \
dealing {move:hpBlock neg} damage!""",
        'blockFailMessage': """\
{sender} blasts a burst of air and {target} fails to block it, \
dealing {move:hpBlockF neg} damage!""",

        'evadeChance': 30,
        'evadeFailHPValue': Bound(-20, -30),
        'evadeMessage': """\
{sender} blasts a burst of air but {target} evades it!""",
        'evadeFailMessage': """\
{sender} blasts a burst of air and {target} fails to evade it, \
dealing {move:hpEvadeF neg} damage!""",

        'criticalChance': 10,
        'criticalHPValue': Bound(-15, -25),
        'blockFailCriticalHPValue': Bound(-20, -30),
        'evadeFailCriticalHPValue': Bound(-25, -35),
        'criticalMessage': """\
{sender} blasts {target} back with an EXPLOSION of air, \
dealing {move:hpCrit neg} damage!""",
        'fastCriticalMessage': """\
{sender} quickly blasts {target} back with an EXPLOSION of air, \
dealing {move:hpCrit neg} damage!""",
        'blockFailCriticalMessage': """\
{sender} blasts an EXPLOSION of air and {target} fails to block, \
dealing {move:hpBlockFCrit neg} damage!""",
        'evadeFailCriticalMessage': """\
{sender} blasts an EXPLOSION of air and {target} fails to evade it, \
dealing {move:hpEvadeFCrit neg} damage!""",

        'failureChance': 5,
        'failureMessage': """\
{sender} tries to fire a blast of air at {target} but fails.""",
        }
    ),
]


class BattleEnvironment:
    """An environment to use for setting up battles as a context manager."""

    BASE_VALUES_MULTIPLIER_PERCENT = 100               # 100
    BASE_VALUE_HEALTH_MULTIPLIER_PERCENT = 100         # 100
    BASE_VALUE_STAMINA_MULTIPLIER_PERCENT = 100        # 100
    BASE_VALUE_MANA_MULTIPLIER_PERCENT = 100           # 100

    BASE_ENERGIES_COST_MULTIPLIER_PERCENT = 100        # 100
    BASE_ENERGY_COST_HEALTH_MULTIPLIER_PERCENT = 100   # 100
    BASE_ENERGY_COST_STAMINA_MULTIPLIER_PERCENT = 100  # 100
    BASE_ENERGY_COST_MANA_MULTIPLIER_PERCENT = 100     # 100

    BASE_CRITICAL_CHANCE_PERCENT = 100                 # 100
    BASE_CRITICAL_VALUE_MULTIPLIER_PERCENT = 100       # 100

    BASE_BLOCK_CHANCE_PERCENT = 100                    # 100
    BASE_BLOCK_VALUES_MULTIPLIER_PERCENT = 100         # 100
    BASE_BLOCK_FAIL_VALUE_MULTIPLIER_PERCENT = 100     # 100

    BASE_EVADE_CHANCE_PERCENT = 100                    # 100
    BASE_EVADE_VALUES_MULTIPLIER_PERCENT = 100         # 100
    BASE_EVADE_FAIL_VALUE_MULTIPLIER_PERCENT = 100     # 100

    BASE_SPEED_MULTIPLIER_PERCENT = 100                # 100

    BASE_FAILURE_CHANCE_PERCENT = 100                  # 100
    BASE_FAILURE_MULTIPLIER_PERCENT = 100              # 100

    BASE_STATUS_EFFECTS_CHANCE_MULTIPLIER = 100        # 100

    REGEN_RATE_PERCENT = 100                           # 100
    HP_RATE_PERCENT = 100                              # 100
    ST_RATE_PERCENT = 100                              # 100
    MP_RATE_PERCENT = 100                              # 100

    DEFAULT_PLAYER_SETTINGS = {
        'hp': 100,                                     # 100
        'hpMax': 100,                                  # 100
        'hpRate': 1,                                   # 1
        'st': 100,                                     # 100
        'stMax': 100,                                  # 100
        'stRate': 10,                                  # 10
        'mp': 100,                                     # 100
        'mpMax': 100,                                  # 100
        'mpRate': 10,                                  # 10
        'status_effects': [],
        # [SKAcrobatics(1), SKKnifeHandling(2), SKBowHandling(1)]
        'skills': [
            SKAcrobatics(1),
            SKKnifeHandling(2),
            SKBowHandling(1),
        ],
        # [MTPhysical, MTMagical]
        'moveTypes': [
            MTPhysical,
            MTMagical,
        ],
        'moves': moveList,                             # moveList
        'AI': FighterAIGeneric,                        # FighterAIGeneric
        'inventory': [
            Item({
                'name': 'Sword',
                'description': 'A sword.',

                'count': 1,
                'maxCount': 1,
                }
            ),
            Item({
                'name': 'Knife',
                'description': 'A knife.',

                'count': 2,
                'maxCount': 10,
                }
            ),
            Item({
                'name': 'Longbow',
                'description': 'A longbow.',

                'count': 1,
                'maxCount': 1,
                }
            ),
            Item({
                'name': 'Arrow',
                'description': 'An arrow.',

                'count': 3,
                'maxCount': 64,
                }
            ),
            Item({
                'name': 'Bob-omb',
                'description': 'A bob-omb.',

                'count': 1,
                'maxCount': 3,
                }
            ),
            Item({
                'name': 'Large Hammer',
                'description': 'A hefty hammer.',

                'count': 1,
                'maxCount': 1,
                }
            ),
        ],
    }
    DEFAULT_PLAYER_SETTINGS_A = {
        # 'moveTypes': [MTKirby],
        # 'AI': FighterAISwordFirst,
    }
    DEFAULT_PLAYER_SETTINGS_B = {
        # 'AI': FighterAIDummy,
    }

    STATS_TO_SHOW = None

    DATA = {}

    SETTINGS_STANDARD = [
        'base_values_multiplier_percent',
        'base_value_health_multiplier_percent',
        'base_value_stamina_multiplier_percent',
        'base_value_mana_multiplier_percent',

        'base_energies_cost_multiplier_percent',
        'base_energy_cost_health_multiplier_percent',
        'base_energy_cost_stamina_multiplier_percent',
        'base_energy_cost_mana_multiplier_percent',

        'base_critical_chance_percent',
        'base_critical_value_multiplier_percent',

        'base_block_chance_percent',
        'base_block_values_multiplier_percent',
        'base_block_fail_value_multiplier_percent',

        'base_evade_chance_percent',
        'base_evade_values_multiplier_percent',
        'base_evade_fail_value_multiplier_percent',

        'base_speed_multiplier_percent',

        'base_failure_chance_percent',
        'base_failure_multiplier_percent',

        'base_status_effects_chance_multiplier',

        'regen_rate_percent',
        'hp_rate_percent',
        'st_rate_percent',
        'mp_rate_percent',

        'stats_to_show',
    ]
    SETTINGS_NONSTANDARD = [
        # NOTE: Do these dictionaries need to be copied
        # on initialization?
        'default_player_settings',
        'default_player_settings_A',
        'default_player_settings_B',

        'data',
    ]

    def __init__(
            self,
            *,
            fighters=None,
            random_player_names=None,
            gamemode=None,
            AI=None,
            default_player_settings=None,
            default_player_settings_A=None,
            default_player_settings_B=None,

            base_values_multiplier_percent=None,
            base_value_health_multiplier_percent=None,
            base_value_stamina_multiplier_percent=None,
            base_value_mana_multiplier_percent=None,

            base_energies_cost_multiplier_percent=None,
            base_energy_cost_health_multiplier_percent=None,
            base_energy_cost_stamina_multiplier_percent=None,
            base_energy_cost_mana_multiplier_percent=None,

            base_critical_chance_percent=None,
            base_critical_value_multiplier_percent=None,

            base_block_chance_percent=None,
            base_block_values_multiplier_percent=None,
            base_block_fail_value_multiplier_percent=None,

            base_evade_chance_percent=None,
            base_evade_values_multiplier_percent=None,
            base_evade_fail_value_multiplier_percent=None,

            base_speed_multiplier_percent=None,

            base_failure_chance_percent=None,
            base_failure_multiplier_percent=None,

            base_status_effects_chance_multiplier=None,

            regen_rate_percent=None,
            hp_rate_percent=None,
            st_rate_percent=None,
            mp_rate_percent=None,

            stats_to_show=None,

            data=None
            ):
        """
        Args:
            fighters (Optional[List[Fighter]]):
                A list of fighters that are participating in the
                battle environment. On setup and teardown, these
                fighters will automatically receive/lose the battle
                environment.
                A ValueError is raised on setup if an object in
                the sequence is not a Fighter or a subclass of Fighter.
                If None, uses an empty list.
            random_player_names (Optional[set]): A sequence of names
                for when names are not provided.
                If None, will raise a ValueError when
                a random name is needed.
            gamemode (Optional[str]): The name of the gamemode to use.
                If an empty string, no changes will occur on setup.
                If None, will prompt for a gamemode when required.
            AI (Optional[str]): The name of the AI to use.
                On setup, the given AI is interpreted
                and default settings will be modified accordingly.
                If an empty string, no changes will occur on setup.
                If None, will prompt for a AI when required.
            default_player_settings (Optional[dict]):
                The default settings for both players.
                If None, uses the class default,
                DEFAULT_PLAYER_SETTINGS.
            default_player_settings_A
            default_player_settings_B (Optional[dict]):
                The default settings for one of the players.
                Takes precedent over default_player_settings.
                If None, uses the class default.
            stats_to_show (Optional[Iterable[str]]):
                An optional set of stats to show.
                If None, shows all stats.
            data (Optional[dict]): A dictionary to store information.
                If None, uses the class default.

        """
        if fighters is not None:
            self.fighters = fighters
        else:
            self.fighters = []
        self._random_player_names = random_player_names
        self._gamemode = gamemode
        self._AI = AI

        for setting in self.SETTINGS_STANDARD:
            exec("""\
if {s} is not None:
    self._{s} = {s}
else:
    self._{s} = self.{s_upper}""".format(
                    s=setting,
                    s_upper=setting.upper()
                )
            )
        for setting in self.SETTINGS_NONSTANDARD:
            exec("""\
if {s} is not None:
    self._{s} = {s}
else:
    self._{s} = self.{s_upper}""".format(
                    s=setting,
                    s_upper=setting.upper()
                )
            )


    def get_gamemode(self, gamemodes):
        print_color(f"Gamemodes: {', '.join(gamemodes[1:])}")
        gamemodes = [gm.casefold() for gm in gamemodes]

        gamemode = input_color(
            'Type a gamemode (case-insensitive) to play it,\n'
            f'or nothing to skip. {GAME_SETUP_INPUT_COLOR}').casefold()

        if gamemode not in gamemodes:
            while gamemode not in gamemodes:
                gamemode = input_color(
                    'Unknown gamemode; check spelling: '
                    f'{GAME_SETUP_INPUT_COLOR}').casefold()

        logger.debug(f'Got gamemode from user: {gamemode!r}')
        self.gamemode = gamemode
        return gamemode


    def get_AI(self, AIs):
        print_color(f"AIs: {', '.join(AIs[1:])}")
        AIs = [AI.casefold() for AI in AIs]

        AI = input_color(
            'Type an AI (case-insensitive) to change it,\n'
            f'or nothing to skip. {GAME_SETUP_INPUT_COLOR}').casefold()

        if AI not in AIs:
            while AI not in AIs:
                AI = input_color(
                    'Unknown AI; check spelling: '
                    f'{GAME_SETUP_INPUT_COLOR}').casefold()

        logger.debug(f'Got AI from user: {AI!r}')
        self.AI = AI
        return AI


    def change_gamemode(self):
        """Change settings based on the environment's gamemode."""
        def stop_randomization_of_moves(*, A=True, B=True):
            if A and 'randomize_moves_A' in self.data:
                del self.data['randomize_moves_A']
            if B and 'randomize_moves_B' in self.data:
                del self.data['randomize_moves_B']

        def filter_moves_by_moveTypes(moves, moveTypes):
            return [
                m for m in moves
                if 'moveTypes' in m
                and Fighter.availableMoveCombination(
                    m, 'moveTypes', moveTypes
                )
            ]

        if self.gamemode == '':
            return
        elif self.gamemode == 'all moves':
            stop_randomization_of_moves()
        elif self.gamemode == 'avatar':
            self.default_player_settings['mpRate'] = 5

            elements = [
                SKEarthBending, SKWaterBending, SKFireBending, SKAirBending
            ]

            self.default_player_settings['moveTypes'] = [MTBender]

            del self.default_player_settings['inventory']

            # Pick random elements for fighters
            playerA_bending = random.choice(elements)
            playerB_bending = random.choice(elements)

            # Pick random skill levels for fighters
            playerA_bending = playerA_bending(random.randint(1, 3))
            playerB_bending = playerB_bending(random.randint(1, 3))
            self.default_player_settings_A['skills'] = [playerA_bending]
            self.default_player_settings_B['skills'] = [playerB_bending]
        elif self.gamemode == 'be kirby':
            self.default_player_settings_A['name'] = 'Kirby'
            self.default_player_settings_A['moveTypes'] = [MTKirby]

            stop_randomization_of_moves()
        elif self.gamemode == 'footsies':
            # Change stats
            self.default_player_settings['st'] = 0
            self.default_player_settings['stRate'] = 0
            self.default_player_settings['mpMax'] = 0
            moveTypes = [MTFootsies]
            self.default_player_settings['moveTypes'] = moveTypes
            self.default_player_settings['moves'] = filter_moves_by_move_type(
                self.default_player_settings['moves'], moveTypes
            )

            stop_randomization_of_moves()

            # Hide mana stat
            self.stats_to_show = ('hp', 'st')
        elif self.gamemode == 'fight kirby':
            self.default_player_settings_B['name'] = 'Kirby'
            self.default_player_settings_B['moveTypes'] = [MTKirby]
        elif self.gamemode == 'hard':
            self.base_values_multiplier_percent = 200
            self.base_energies_cost_multiplier_percent = 200
            self.base_critical_chance_percent = 0
            self.base_failure_chance_percent = 0

            self.default_player_settings['hpRate'] = 3
            self.default_player_settings['stRate'] = 20
            self.default_player_settings['mpRate'] = 15
        else:
            raise ValueError(f'{self.gamemode} is not a valid gamemode')
        logger.info(f'Set gamemode to {self.gamemode!r}')


    def change_AI(self):
        """Change settings based on the environment's AI."""
        def_settings = self.default_player_settings
        if self.AI == '':
            if self.gamemode == 'footsies':
                def_settings['AI'] = FighterAIFootsies
            return
        elif self.AI == 'sword first':
            def_settings['AI'] = FighterAISwordFirst
        elif self.AI == 'dummy':
            def_settings['AI'] = FighterAIDummy
        elif self.AI == 'mimic':
            def_settings['AI'] = FighterAIMimic
        else:
            raise ValueError(f'{self.AI} is not a valid AI')
        logger.info(f'Set AI to {self.AI!r}')


    def game_setup(self):
        """Do procedures on the start of a game loop."""
        if self.gamemode is None:
            gamemodes = [
                '', 'All Moves', 'Avatar', 'Be Kirby', 'Footsies',
                'Fight Kirby', 'Hard']
            self.get_gamemode(gamemodes)
        self.change_gamemode()

        if self.AI is None:
            # AI options
            AIs = ['', 'Sword First', 'Dummy', 'Mimic']
            # Change AI options based on the gamemode
            # if they shouldn't be used
            if self.gamemode == 'avatar':
                AIs.remove('Sword First')
            elif self.gamemode == 'footsies':
                AIs.remove('Sword First')
            elif self.gamemode == 'be kirby':
                AIs.remove('Mimic')
            elif self.gamemode == 'fight kirby':
                AIs.remove('Mimic')
                AIs.remove('Sword First')

            # If there are available AI options, ask for them
            if AIs:
                self.get_AI(sorted(AIs))
        self.change_AI()


    def __enter__(self):
        self.random_player_names = self._random_player_names
        self.gamemode = self._gamemode
        self.AI = self._AI
        self.default_player_settings = \
            self._default_player_settings.copy()
        self.default_player_settings_A = \
            self._default_player_settings_A.copy()
        self.default_player_settings_B = \
            self._default_player_settings_B.copy()
        self.data = {k: v.copy() if hasattr(v, 'copy') else v
                     for k, v in self._data.items()}

        for setting in self.SETTINGS_STANDARD:
            exec(f'self.{setting} = self._{setting}')

        self.game_setup()

        for fighter in self.fighters:
            if isinstance(fighter, Fighter):
                fighter.battle_env = self
            else:
                raise ValueError(
                    f'Unknown fighter object in fighters: {fighter!r}')

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        del self.random_player_names
        del self.gamemode
        del self.AI
        for setting in self.SETTINGS_STANDARD:
            exec(f'del self.{setting}')

        for fighter in self.fighters:
            if isinstance(fighter, Fighter):
                fighter.battle_env = None
            else:
                raise ValueError(
                    f'Unknown fighter object in fighters: {fighter!r}')


    @staticmethod
    def battle_stats_log(fighter, statLog=None):
        """Create or append to a list of dictionaries storing stats."""
        if statLog is None:
            statLog = []

        stats = dict()
        for stat in fighter.allStats:
            stats[stat] = eval(f'fighter.{stat}')

        statLog.append(stats)
        return statLog


    def begin_battle(
            self, a, b, *,
            autoplay=False,
            return_end_message=True):
        """
        Returns:
            list: Contains 4 lines
                "Number of Turns: {turns}"
                Fighter A's health: {hp}
                Fighter B's health: {hp}
                "The winner is {winner}!"
            None: Returned when return_end_message is False.

        """
        def fight_chart(
                *, topMessage, color_mode=None):
            if color_mode is None:
                color_mode = GAME_DISPLAY_STATS_COLOR_MODE
            return self.fightChartTwo(
                a, b, statLogA, statLogB,
                statsToShow=self.stats_to_show,
                topMessage=topMessage, tabs=GAME_DISPLAY_USE_TABS,
                color_mode=color_mode)

        def autoplay_pause():
            if autoplay:
                if a.isPlayer or b.isPlayer:
                    # If there is one/two players, pause AUTOPLAY seconds
                    pause(GAME_AUTOPLAY_NORMAL_DELAY / GAME_DISPLAY_SPEED)
                else:
                    # If two AIs are fighting, pause FIGHT_AI seconds
                    pause(GAME_AUTOPLAY_AI_DELAY / GAME_DISPLAY_SPEED)
                print()
            else:
                input()

        def cannotMove(fighter):
            for effect in fighter.status_effects:
                if 'noMove' in effect:
                    return True
            return False

        def status_effects_print_delay():
            if autoplay:
                if a.isPlayer or b.isPlayer:
                    return GAME_AUTOPLAY_NORMAL_DELAY / GAME_DISPLAY_SPEED
                else:
                    return GAME_AUTOPLAY_AI_DELAY / GAME_DISPLAY_SPEED
            return None

        logger.info(
            f'Starting fight against {a.decoloredName} and {b.decoloredName}')
        turns = 0
        statLogA, statLogB = self.battle_stats_log(a), self.battle_stats_log(b)

        # Game Loop
        print()
        while a.hp > 0 and b.hp > 0:
            turns += 1

            effects_messages_durations = a.updateStatusEffectsDuration()
            effects_messages_values = a.applyStatusEffectsValues()
            if effects_messages_values:
                autoplay_pause()
                a.printStatusEffectsMessages(effects_messages_values,
                                             status_effects_print_delay())
                if autoplay:
                    print()
            elif turns > 1:
                # Only triggers after first turn so battle starts immediately
                autoplay_pause()

            if a.hp <= 0 or b.hp <= 0:
                break

            # Print a chart of both fighters' stats
            print(fight_chart(topMessage='<--'), end='\n')

            autoplay_pause()
            if effects_messages_durations:
                a.printStatusEffectsMessages(effects_messages_durations,
                                             status_effects_print_delay())

            if GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show damage difference
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            # Print user moves if enabled
            if GAME_DISPLAY_PRINT_MOVES:
                print_color(a.formatMoves())
            a.move(b)

            if a.hp <= 0 or b.hp <= 0:
                break

            if not GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show regeneration
                statLogA = self.battle_stats_log(a)
            a.updateStats()

            # Repeat for B
            effects_messages_durations = b.updateStatusEffectsDuration()
            effects_messages_values = b.applyStatusEffectsValues()
            autoplay_pause()
            if effects_messages_values:
                b.printStatusEffectsMessages(effects_messages_values,
                                             status_effects_print_delay())
                if autoplay:
                    print()

            if a.hp <= 0 or b.hp <= 0:
                break

            print(fight_chart(topMessage='-->'), end='\n')

            autoplay_pause()
            if effects_messages_durations:
                b.printStatusEffectsMessages(effects_messages_durations,
                                             status_effects_print_delay())

            if GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            if GAME_DISPLAY_PRINT_MOVES:
                print_color(b.formatMoves())

            b.move(a)

            if a.hp <= 0 or b.hp <= 0:
                break

            if not GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                statLogB = self.battle_stats_log(b)
            b.updateStats()

        # Print results
        winner = a if a.hp > 0 and b.hp <= 0 \
            else b if b.hp > 0 and a.hp <= 0 \
            else None

        # Show the stat change only for the loser
        if winner is a:
            statLogA = None
        elif winner is b:
            statLogB = None
        else:
            # No winner; don't show any stat change
            statLogA = statLogB = None

        fightChart = fight_chart(topMessage='END')
        fightChart_nocolor = fight_chart(
            topMessage='END', color_mode=0)

        logFightChart = '\n'.join(fightChart_nocolor.split('\n')[1:])
        logger.info(
            f'Fight ended in {turns} turn{plural(turns)}:\n{logFightChart}\n')

        # add green color to the top message and print it
        autoplay_pause()
        print_color(fightChart.replace('END', '{FLgree}END{RA}'))
        print()

        if return_end_message:
            end_message = []

            end_message.append(f"Number of Turns: {turns}")

            a_win_color = ColoramaCodes.FLgree if a.hp > 0 \
                          else ColoramaCodes.FLred
            b_win_color = ColoramaCodes.FLgree if b.hp > 0 \
                          else ColoramaCodes.FLred
            end_message.append(format_color(
                "{a}'s {a.allStats['hp'].ext_full.title()}: "
                '{a_win_color}{a.hp}',
                namespace=locals()
                )
            )
            end_message.append(format_color(
                "{b}'s {b.allStats['hp'].ext_full.title()}: "
                '{b_win_color}{b.hp}',
                namespace=locals()
                )
            )

            winner_str = str(winner) if not None else 'nobody'
            end_message.append(format_color(f'The winner is {winner_str}!'))

            return end_message


    @staticmethod
    def print_end_message(end_message):
        time.sleep(0.75 / GAME_DISPLAY_SPEED)
        print_color(end_message[0])
        time.sleep(0.5 / GAME_DISPLAY_SPEED)
        print_color(end_message[1])
        time.sleep(0.25 / GAME_DISPLAY_SPEED)
        print_color(end_message[2])
        time.sleep(0.8 / GAME_DISPLAY_SPEED)
        print_color(end_message[3])


    @staticmethod
    def fightChartStat(
            statName, stat, preStat=None, *, spaces=True,
            color='', color_number_only=True):
        """Return a message for a stat with differences in the stat and preStat.
    statName - The name of the stat to show.
    stat - The current stat value.
    preStat - The previous stat value for showing change.'
    spaces - If True, add spaces between the +/-.
    color - The ANSI color code to return. By default, it is an empty string.
    color_number_only - If True, place the ANSI code before the stat number
        instead if before the statname."""
        s = ' ' if spaces else ''
        # Place the color before the statName if color_number_only is False
        color_name = color if not color_number_only else ''
        # Place the color before the stat value if color_number_only is True
        color_stat = color if color_number_only else ''
        # Add a reset ANSI code at the end if a color is used
        r = ColoramaCodes.RESET_ALL if color else ''

        if preStat is None or stat == preStat:
            msg = [f'{statName}: ', f'{stat}']
        elif stat > preStat:
            msg = [f'{statName}: ', f'{preStat}{s}+{s}{stat - preStat}']
        elif stat < preStat:
            msg = [f'{statName}: ', f'{preStat}{s}-{s}{preStat - stat}']
        no_code = ''.join(msg)

        return f'{color_name}{msg[0]}' + f'{color_stat}{msg[1]}' + r, no_code


    @classmethod
    def fightChartOne(cls, fighter, statLog=None, statsToShow=None, color=0):
        """Return a multi-line message showing a fighter's stats.

        Args:
            fighter:
                The fighter to get stats from.
            statLog:
                An optional statLog to show change in each stat.
            statsToShow (Optional[Iterable[str]]):
                An optional set of stats to show.
                If None, shows all stats.
            color:
                0 - Do not use any ANSI color codes.
                1 - Use the stat colors on the values.
                2 - Use the stat colors on the entire line.

        """
        if color < 0 or color > 2:
            raise ValueError('Unknown color mode')

        color_number_only = True if color == 1 else False

        message = str(fighter)
        no_codes = [fighter.decoloredName]

        def chart_stat(*args, **kwargs):
            nonlocal fighter, message
            chart_stat, no_code = cls.fightChartStat(
                statInfo.ext_short,
                eval(f'fighter.{stat}'), *args,
                color=colorString,
                color_number_only=color_number_only,
                **kwargs
            )
            message += '\n' + chart_stat
            no_codes.append(no_code)

        def showing_stat(statInfo):
            if statsToShow is not None:
                return statInfo.int_short in statsToShow
            return True

        if statLog is None:
            for stat, statInfo in fighter.allStats.items():
                if showing_stat(statInfo):
                    colorString = statInfo.color_fore if color > 0 else ''
                    chart_stat()
        else:
            recentStatLog = statLog[-1]
            for stat, statInfo in fighter.allStats.items():
                if showing_stat(statInfo):
                    preStat = recentStatLog.get(stat)
                    colorString = statInfo.color_fore if color > 0 else ''
                    chart_stat(preStat)

        return message, no_codes


    @classmethod
    def fightChartTwo(
            cls, a, b,
            statLogA=None, statLogB=None, *,
            statsToShow=None, topMessage=None, tabs=False,
            color_mode=0):
        """Return a multi-line message with two fighters showing their stats."""
        a, a_nocodes = cls.fightChartOne(
            a, statLogA, statsToShow=statsToShow, color=color_mode)
        a = a.split('\n')
        b, b_nocodes = cls.fightChartOne(
            b, statLogB, statsToShow=statsToShow, color=color_mode)
        b = b.split('\n')

        lengthA = len(max(a_nocodes, key=len))
        lengthB = len(max(b_nocodes, key=len))

        # Leading whitespaces to center-align all stats on first fighter but
        # keeping each stat aligned with each other
        leadingA = ' ' * (
            (len(a_nocodes[0]) - len(max(a_nocodes[1:], key=len))) // 2)
        lengthA_with_lead = lengthA - len(leadingA)
        leadingB = ' ' * (
            (len(b_nocodes[0]) - len(max(b_nocodes[1:], key=len))) // 2)
        lengthB_with_lead = lengthB - len(leadingB)

        message_list = []

        # If there is a top message, print it center-aligned
        if topMessage is not None:
            topMessageLength = lengthA * 2 + GAME_DISPLAY_STAT_GAP
            message_list.append(f'{topMessage:^{topMessageLength}}'.rstrip())

        # For each line in both states
        for line_num, lines in enumerate(zip(a, b, a_nocodes, b_nocodes)):
            a_line, b_line, a_line_nocode, b_line_nocode = lines

            # Center-align first line (names) only
            msg_align = '^' if line_num == 0 else ''

            if msg_align:
                # Skip first line, leadingA-center-aligning is for the stats
                msgA = f'{a_line_nocode:{msg_align}{lengthA}}' \
                       f"{' ' * GAME_DISPLAY_STAT_GAP}"
            else:
                msgA = f'{leadingA}' \
                       f'{a_line_nocode:{lengthA_with_lead}}' \
                       f"{' ' * GAME_DISPLAY_STAT_GAP}"
            # Replace the line_nocode with the actual ANSI-coded string
            msgA = msgA.replace(a_line_nocode, a_line, 1)

            if msg_align:
                msgB = f'{b_line_nocode:{msg_align}{lengthB}}'
            else:
                msgB = f'{leadingB}' \
                       f'{b_line_nocode:{lengthB_with_lead}}'
            msgB = msgB.replace(b_line_nocode, b_line, 1)

            message_list.append(msgA + msgB)

        # Add indent to all lines and strip trailing whitespace
        message = []
        for line in message_list:
            message.append(' ' * GAME_DISPLAY_STATS_SHIFT + line.rstrip())
        message = '\n'.join(message)

        if tabs:
            message = message.replace(' ' * GAME_DISPLAY_TAB_LENGTH, '\t')

        return message


    @staticmethod
    def get_players_and_autoplay():
        """Prompt the user for the players and autoplay mode.

        Returns:
            Tuple[Union[False, str], Union[False, str], bool]:
                firstPlayer, secondPlayer, and autoplay:
                firstPlayer and secondPlayer will either be
                their names, or False for AI.
                autoplay indicates the autoplay mode begin_battle should use.

        """
        firstPlayer = None
        secondPlayer = None

        firstPlayerPrompt, secondPlayerPrompt = None, None
        autoplay = False

        prompt_boolean = PromptBoolean(input_func=input_color)
        input_advanced = InputAdvanced(input_func=input_color)
        firstPlayerPrompt = prompt_boolean(
            'Is there a player-controlled fighter? {FLcyan}',
            false=('no', 'n'))
        if firstPlayerPrompt:
            firstPlayer = input_advanced(
                'Choose your name: {FLcyan}',
                loopPrompt='Name cannot be empty: {FLcyan}',
                breakString=None)
            secondPlayerPrompt = prompt_boolean(
                'Is there a second player? {FLcyan}',
                false=('no', 'n'))
            if secondPlayerPrompt:
                secondPlayer = input_advanced(
                    'Choose your name: {FLcyan}',
                    loopPrompt='Name cannot be empty: {FLcyan}',
                    breakString=None)
        if not (firstPlayerPrompt and secondPlayerPrompt):
            autoplay = prompt_boolean(
                'Automatically play AI turns? {FLcyan}',
                false=('no', 'n'))

        return firstPlayer, secondPlayer, autoplay


    def player_create_default_settings(
            self, initializeAI=True):
        """Creates the default player settings.

        It copies GAME_DEFAULT_PLAYER_SETTINGS for both players,
        then updates them with GAME_DEFAULT_PLAYER_A_SETTINGS and
        GAME_DEFAULT_PLAYER_B_SETTINGS for their respective Fighters.

        Args:
            initializeAI (bool): Initialize the AI in the default settings.

        Returns:
            Tuple[Dict, Dict]: The first and second players settings.

        """
        def copy_dict(dictionary):
            new = {}
            for k, v in dictionary.items():
                if isinstance(v, list):
                    new[k] = list_copy(v)
                elif hasattr(v, 'copy'):
                    new[k] = v.copy()
                else:
                    new[k] = v
            return new

        firstPlayerSettings = copy_dict(self.default_player_settings)
        firstPlayerSettings.update(
            copy_dict(self.default_player_settings_A)
        )
        secondPlayerSettings = copy_dict(self.default_player_settings)
        secondPlayerSettings.update(
            copy_dict(self.default_player_settings_B)
        )

        if initializeAI:
            if 'AI' in firstPlayerSettings:
                firstPlayerSettings['AI'] = firstPlayerSettings['AI']()
            if 'AI' in secondPlayerSettings:
                secondPlayerSettings['AI'] = secondPlayerSettings['AI']()

        return firstPlayerSettings, secondPlayerSettings


    def player_update_default_items(self, playerSettings, defaultSettings):
        """Updates the inventory and status effects in a player's settings.

        It replaces the items in playerSettings with defaultSettings
        since Fighters will mutate the same items if the objects are not copied.

        If there is an inventory in defaultSettings, it will replace the entire
        inventory in playerSettings. Otherwise, it will copy from
        GAME_DEFAULT_PLAYER_SETTINGS.

        Args:
            playerSettings (Dict): The player's settings.
            defaultSettings (Dict): The default settings to copy the items from.

        """
        defaultItems = self.default_player_settings.get('inventory')
        defaultPlayerItems = defaultSettings.get('inventory')
        defaultStatusEffects = defaultSettings.get('status_effects')

        if defaultPlayerItems is not None:
            playerSettings['inventory'] = list_copy(defaultPlayerItems)
        elif defaultItems is not None:
            playerSettings['inventory'] = list_copy(defaultItems)

        if defaultStatusEffects is not None:
            playerSettings['status_effects'] = list_copy(defaultStatusEffects)


    def player_update_names(
            self, firstPlayer, secondPlayer,
            firstName=None, secondName=None, nameSet=None):
        """Updates the names in a player's settings.

        If one or two names are missing, it will sample from nameSet,
        avoiding any name collisions.

        Args:
            firstPlayer (Dict): The first player's settings.
            secondPlayer (Dict): The second player's settings.
            firstName (Optional[str]): The first player's name.
                If not provided, will sample a name from nameSet.
            secondName (Optional[str]): The second player's name.
                If not provided, will sample a name from nameSet.
            nameSet (Optional[Set]): A set of names to randomly sample from.
                If one or two names are not provided, this must be available,
                containing at least two names.

        """
        def set_random_player_names(names):
            fighterAINames = random.sample(
                names.copy() - {firstName, secondName}, 2)
            firstPlayer.setdefault('name', fighterAINames[0])
            secondPlayer.setdefault('name', fighterAINames[1])

        if firstName is not None:
            firstPlayer['name'] = firstName
        if secondName is not None:
            secondPlayer['name'] = secondName

        if firstName is None or secondName is None:
            try:
                set_random_player_names(nameSet)
            except Exception:
                # Use self.random_player_names as fallback
                set_random_player_names(self.random_player_names)


    def player_create_fighters(
            self, firstPlayerSettings, secondPlayerSettings,
            firstIsPlayer=False, secondIsPlayer=False):
        """Creates the players' fighters.

        The BattleEnvironment() is automatically given to the fighters.

        Args:
            firstPlayerSettings (Dict): The first player's settings.
            secondPlayerSettings (Dict): The second player's settings.
            firstIsPlayer (Optional[Union[bool, str]]):
                Enable player control of the first fighter.
            secondIsPlayer (Optional[Union[bool, str]]):
                Enable player control of the second fighter.

        Returns:
            Tuple[Fighter, Fighter]: The first and second fighters.

        """
        firstFighter = Fighter(
            self, **firstPlayerSettings, isPlayer=True if firstIsPlayer else False)
        secondFighter = Fighter(
            self, **secondPlayerSettings, isPlayer=True if secondIsPlayer else False)

        return firstFighter, secondFighter


def startup_procedures():
    """Do procedures at the start of main()."""


def collect_and_log_garbage(log_handler=None):
    garbageCollection = gc.get_stats()
    garbageCollectionLog = '\n'.join(
        [f'Generation {n}: {repr(d)}'
         for n, d in enumerate(garbageCollection)])
    if log_handler is not None:
        logger.debug(
            'Logging garbage collection:\n' + garbageCollectionLog)
    return garbageCollectionLog


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

    try:
        startup_procedures()

        logger.info('Starting game loop')

        while True:
            with BattleEnvironment(
                        random_player_names=playernamelist,
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
                    firstPlayer, secondPlayer, nameSet=playernamelist)

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
                        if fighter.availableMove(m)
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

            # Collect garbage and log them
            collect_and_log_garbage(logger)

            # Wait for player to start another game
            input()
            print()
    except Exception:
        msg = exception_message(header='RUNTIME ERROR', log_handler=logger)
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
        logger.info('Ending game loop')


if __name__ == '__main__':
    while True:
        main()
