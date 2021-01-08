from src.utility import dict_copy


def player_create_default_settings(battle_env, initialize_AI=True):
    """Creates the default player settings.

    It copies default_player_settings for both players,
    then updates them with default_player_settings_A and
    default_player_settings_B for their respective Fighters.

    Args:
        battle_env (src.engine.BattleEnvironment):
            The battle environment that the default player settings
            is being taken from.
        initialize_AI (bool): If True, initializes the AI
            copied settings.

    Returns:
        Tuple[Dict, Dict]: The first and second players settings.

    """
    firstPlayerSettings = dict_copy(battle_env.default_player_settings)
    firstPlayerSettings.update(
        dict_copy(battle_env.default_player_settings_A)
    )
    secondPlayerSettings = dict_copy(battle_env.default_player_settings)
    secondPlayerSettings.update(
        dict_copy(battle_env.default_player_settings_B)
    )

    if initialize_AI:
        if 'AI' in firstPlayerSettings:
            firstPlayerSettings['AI'] = firstPlayerSettings['AI']()
        if 'AI' in secondPlayerSettings:
            secondPlayerSettings['AI'] = secondPlayerSettings['AI']()

    return firstPlayerSettings, secondPlayerSettings
