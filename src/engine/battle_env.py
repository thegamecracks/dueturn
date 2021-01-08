import enum
import time

from . import fighter_ai
from . import util
from .data import fighter_stats
from .fighter import Fighter
from .item import Item
from .movetype import MoveType
from .skill import Skill
from src import logs
from src import settings
from src.textio import (
    ColoramaCodes, cr, format_color, input_color, print_color,
    input_boolean, input_loop_if_equals
)
from src.utility import dict_copy, list_copy, plural

logger = logs.get_logger()

cfg_engine = settings.load_config('engine')

# Convert text color placeholders in config into color codes
cfg_engine.GAME_SETUP_INPUT_COLOR = format_color(
    cfg_engine.GAME_SETUP_INPUT_COLOR
)


class Autoplay(enum.Enum):
    INSTANT = 0
    SLEEP = 1
    INPUT = 2


class BattleEnvironment:
    """An environment to use for setting up battles as a context manager.

    This environment contains settings that fighters can use in their
    code, such as damage multipliers.

    Attributes:
        base_values_multiplier_percent: Multiplies all values
            that fighters receive.
        base_value_{int_full}_multiplier_percent:
            Multiplies a specific stat's value.

        base_stat_costs_multiplier_percent: Multiplies all stat costs
            that fighters spend on a move.
        base_stat_cost_{int_full}_multiplier_percent:
            Multiplies a specific stat's cost.

        base_critical_chance_percent: Multiplies the chance of a move
            being critical.
        base_critical_value_multiplier_percent: Multiplies the values
            of a critical move.

        base_{counter}_chance_percent: Multiplies a specific counter's
            chance of being successful.
        base_{counter}_multiplier_percent:
            Multiplies a specific counter's values from a move.
        base_speed_multiplier_percent: Multiplies the chance of a move
            being fast.
        base_status_effects_chance_percent: Multiplies the chance of a move
            applying a status effect (per status effect in move).

        regen_rate_percent: Multiplies all stats' update rate.
        {int_full}_rate_percent: Multiplies a specific stat's update rate.
    Attributes here that don't have a placeholder will have a class variable
    used as defaults for them.

    Args:
        fighters (Optional[List[Fighter]]):
            A list of fighters that are participating in the
            battle environment. On setup and teardown, these
            fighters will automatically receive/lose the battle
            environment.
            A ValueError is raised on setup if an object in
            the sequence is not a Fighter or a subclass of Fighter.
            If None, uses an empty list.
        **settings: Attributes available for the fighters to access,
            such as those in ALL_SETTINGS.

    """

    BASE_VALUES_MULTIPLIER_PERCENT = 100             # 100
    BASE_VALUE_HEALTH_MULTIPLIER_PERCENT = 100       # 100
    BASE_VALUE_STAMINA_MULTIPLIER_PERCENT = 100      # 100
    BASE_VALUE_MANA_MULTIPLIER_PERCENT = 100         # 100

    BASE_STAT_COSTS_MULTIPLIER_PERCENT = 100         # 100
    BASE_STAT_COST_HEALTH_MULTIPLIER_PERCENT = 100   # 100
    BASE_STAT_COST_STAMINA_MULTIPLIER_PERCENT = 100  # 100
    BASE_STAT_COST_MANA_MULTIPLIER_PERCENT = 100     # 100

    BASE_CRITICAL_CHANCE_PERCENT = 100               # 100
    BASE_CRITICAL_VALUE_MULTIPLIER_PERCENT = 100     # 100

    BASE_BLOCK_CHANCE_PERCENT = 100                  # 100
    BASE_BLOCK_VALUES_MULTIPLIER_PERCENT = 100       # 100
    BASE_BLOCK_FAIL_VALUE_MULTIPLIER_PERCENT = 100   # 100

    BASE_EVADE_CHANCE_PERCENT = 100                  # 100
    BASE_EVADE_VALUES_MULTIPLIER_PERCENT = 100       # 100
    BASE_EVADE_FAIL_VALUE_MULTIPLIER_PERCENT = 100   # 100

    BASE_SPEED_MULTIPLIER_PERCENT = 100              # 100

    BASE_FAILURE_CHANCE_PERCENT = 100                # 100
    BASE_FAILURE_MULTIPLIER_PERCENT = 100            # 100

    BASE_STATUS_EFFECTS_CHANCE_PERCENT = 100         # 100

    REGEN_RATE_PERCENT = 100                         # 100
    HP_RATE_PERCENT = 100                            # 100
    ST_RATE_PERCENT = 100                            # 100
    MP_RATE_PERCENT = 100                            # 100

    DEFAULT_PLAYER_SETTINGS = {
        'stats': fighter_stats.get_defaults(),
        'status_effects': [],
        # [Skill('Acrobatics', 1), Skill('Knife Handling', 2),
        #  Skill('Bow Handling', 1)]
        'skills': [
            Skill('Acrobatics', 1),
            Skill('Knife Handling', 2),
            Skill('Bow Handling', 1),
        ],
        # [MoveType('Physical'), MoveType('Magical')]
        'movetypes': [
            MoveType('Physical'),
            MoveType('Magical'),
        ],
        'moves': [],
        'AI': fighter_ai.FighterAIGeneric,             # FighterAIGeneric
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
        # 'movetypes': [MoveType('Kirby')],
        # 'AI': FighterAISwordFirst,
    }
    DEFAULT_PLAYER_SETTINGS_B = {
        # 'AI': FighterAIDummy,
    }

    STATS_TO_SHOW = None

    DATA = {}

    ALL_SETTINGS = [
        'base_values_multiplier_percent',
        'base_value_health_multiplier_percent',
        'base_value_stamina_multiplier_percent',
        'base_value_mana_multiplier_percent',

        'base_stat_costs_multiplier_percent',
        'base_stat_cost_health_multiplier_percent',
        'base_stat_cost_stamina_multiplier_percent',
        'base_stat_cost_mana_multiplier_percent',

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

        'base_status_effects_chance_percent',

        'regen_rate_percent',
        'hp_rate_percent',
        'st_rate_percent',
        'mp_rate_percent',

        'stats_to_show',

        # NOTE: Do these dictionaries need to be copied
        # on initialization?
        'default_player_settings',
        'default_player_settings_A',
        'default_player_settings_B',

        'data',
    ]

    def __init__(self, fighters=None, **settings):
        def set_setting(name):
            internal_name = '_' + name
            if name in settings:
                # Setting found; use it and remove it from kwargs
                setattr(self, internal_name, settings.pop(name))
            else:
                # No setting found; get stored class constant
                setattr(
                    self,
                    internal_name,
                    getattr(self, name.upper())
                )

        if fighters is not None:
            self.fighters = fighters
        else:
            self.fighters = []

        for name in self.ALL_SETTINGS:
            set_setting(name)

        if settings:
            raise TypeError(f'Too many arguments given ({settings})')

    def __enter__(self):
        def setup_setting(name):
            internal_name = '_' + name
            internal_setting = getattr(self, internal_name)
            cls = internal_setting.__class__
            if internal_setting.__hash__ is not None:
                # Probably immutable and therefore does not need a copy
                setattr(self, name, internal_setting)
            elif cls is dict:
                # NOTE: If a lot more types need to be supported for copying
                # here, start using a dictionary
                setattr(self, name, dict_copy(internal_setting))
            elif cls is list:
                setattr(self, name, list_copy(internal_setting))
            else:
                raise ValueError(
                    f'{internal_name} cannot be hashed and '
                    f'{self.__class__.__name__} does not support creating a '
                    f'deep copy of the object ({internal_setting!r})'
                )

        for setting in self.ALL_SETTINGS:
            setup_setting(setting)

        for fighter in self.fighters:
            if isinstance(fighter, Fighter):
                fighter.battle_env = self
            else:
                raise ValueError(
                    f'Unknown fighter object in fighters: {fighter!r}')

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for setting in self.ALL_SETTINGS:
            delattr(self, setting)

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
        for stat, stat_obj in fighter.stats.items():
            stats[stat] = stat_obj.value

        statLog.append(stats)
        return statLog

    def begin_battle(
            self, a, b, *,
            statLogA=None, statLogB=None,
            starting_turn=2,
            autoplay=2,
            return_end_message=True,
            stop_after_move=False):
        """
        Args:
            a (Fighter)
            b (Fighter): The two fighters battling each other.
            statLogA (Optional[List[dict]])
            statLogB (Optional[List[dict]]): A stat log generated by
                self.battle_stats_log() for their respective fighters.
                This info is used to calculate what stats have changed.
            starting_turn (int): The starting turn.
                If uneven, fighter B will move first.
                By default the starting turn is 2 so if one wins
                and `return_end_message` is True, it will show
                that the battle took one turn (`turn // 2`).
            autoplay (Autoplay):
                Autoplay.INSTANT: Disables pauses.
                Autoplay.SLEEP: Pauses using time.sleep.
                Autoplay.INPUT: Pauses using input().
            return_end_message (bool): If True, a list of color-formatted
                end messages is returned and can be printed out with
                `self.print_end_message`. Otherwise, returns None.
                If you know you will not print the default end message,
                set this to False so the messages do not get generated.
            stop_after_move (bool): If True, the next Fighter to move
                will not trigger `target.move_receive` but instead this
                method returns the results of `sender.move(do_not_send=True)`.
                `statLogA`, `statLogB`, and `turn` values are included.
                Note that `turn` is assigned to the "starting_turn" key to
                simplify using the return value as a starred expression
                for this method.
                Creating a custom code loop:
                    def step_battle(results=None):
                        results = {} if results is None else results
                        return begin_battle(a, b, stop_after_move=True, **results)
                    results = step_battle()
                    while isinstance(results, dict):
                        move_result = results.pop('move_result')
                        if move_result is None:
                            # Move failed due to unsatisfied requirements
                            results = step_battle(results)
                            continue
                        # <Your code here>
                        results = step_battle(results)
        Returns:
            dict: Returned when `stop_after_move` and a Fighter moves.
                See Args for more info.
            list: When `return_end_message`, this list contains 4 lines:
                "Number of Turns: {turn}"
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
            if autoplay == Autoplay.INSTANT:
                print()
            elif autoplay == Autoplay.SLEEP:
                if a.is_player or b.is_player:
                    # If there is one/two players, pause AUTOPLAY seconds
                    util.pause(
                        cfg_engine.GAME_AUTOPLAY_NORMAL_DELAY
                        / cfg_engine.GAME_DISPLAY_SPEED
                    )
                else:
                    # If two AIs are fighting, pause FIGHT_AI seconds
                    util.pause(
                        cfg_engine.GAME_AUTOPLAY_AI_DELAY
                        / cfg_engine.GAME_DISPLAY_SPEED
                    )
                print()
            elif autoplay == Autoplay.INPUT:
                input()
            else:
                raise TypeError(
                    'expected autoplay argument to be an Autoplay enum '
                    f'but received {autoplay!r}')

        def cannotMove(fighter):
            for effect in fighter.status_effects:
                if 'noMove' in effect:
                    return True
            return False

        def get_status_effects_print_delay():
            if autoplay == Autoplay.INSTANT:
                return 0
            elif autoplay == Autoplay.SLEEP:
                if a.is_player or b.is_player:
                    return (
                        cfg_engine.GAME_AUTOPLAY_NORMAL_DELAY
                        / cfg_engine.GAME_DISPLAY_SPEED
                    )
                else:
                    return (
                        cfg_engine.GAME_AUTOPLAY_AI_DELAY
                        / cfg_engine.GAME_DISPLAY_SPEED
                    )
            elif autoplay == Autoplay.INPUT:
                return None
            else:
                raise TypeError(
                    'expected autoplay argument to be an Autoplay enum '
                    f'but received {autoplay!r}')

        def is_dead(fighter):
            return hasattr(fighter, 'hp') and fighter.hp <= 0

        logger.info('Starting fight against '
                    f'{a.name_decolored} and {b.name_decolored}')
        turn = starting_turn
        move_result = None
        statLogA = self.battle_stats_log(a) if statLogA is None else statLogA
        statLogB = self.battle_stats_log(b) if statLogB is None else statLogB

        def a_turn():
            nonlocal move_result
            nonlocal statLogA
            nonlocal statLogB

            effects_messages_durations = a.update_status_effect_durations()
            effects_messages_values = a.update_status_effect_values()
            if effects_messages_values:
                autoplay_pause()
                a.print_status_effect_messages(effects_messages_values,
                                             get_status_effects_print_delay())
                if autoplay:
                    print()
            elif turn > 1:
                # Only triggers after first turn so battle starts immediately
                autoplay_pause()

            if is_dead(a) or is_dead(b):
                return False

            # Print a chart of both fighters' stats
            print(fight_chart(topMessage='<--'))

            autoplay_pause()
            if effects_messages_durations:
                a.print_status_effect_messages(effects_messages_durations,
                                             get_status_effects_print_delay())
                print()

            if cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show damage difference
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            # Print user moves if enabled
            if cfg_engine.GAME_DISPLAY_PRINT_MOVES:
                print_color(a.string_moves())

            # Fighter attacks
            move_result = a.move(b, do_not_send=stop_after_move)

            if not cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                # Show regeneration
                statLogA = self.battle_stats_log(a)
            if not is_dead(a) and not is_dead(b):
                a.update_stats()
                return True
            return False

        def b_turn():
            nonlocal move_result
            nonlocal statLogA
            nonlocal statLogB

            effects_messages_durations = b.update_status_effect_durations()
            effects_messages_values = b.update_status_effect_values()
            autoplay_pause()
            if effects_messages_values:
                b.print_status_effect_messages(effects_messages_values,
                                             get_status_effects_print_delay())
                if autoplay:
                    print()

            if is_dead(a) or is_dead(b):
                return False

            print(fight_chart(topMessage='-->'))

            autoplay_pause()
            if effects_messages_durations:
                b.print_status_effect_messages(effects_messages_durations,
                                             get_status_effects_print_delay())
                print()

            if cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                statLogA = self.battle_stats_log(a)
                statLogB = self.battle_stats_log(b)

            if cfg_engine.GAME_DISPLAY_PRINT_MOVES:
                print_color(b.string_moves())

            move_result = b.move(a, do_not_send=stop_after_move)

            if not cfg_engine.GAME_DISPLAY_SHOW_STAT_DIFFERENCE:
                statLogB = self.battle_stats_log(b)
            if not is_dead(a) and not is_dead(b):
                b.update_stats()
                return True
            return False

        def game_loop():
            nonlocal turn

            someone_has_moved = False

            while True:
                if turn % 2 == 0:
                    continue_turn = a_turn()
                    someone_has_moved = True
                    turn += 1
                else:
                    # Skip to fighter B's turn
                    continue_turn = True

                if not continue_turn or stop_after_move and someone_has_moved:
                    # Either a_turn() says a fighter has no health
                    # or stop_after_move is True and fighter A has moved
                    break

                # Repeat for B
                if turn % 2 != 0:
                    continue_turn = b_turn()
                    someone_has_moved = True
                    turn += 1
                else:
                    # Skip to fighter A's turn
                    continue_turn = True

                if not continue_turn or stop_after_move and someone_has_moved:
                    # Either b_turn() says a fighter has no health
                    # or stop_after_move is True and fighter B has moved
                    break

        print()
        if not is_dead(a) and not is_dead(b):
            game_loop()

        if not is_dead(a) and not is_dead(b) and stop_after_move:
            # Return results of move since `stop_after_move` is True
            # along with the info required to continue `begin_battle`
            return {
                'move_result': move_result,
                'starting_turn': turn,
                'statLogA': statLogA,
                'statLogB': statLogB
            }

        # Semantically, one turn is where both fighters move
        turn //= 2

        # Print results
        winner = a if not is_dead(a) and is_dead(b) \
            else b if is_dead(a) and not is_dead(b) \
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
            f'Fight ended in {turn} turn{plural(turn)}:\n'
            f'{logFightChart}\n'
        )

        # add green color to the top message and print it
        autoplay_pause()
        print_color(fightChart.replace('END', '{FLgree}END{RA}'))
        print()

        if return_end_message:
            end_message = []

            end_message.append(f"Number of Turns: {turn}")

            a_win_color = (ColoramaCodes.FLgree if a.hp > 0
                           else ColoramaCodes.FLred)
            b_win_color = (ColoramaCodes.FLgree if b.hp > 0
                           else ColoramaCodes.FLred)
            end_message.append(format_color(
                "{a}'s {a.stats['hp'].ext_full.title()}: "
                '{a_win_color}{a.hp}',
                namespace=locals()
                )
            )
            end_message.append(format_color(
                "{b}'s {b.stats['hp'].ext_full.title()}: "
                '{b_win_color}{b.hp}',
                namespace=locals()
                )
            )

            winner_str = str(winner) if winner is not None else 'nobody'
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

        Args:
            statName (str): The name of the stat to show.
            stat (int): The current stat value.
            preStat (Optional[int]):
                The previous stat value for showing change.
            spaces (bool): If True, add spaces between the +/-.
            color (str): The ANSI color code to return.
                By default, it is an empty string.
            color_number_only (bool):
                If True, place the ANSI code before the stat number
                instead of before the statname.

        Returns:
            str

        """
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
            fighter (Fighter):
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
        no_codes = [fighter.name_decolored]

        def chart_stat(*args, **kwargs):
            nonlocal fighter, message
            chart_stat, no_code = cls.fightChartStat(
                statInfo.ext_short.upper(),
                getattr(fighter, stat), *args,
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
            for stat, statInfo in fighter.stats.items():
                if showing_stat(statInfo):
                    colorString = statInfo.color_fore if color > 0 else ''
                    chart_stat()
        else:
            recentStatLog = statLog[-1]
            for stat, statInfo in fighter.stats.items():
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
        """Return a multi-line message for two fighters showing their stats."""
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
            message.append(
                ' ' * cfg_engine.GAME_DISPLAY_STATS_SHIFT + line.rstrip())
        message = '\n'.join(message)

        if tabs:
            message = message.replace(
                ' ' * cfg_engine.GAME_DISPLAY_TAB_LENGTH, '\t')

        return message
