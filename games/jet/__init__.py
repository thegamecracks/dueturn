"""A game demonstrating how to deviate from `src.engine.begin_battle` with
custom stats and a modified battle loop."""
import functools

from . import ai
from . import moves
from . import stats
from .begin_jet_battle import begin_jet_battle
from src import engine
from src import logs
from src import sequencer
from src.textio import (
    ColoramaCodes, cr, format_color, input_color, print_color,

    input_choice_typewriter, input_loop_if_equals,
    input_number_typewriter, print_sleep_multiline, print_typewriter,

    SLEEP_CHAR_DELAY_NORMAL, SLEEP_CHAR_DELAY_SPECIFICS
)
from src.utility import exception_message

logger = logs.get_logger()

player_stats = stats.get_defaults(stats.stats)
player_evading_stats = stats.get_defaults(stats.evading_stats)

player_inventory = {
    engine.Item({
        'name': 'AIM-9 Sidewinder',
        'description': 'A short-range AA infrared-guided missile.',

        'count': 4,
        'maxCount': 4,
    }),
    engine.Item({
        'name': 'AIM-120 AMRAAM',
        'description': 'A medium-range AA active radar-guided missile.',

        'count': 4,
        'maxCount': 4,
    }),
}


def reset_color_method(s):
    print(ColoramaCodes.RESET_ALL, end='')
    return s


# Get username with custom colour printing
# (copied from
#  src.engine.battle_env.BattleEnvironment.get_players_and_autoplay)
input_name = functools.partial(
    input_loop_if_equals,
    loop_if_equals=(''),
    apply_methods=(str.strip, str.casefold, reset_color_method),
    print_func=functools.partial(print_color, end='')
)

player = engine.Fighter(
    name='Player',
    stats=player_stats,
    moves=moves.player_moves,
    counters={},
    inventory=player_inventory,
    is_player=True
)
player_evading = engine.Fighter(
    name=player.name,
    stats=player_evading_stats,
    moves=moves.evading_moves,
    counters={},
    is_player=True,
    interface_shell_dict={}  # Prevents first-tiem tutorial from opening again
)


def scene_1():
    player_name = input_name("Name: {FLgree}").title()
    # Add color to the name
    player_name = '{}{}{}'.format('{FLgree}', player_name, '{RA}')
    # Change player fighters to use new name
    player.name = player_name
    player_evading.name = player_name

    print_typewriter(
        'You are flying a jet armed with four Sidewinders and four AMRAAMs.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    print_typewriter(
        'Contact! A SU-35 is intercepting you!',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )

    return scene_2


def scene_2():
    # Battle scene
    # TODO: Create enemy fighter and start a battle with stop_after_move=True
    enemy_stats = stats.get_defaults(stats.stats)
    # Set flares and chaff to 120
    fl = stats.evading_stats['fl'].copy(120, engine.Bound(0, 120), 0)
    ch = stats.evading_stats['ch'].copy(120, engine.Bound(0, 120), 0)
    enemy_evading_stats = {'fl': fl, 'ch': ch}
    enemy_inventory = {
        engine.Item({
            'name': 'AA-11 Archer',
            'description': 'A short-range AA infrared-guided missile.',

            'count': 2,
            'maxCount': 2,
        }),
        engine.Item({
            'name': 'AA-12 Adder',
            'description': 'A medium-range AA active radar-guided missile.',

            'count': 2,
            'maxCount': 2,
        }),
    }
    enemy = engine.Fighter(
        name='{FLred}Su-35{RA}',
        stats=enemy_stats,
        moves=moves.enemy_moves,
        counters={},
        inventory=enemy_inventory,
        AI=ai.JetAI()
    )
    enemy_evading = engine.Fighter(
        name=enemy.name,
        stats=enemy_evading_stats,
        moves=moves.evading_moves,
        counters={},
        AI=ai.JetEvadingAI(),
        interface_shell_dict={}
    )

    # Battle loop
    begin_jet_battle(player, player_evading, enemy, enemy_evading)


def main():
    try:
        sequencer.begin_sequence(scene_1)
    except Exception:
        msg = exception_message(
            header='RUNTIME ERROR', log_handler=logger)
        msg += '\n\nSee the log for more details.'

        # Print message in red
        print_color('{RA}{FLred}', end='')
        print_color(msg, do_not_format=True)
