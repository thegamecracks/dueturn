from src import logs
from src import settings
from src.engine import fighter_ai
from src.textio import input_color, print_color

logger = logs.get_logger()

cfg_engine = settings.load_config('engine')


def get_AI(AIs):
    print_color(f"AIs: {', '.join(AIs[1:])}")
    AIs = [AI.casefold() for AI in AIs]

    AI = input_color(
        'Type an AI (case-insensitive) to change it,\n'
        f'or nothing to skip. {cfg_engine.GAME_SETUP_INPUT_COLOR}'
    ).casefold()

    while AI not in AIs:
        AI = input_color(
            'Unknown AI; check spelling: '
            f'{cfg_engine.GAME_SETUP_INPUT_COLOR}').casefold()

    logger.debug(f'Got AI from user: {AI!r}')
    return AI


def change_AI(battle, gamemode, AI):
    """Change settings based on the environment's AI."""
    def_settings = battle.default_player_settings
    if AI == '':
        if gamemode == 'footsies':
            def_settings['AI'] = fighter_ai.FighterAIFootsies
        return
    elif AI == 'sword first':
        def_settings['AI'] = fighter_ai.FighterAISwordFirst
    elif AI == 'dummy':
        def_settings['AI'] = fighter_ai.FighterAIDummy
    elif AI == 'mimic':
        def_settings['AI'] = fighter_ai.FighterAIMimic
    else:
        raise ValueError(f'{AI!r} is not a valid AI')
    logger.info(f'Set AI to {AI!r}')


def setup_AI(battle, gamemode):
    # AI options
    AIs = ['', 'Sword First', 'Dummy', 'Mimic']
    # Change AI options based on the gamemode
    # if they shouldn't be used
    if gamemode == 'avatar':
        AIs.remove('Sword First')
    elif gamemode == 'footsies':
        AIs.remove('Sword First')
    elif gamemode == 'be kirby':
        AIs.remove('Mimic')
    elif gamemode == 'fight kirby':
        AIs.remove('Mimic')
        AIs.remove('Sword First')

    # If there are available AI options, ask for them
    if AIs:
        selected_AI = get_AI(sorted(AIs))
        change_AI(battle, gamemode, selected_AI)
