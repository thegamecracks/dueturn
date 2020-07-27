import cmd
import platform
import time

from .booldetailed import BoolDetailed
from .data import fighter_stats
from .move import Move
from src import logs
from src import settings
from src.textio import (
    ColoramaCodes, cr, format_color, input_color, print_color
)

logger = logs.get_logger()

# Conditional import
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

cfg_engine = settings.load_config('engine')
cfg_interface = settings.load_config('interface')


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
            print(
                format_color(f'Your player is {self.fighter.name}' + '{RA}!'),
                'Below will be a list of commands you can type to use.',
                'To start, type "list" to show what moves you have.',
                'Type one of those moves to use them on your opponent.',
                sep='\n'
            )
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
            self.fighter.battle_env.fightChartOne(
                self.fighter, color=cfg_engine.GAME_DISPLAY_STATS_COLOR_MODE
            )[0]
        )
        print()

        self.updateCmdqueue(arg)

    def do_display(self, arg):
        """Display the current battle.
Usage: display [future commands]"""
        print_color(self.fighter.battle_env.fightChartTwo(
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
            namespace = fighter_stats.ALL_STAT_INFOS.copy()
            namespace['move'] = moveFind
            print_color(moveFind['description'], namespace=namespace)
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
