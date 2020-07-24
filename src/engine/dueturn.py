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
import cmd          # Player Interface
import collections  # Useful classes
import functools    # Useful tools
import gc           # End-of-game garbage collection
import itertools    # Useful iteration functions
import json         # Loading moves
import platform     # OS identification
import pprint       # Pretty-format objects for logging
import random       # Random Number Generator
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

from .booldetailed import BoolDetailed
from .bound import Bound
from .item import Item
from .move import Move
from .movetype import MoveType
from .skill import Skill
from .status_effect import StatusEffect
from .util import *
from src.ai import goapy
from src import logs  # Creating logs
from src import settings
from src.textio import (  # Color I/O
    ColoramaCodes, cr, format_color, input_color, print_color
)
import src.engine.json_handler as json_handler

# Game Settings
playernamelist = {'abc', 'def', 'ghi', 'ned', 'led', 'med', 'red',
                  'ked', 'sed', 'ped', 'ben'}
# Name list for auto-selecting names

# Load settings
cfg_engine = settings.load_config('engine')
cfg_interface = settings.load_config('interface')

INDENT = '\t' if cfg_engine.GAME_DISPLAY_USE_TABS \
    else ' ' * cfg_engine.GAME_DISPLAY_TAB_LENGTH
# The standard indentation to use for printing based on game settings.

# Convert text color placeholders in config into color codes
cfg_engine.GAME_SETUP_INPUT_COLOR = format_color(
    cfg_engine.GAME_SETUP_INPUT_COLOR
)

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


# class Singleton(type):
#     _instances = {}
#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


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
            completekey=cfg_interface.AUTOCOMPLETE_KEY)
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
                self.fighter, color=cfg_engine.GAME_DISPLAY_STATS_COLOR_MODE
            )[0]
        )
        print()

        self.updateCmdqueue(arg)

    def do_display(self, arg):
        """Display the current battle.
Usage: display [future commands]"""
        print_color(BattleEnvironment.fightChartTwo(
            self.fighter, self.opponent,
            topMessage='<--', tabs=cfg_engine.GAME_DISPLAY_USE_TABS,
            color_mode=cfg_engine.GAME_DISPLAY_STATS_COLOR_MODE)
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
            exactSearch=cfg_interface.MOVES_REQUIRE_EXACT_SEARCH,
            detailedFail=True,
            showUnsatisfactories=True)

        # If search worked, check for unsatisfactories
        if not isinstance(moveFind, (type(None), BoolDetailed)):
            if unsatisfactories:
                # Missing dependencies; explain then request another move
                reasonMessage = f'Could not use {moveFind}; ' \
                                + moveFind.parse_unsatisfactories(
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
            exactSearch=cfg_interface.MOVES_REQUIRE_EXACT_SEARCH,
            detailedFail=True)

        # If search worked, print info about the move
        if not isinstance(moveFind, (type(None), BoolDetailed)):
            print_color(Fighter.get_move_info(moveFind))
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

    def __bool__(self):
        return self.hp > 0

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

    @classmethod
    def get_move_info(cls, move):
        """Return an informational string about a move.

        The description will be formatted with an environment containing:
            move: The instance of Move that the description is in.
            *cls.allStats: All StatInfo objects that Fighter has.
        It will also format color placeholders using `format_color()`.

        """
        namespace = cls.allStats.copy()
        namespace['move'] = move
        return format_color(move['description'], namespace=namespace)

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
                    value = Bound.call_random(effect[key])
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
                """Create the missing requirement message."""
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
            completekey=cfg_interface.AUTOCOMPLETE_KEY
        ).cmdloop()

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
                    random.uniform(1, 100) <= chance
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
        if random.uniform(1, 100) <= self.genChance(move, 'failure'):
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
                and random.uniform(1, 100) <= self.genChance(move, 'speed'):
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
        if random.uniform(1, 100) <= self.genChance(move, 'critical'):
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
        if random.uniform(1, 100) <= self.genChance(move, 'critical'):
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
        if random.uniform(1, 100) <= self.genChance(move, 'block'):
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
            if random.uniform(1, 100) <= self.genChance(move, 'critical'):
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
        if random.uniform(1, 100) <= self.genChance(move, 'evade'):
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
            if random.uniform(1, 100) <= self.genChance(move, 'critical'):
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

        value = Bound.call_random(move[statName])

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

        cost = Bound.call_random(move[statName])

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
            chance = Bound.call_random(move[chanceName])

            chance *= eval(
                f'self.battle_env.base_{chanceType}_chance_percent') / 100

            return chance

        elif chanceType in validChancesCounter:
            chanceConstant = self.allCounters[chanceType]

            chance = Bound.call_random(move[chanceName])

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

        value = Bound.call_random(move[statName])

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

        value = Bound.call_random(move[statName])

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

        value = Bound.call_random(move[statName])

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

        value = Bound.call_random(move[statName])

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

        value = Bound.call_random(move[statName])

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
        return Bound.call_average(move[f'{stat}Cost'])

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
        for _ in range(10):
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

    def avgMoveValuesWeighted(self, user, move, key_format):
        """Calculates the average value for each stat in a set of key values
found by move.averageValues(keySubstring), scales them by the internal
AI data values, and returns the sum.
Variables provided for key_format:
    stat - The current stat being iterated through
Example usage: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')"""
        total = 0
        for stat in user.allStats:
            key = eval("f'''" + key_format + "'''")
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

    def analyseMoveValuesWeighted(self, user, move, key_format):
        """Calculates the average value for each stat in a set of key values
found by move.averageValues(keySubstring), scales them by the internal
AI data values modified by an algorithm, and returns the sum.
Variables provided for key_format:
    stat - The current stat being iterated through
Example usage: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')"""
        total = 0
        for stat in user.allStats:
            key = eval("f'''" + key_format + "'''")
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
        for _ in range(10):
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
            if 'hpValue' in move and Bound.call_average(move['hpValue']) < 0:
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
        'moveTypes': ([MoveType('Physical')],),
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
        # [Skill('Acrobatics', 1), Skill('Knife Handling', 2), Skill('Bow Handling', 1)]
        'skills': [
            Skill('Acrobatics', 1),
            Skill('Knife Handling', 2),
            Skill('Bow Handling', 1),
        ],
        # [MoveType('Physical'), MoveType('Magical')]
        'moveTypes': [
            MoveType('Physical'),
            MoveType('Magical'),
        ],
        'moves': [],
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
        # 'moveTypes': [MoveType('Kirby')],
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
            f'or nothing to skip. {cfg_engine.GAME_SETUP_INPUT_COLOR}'
        ).casefold()

        if gamemode not in gamemodes:
            while gamemode not in gamemodes:
                gamemode = input_color(
                    'Unknown gamemode; check spelling: '
                    f'{cfg_engine.GAME_SETUP_INPUT_COLOR}').casefold()

        logger.debug(f'Got gamemode from user: {gamemode!r}')
        self.gamemode = gamemode
        return gamemode


    def get_AI(self, AIs):
        print_color(f"AIs: {', '.join(AIs[1:])}")
        AIs = [AI.casefold() for AI in AIs]

        AI = input_color(
            'Type an AI (case-insensitive) to change it,\n'
            f'or nothing to skip. {cfg_engine.GAME_SETUP_INPUT_COLOR}'
        ).casefold()

        if AI not in AIs:
            while AI not in AIs:
                AI = input_color(
                    'Unknown AI; check spelling: '
                    f'{cfg_engine.GAME_SETUP_INPUT_COLOR}').casefold()

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

        def filter_moves_by_move_types(moves, moveTypes):
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

            self.default_player_settings['moveTypes'] = [MoveType('Bender')]

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
            self.default_player_settings_A['moveTypes'] = [MoveType('Kirby')]

            stop_randomization_of_moves()
        elif self.gamemode == 'footsies':
            # Change stats
            self.default_player_settings['st'] = 0
            self.default_player_settings['stRate'] = 0
            self.default_player_settings['mpMax'] = 0
            moveTypes = [MoveType('Footsies')]
            self.default_player_settings['moveTypes'] = moveTypes
            self.default_player_settings['moves'] = filter_moves_by_move_types(
                self.default_player_settings['moves'], moveTypes
            )

            stop_randomization_of_moves()

            # Hide mana stat
            self.stats_to_show = ('hp', 'st')
        elif self.gamemode == 'fight kirby':
            self.default_player_settings_B['name'] = 'Kirby'
            self.default_player_settings_B['moveTypes'] = [MoveType('Kirby')]
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
                color_mode = cfg_engine.GAME_DISPLAY_STATS_COLOR_MODE
            return self.fightChartTwo(
                a, b, statLogA, statLogB,
                statsToShow=self.stats_to_show,
                topMessage=topMessage, tabs=cfg_engine.GAME_DISPLAY_USE_TABS,
                color_mode=color_mode)

        def autoplay_pause():
            if autoplay:
                if a.isPlayer or b.isPlayer:
                    # If there is one/two players, pause AUTOPLAY seconds
                    pause(cfg_engine.GAME_AUTOPLAY_NORMAL_DELAY / cfg_engine.GAME_DISPLAY_SPEED)
                else:
                    # If two AIs are fighting, pause FIGHT_AI seconds
                    pause(cfg_engine.GAME_AUTOPLAY_AI_DELAY / cfg_engine.GAME_DISPLAY_SPEED)
                print()
            else:
                input()

        def cannotMove(fighter):
            for effect in fighter.status_effects:
                if 'noMove' in effect:
                    return True
            return False

        def get_status_effects_print_delay():
            if autoplay:
                if a.isPlayer or b.isPlayer:
                    return cfg_engine.GAME_AUTOPLAY_NORMAL_DELAY / cfg_engine.GAME_DISPLAY_SPEED
                else:
                    return cfg_engine.GAME_AUTOPLAY_AI_DELAY / cfg_engine.GAME_DISPLAY_SPEED
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
                                             get_status_effects_print_delay())
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
                                             get_status_effects_print_delay())

            if cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show damage difference
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            # Print user moves if enabled
            if cfg_engine.GAME_DISPLAY_PRINT_MOVES:
                print_color(a.formatMoves())
            a.move(b)

            if a.hp <= 0 or b.hp <= 0:
                break

            if not cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show regeneration
                statLogA = self.battle_stats_log(a)
            a.updateStats()

            # Repeat for B
            effects_messages_durations = b.updateStatusEffectsDuration()
            effects_messages_values = b.applyStatusEffectsValues()
            autoplay_pause()
            if effects_messages_values:
                b.printStatusEffectsMessages(effects_messages_values,
                                             get_status_effects_print_delay())
                if autoplay:
                    print()

            if a.hp <= 0 or b.hp <= 0:
                break

            print(fight_chart(topMessage='-->'), end='\n')

            autoplay_pause()
            if effects_messages_durations:
                b.printStatusEffectsMessages(effects_messages_durations,
                                             get_status_effects_print_delay())

            if cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            if cfg_engine.GAME_DISPLAY_PRINT_MOVES:
                print_color(b.formatMoves())

            b.move(a)

            if a.hp <= 0 or b.hp <= 0:
                break

            if not cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
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
        speed = cfg_engine.GAME_DISPLAY_SPEED
        time.sleep(0.75 / speed)
        print_color(end_message[0])
        time.sleep(0.5 / speed)
        print_color(end_message[1])
        time.sleep(0.25 / speed)
        print_color(end_message[2])
        time.sleep(0.8 / speed)
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
            topMessageLength = lengthA * 2 + cfg_engine.GAME_DISPLAY_STAT_GAP
            message_list.append(f'{topMessage:^{topMessageLength}}'.rstrip())

        # For each line in both states
        for line_num, lines in enumerate(zip(a, b, a_nocodes, b_nocodes)):
            a_line, b_line, a_line_nocode, b_line_nocode = lines

            # Center-align first line (names) only
            msg_align = '^' if line_num == 0 else ''

            if msg_align:
                # Skip first line, leadingA-center-aligning is for the stats
                msgA = f'{a_line_nocode:{msg_align}{lengthA}}' \
                       f"{' ' * cfg_engine.GAME_DISPLAY_STAT_GAP}"
            else:
                msgA = f'{leadingA}' \
                       f'{a_line_nocode:{lengthA_with_lead}}' \
                       f"{' ' * cfg_engine.GAME_DISPLAY_STAT_GAP}"
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
            message.append(' ' * cfg_engine.GAME_DISPLAY_STATS_SHIFT + line.rstrip())
        message = '\n'.join(message)

        if tabs:
            message = message.replace(' ' * cfg_engine.GAME_DISPLAY_TAB_LENGTH, '\t')

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

        # Define input functions
        def input_name_func(*args, **kwargs):
            """Modified input_color function that strips whitespace."""
            return input_color(*args, **kwargs).strip()

        input_boolean_color = functools.partial(
            input_boolean,
            repeat_message='Answer with {true} or {false}: {FLcyan}',
            false=('no', 'n'),
            input_func=input_color
        )
        input_name = functools.partial(
            input_loop_if_equals,
            repeat_message='Name cannot be empty: {FLcyan}',
            loop_if_equals=(''),
            input_func=input_name_func
        )

        # Get player options
        firstPlayerPrompt = input_boolean_color(
            'Is there a player-controlled fighter? {FLcyan}')
        if firstPlayerPrompt:
            firstPlayer = input_name('Choose your name: {FLcyan}')
            secondPlayerPrompt = input_boolean_color(
                'Is there a second player? {FLcyan}')
            if secondPlayerPrompt:
                secondPlayer = input_name('Choose your name: {FLcyan}')
        if not (firstPlayerPrompt and secondPlayerPrompt):
            autoplay = input_boolean_color(
                'Automatically play AI turns? {FLcyan}')

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

    logger.debug('Reading src/engine/data/moves.json')
    moveList = json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

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
        logger.info('Ending game loop')


if __name__ == '__main__':
    while True:
        main()
