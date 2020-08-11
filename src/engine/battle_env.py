import functools
import random
import time

from . import fighter_ai
from . import json_handler
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
            gamemode='',
            AI='',
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

        def filter_moves_by_move_types(moves, movetypes):
            return [
                m for m in moves
                if 'movetypes' in m
                and Fighter.available_combination_in_move(
                    m, 'movetypes', movetypes
                )
            ]

        if self.gamemode == '':
            return
        elif self.gamemode == 'all moves':
            self.default_player_settings['moves'] = json_handler.load(
                'src/engine/data/moves.json', encoding='utf-8')

            stop_randomization_of_moves()
        elif self.gamemode == 'avatar':
            self.default_player_settings['moves'] = json_handler.load(
                'src/engine/data/avatar.json', encoding='utf-8')

            self.default_player_settings['stats']['mp'].rate = 5

            elements = [
                'Earth Bending', 'Water Bending', 'Fire Bending', 'Air Bending'
            ]

            self.default_player_settings['movetypes'] = [MoveType('Bender')]

            del self.default_player_settings['inventory']

            # Pick random elements for fighters
            playerA_bending = random.choice(elements)
            playerB_bending = random.choice(elements)

            # Pick random skill levels for fighters
            playerA_bending = Skill(playerA_bending, random.randint(1, 3))
            playerB_bending = Skill(playerB_bending, random.randint(1, 3))
            self.default_player_settings_A['skills'] = [playerA_bending]
            self.default_player_settings_B['skills'] = [playerB_bending]
        elif self.gamemode == 'be kirby':
            self.default_player_settings_A['moves'] = json_handler.load(
                'src/engine/data/kirby.json', encoding='utf-8')
            self.default_player_settings_B['moves'] = json_handler.load(
                'src/engine/data/moves.json', encoding='utf-8')
            self.default_player_settings_A['name'] = 'Kirby'
            self.default_player_settings_A['movetypes'] = [MoveType('Kirby')]

            stop_randomization_of_moves()
        elif self.gamemode == 'footsies':
            self.default_player_settings['moves'] = json_handler.load(
                'src/engine/data/footsies.json', encoding='utf-8')

            # Change stats
            self.default_player_settings['stats']['st'].value = 0
            self.default_player_settings['stats']['st'].rate = 0
            del self.default_player_settings['stats']['mp']
            movetypes = [MoveType('Footsies')]
            self.default_player_settings['movetypes'] = movetypes
            self.default_player_settings['moves'] = filter_moves_by_move_types(
                self.default_player_settings['moves'], movetypes
            )

            stop_randomization_of_moves()

        elif self.gamemode == 'fight kirby':
            self.default_player_settings_A['moves'] = json_handler.load(
                'src/engine/data/moves.json', encoding='utf-8')
            self.default_player_settings_B['moves'] = json_handler.load(
                'src/engine/data/kirby.json', encoding='utf-8')

            self.default_player_settings_B['name'] = 'Kirby'
            self.default_player_settings_B['movetypes'] = [MoveType('Kirby')]
        elif self.gamemode == 'hard':
            self.default_player_settings['moves'] = json_handler.load(
                'src/engine/data/moves.json', encoding='utf-8')

            self.base_values_multiplier_percent = 200
            self.base_energies_cost_multiplier_percent = 200
            self.base_critical_chance_percent = 0
            self.base_failure_chance_percent = 0
            self.base_status_effects_chance_multiplier = 130

            self.default_player_settings['stats']['hp'].rate = 3
            self.default_player_settings['stats']['st'].rate = 20
            self.default_player_settings['stats']['mp'].rate = 15
        else:
            raise ValueError(f'{self.gamemode} is not a valid gamemode')
        logger.info(f'Set gamemode to {self.gamemode!r}')

    def change_AI(self):
        """Change settings based on the environment's AI."""
        def_settings = self.default_player_settings
        if self.AI == '':
            if self.gamemode == 'footsies':
                def_settings['AI'] = fighter_ai.FighterAIFootsies
            return
        elif self.AI == 'sword first':
            def_settings['AI'] = fighter_ai.FighterAISwordFirst
        elif self.AI == 'dummy':
            def_settings['AI'] = fighter_ai.FighterAIDummy
        elif self.AI == 'mimic':
            def_settings['AI'] = fighter_ai.FighterAIMimic
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
            dict_copy(self._default_player_settings)
        self.default_player_settings_A = \
            dict_copy(self._default_player_settings_A)
        self.default_player_settings_B = \
            dict_copy(self._default_player_settings_B)
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
        for stat, stat_obj in fighter.stats.items():
            stats[stat] = stat_obj.value

        statLog.append(stats)
        return statLog

    def begin_battle(
            self, a, b, *,
            statLogA=None, statLogB=None,
            starting_turn=2,
            autoplay=False,
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
            autoplay (bool): Will use time.sleep instead of input()
                whenever there is a pause.
            return_end_message (bool): If True, a list of color-formatted
                end messages is returned and can be printed out with
                `self.print_end_message`. Otherwise, returns None.
                If you know you will not print the default end message,
                set this to False so the messages do not get generated.
            stop_after_move (bool): If True, the next Fighter to move
                will not trigger `target.move_receive` but instead returns
                the results of `sender.move(do_not_send=True)`.
                If the result is a dictionary then `statLogA`, `statLogB`,
                and `turn` values are added.
                Note that `turn` is assigned to the "starting_turn" key to
                simplify using the return value as a starred expression
                for this method.
                Creating a custom code loop:
                    results = {}
                    while True:
                        results = begin_battle(a, b, stop_after_move=True,
                                               **results)
                        if not isinstance(results, dict):
                            break
                        move_result = results.pop('move_result')
                        # <Your code here>
        Returns:
            list: Contains 4 lines
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
            if autoplay:
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
            else:
                input()

        def cannotMove(fighter):
            for effect in fighter.status_effects:
                if 'noMove' in effect:
                    return True
            return False

        def get_status_effects_print_delay():
            if autoplay:
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
            return None

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
        def reset_color_method(s):
            print(ColoramaCodes.RESET_ALL, end='')
            return s
        print_color_without_newline = functools.partial(
            print_color, end='')
        input_boolean_color = functools.partial(
            input_boolean,
            repeat_prompt='Answer with {true} or {false}: {FLcyan}',
            false=('no', 'n'),
            apply_methods=(str.strip, str.casefold, reset_color_method),
            print_func=print_color_without_newline
        )
        input_name = functools.partial(
            input_loop_if_equals,
            repeat_prompt='Name cannot be empty: {FLcyan}',
            loop_if_equals=(''),
            apply_methods=(str.strip, str.casefold, reset_color_method),
            print_func=print_color_without_newline
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
        else:
            autoplay = input_boolean_color(
                'Automatically advance occurring events? {FLcyan}')

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
        firstPlayerSettings = dict_copy(self.default_player_settings)
        firstPlayerSettings.update(
            dict_copy(self.default_player_settings_A)
        )
        secondPlayerSettings = dict_copy(self.default_player_settings)
        secondPlayerSettings.update(
            dict_copy(self.default_player_settings_B)
        )

        if initializeAI:
            if 'AI' in firstPlayerSettings:
                firstPlayerSettings['AI'] = firstPlayerSettings['AI']()
            if 'AI' in secondPlayerSettings:
                secondPlayerSettings['AI'] = secondPlayerSettings['AI']()

        return firstPlayerSettings, secondPlayerSettings

    def player_update_default_items(self, playerSettings, defaultSettings):
        """Updates the inventory and status effects in a player's settings.

        It replaces the items in playerSettings with defaultSettings since
        Fighters will mutate the same items if the objects are not copied.

        If there is an inventory in defaultSettings, it will replace the entire
        inventory in playerSettings. Otherwise, it will copy from
        GAME_DEFAULT_PLAYER_SETTINGS.

        NOTE: Status effects are updated in playerSettings contrary to
        the method name `player_update_default_items`, which only implies
        that items are updated.

        Args:
            playerSettings (Dict): The player's settings.
            defaultSettings (Dict): The default settings to copy items from.

        """
        defaultItems = self.default_player_settings.get('inventory')
        defaultPlayerItems = defaultSettings.get('inventory')
        defaultStatusEffects = defaultSettings.get('status_effects')

        if defaultPlayerItems is not None:
            playerSettings['inventory'] = list_copy(defaultPlayerItems)
        elif defaultItems is not None:
            playerSettings['inventory'] = list_copy(defaultItems)

        if defaultStatusEffects is not None:
            playerSettings['status_effects'] = list_copy(
                defaultStatusEffects)

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
            firstis_player=False, secondis_player=False):
        """Creates the players' fighters.

        The BattleEnvironment() is automatically given to the fighters.

        Args:
            firstPlayerSettings (Dict): The first player's settings.
            secondPlayerSettings (Dict): The second player's settings.
            firstis_player (Optional[Union[bool, str]]):
                Enable player control of the first fighter.
            secondis_player (Optional[Union[bool, str]]):
                Enable player control of the second fighter.

        Returns:
            Tuple[Fighter, Fighter]: The first and second fighters.

        """
        firstFighter = Fighter(
            **firstPlayerSettings, battle_env=self,
            is_player=True if firstis_player else False
        )
        secondFighter = Fighter(
            **secondPlayerSettings, battle_env=self,
            is_player=True if secondis_player else False
        )

        return firstFighter, secondFighter
