import random

from src import engine
from src import logs
from src import settings
from src.textio import input_color, print_color

logger = logs.get_logger()

cfg_engine = settings.load_config('engine')


def input_gamemode(gamemodes):
    print_color(f"Gamemodes: {', '.join(gamemodes[1:])}")
    gamemodes = [gm.casefold() for gm in gamemodes]

    gamemode = input_color(
        'Type a gamemode (case-insensitive) to play it,\n'
        f'or nothing to skip. {cfg_engine.GAME_SETUP_INPUT_COLOR}'
    ).casefold()

    while gamemode not in gamemodes:
        gamemode = input_color(
            'Unknown gamemode; check spelling: '
            f'{cfg_engine.GAME_SETUP_INPUT_COLOR}').casefold()

    logger.debug(f'Got gamemode from user: {gamemode!r}')
    return gamemode


def stop_randomization_of_moves(battle, *, A=True, B=True):
    """Remove keys in a battle environment telling the game loop to randomize
    moves when generating them for the players (see __init__.py)."""
    if A and 'randomize_moves_A' in battle.data:
        del battle.data['randomize_moves_A']
    if B and 'randomize_moves_B' in battle.data:
        del battle.data['randomize_moves_B']


def filter_moves_by_move_types(moves, movetypes):
    """Filters moves by whether the move matches a movetype combination."""
    return [
        m for m in moves
        if 'movetypes' in m
        and engine.Fighter.available_combination_in_move(
            m, 'movetypes', movetypes
        )
    ]


def change_gamemode(battle, gamemode):
    """Change settings based on the environment's gamemode."""

    gamemodes = {
        'all moves': gamemode_all_moves,
        'avatar': gamemode_avatar,
        'be kirby': gamemode_be_kirby,
        'footsies': gamemode_footsies,
        'fight kirby': gamemode_fight_kirby,
        'hard': gamemode_hard,
    }
    if gamemode == '':
        logger.info('No gamemode was selected')
    else:
        gamemode_func = gamemodes.get(gamemode)
        if gamemode_func is not None:
            gamemode_func(battle)
            logger.info(f'Set gamemode to {gamemode!r}')
        else:
            raise ValueError(f'{gamemode!r} is not a valid gamemode')


def gamemode_all_moves(battle):
    battle.default_player_settings['moves'] = engine.json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

    stop_randomization_of_moves(battle)


def gamemode_avatar(battle):
    battle.default_player_settings['moves'] = engine.json_handler.load(
        'src/engine/data/avatar.json', encoding='utf-8')

    battle.default_player_settings['stats']['mp'].rate = 5

    elements = [
        'Earth Bending', 'Water Bending', 'Fire Bending', 'Air Bending'
    ]

    battle.default_player_settings['movetypes'] = [engine.MoveType('Bender')]

    del battle.default_player_settings['inventory']

    # Pick random elements for fighters
    playerA_bending = random.choice(elements)
    playerB_bending = random.choice(elements)

    # Pick random skill levels for fighters
    playerA_bending = engine.Skill(playerA_bending, random.randint(1, 3))
    playerB_bending = engine.Skill(playerB_bending, random.randint(1, 3))
    battle.default_player_settings_A['skills'] = [playerA_bending]
    battle.default_player_settings_B['skills'] = [playerB_bending]


def gamemode_be_kirby(battle):
    battle.default_player_settings_A['moves'] = engine.json_handler.load(
        'src/engine/data/kirby.json', encoding='utf-8')
    battle.default_player_settings_B['moves'] = engine.json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')
    battle.default_player_settings_A['name'] = 'Kirby'
    battle.default_player_settings_A['movetypes'] = [
        engine.MoveType('Kirby')
    ]

    stop_randomization_of_moves(battle)


def gamemode_footsies(battle):
    battle.default_player_settings['moves'] = engine.json_handler.load(
        'src/engine/data/footsies.json', encoding='utf-8')

    # Change stats
    battle.default_player_settings['stats']['st'].value = 0
    battle.default_player_settings['stats']['st'].rate = 0
    del battle.default_player_settings['stats']['mp']
    movetypes = [engine.MoveType('Footsies')]
    battle.default_player_settings['movetypes'] = movetypes
    battle.default_player_settings['moves'] = filter_moves_by_move_types(
        battle.default_player_settings['moves'], movetypes
    )

    stop_randomization_of_moves(battle)


def gamemode_fight_kirby(battle):
    battle.default_player_settings_A['moves'] = engine.json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')
    battle.default_player_settings_B['moves'] = engine.json_handler.load(
        'src/engine/data/kirby.json', encoding='utf-8')

    battle.default_player_settings_B['name'] = 'Kirby'
    battle.default_player_settings_B['movetypes'] = [
        engine.MoveType('Kirby')
    ]


def gamemode_hard(battle):
    battle.default_player_settings['moves'] = engine.json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

    battle.base_values_multiplier_percent = 200
    battle.base_stat_costs_multiplier_percent = 200
    battle.base_critical_chance_percent = 0
    battle.base_failure_chance_percent = 0
    battle.base_status_effects_chance_percent = 130

    battle.default_player_settings['stats']['hp'].rate = 3
    battle.default_player_settings['stats']['st'].rate = 20
    battle.default_player_settings['stats']['mp'].rate = 15


def setup_gamemode(battle):
    """Do procedures on the start of a game loop."""
    gamemodes = [
        '', 'All Moves', 'Avatar', 'Be Kirby', 'Footsies',
        'Fight Kirby', 'Hard'
    ]
    selected_gamemode = input_gamemode(gamemodes)
    change_gamemode(battle, selected_gamemode)
