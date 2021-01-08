from src.engine import Fighter


def create_player_fighters(
        battle, firstPlayerSettings, secondPlayerSettings,
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
        **firstPlayerSettings, battle_env=battle,
        is_player=True if firstis_player else False
    )
    secondFighter = Fighter(
        **secondPlayerSettings, battle_env=battle,
        is_player=True if secondis_player else False
    )

    return firstFighter, secondFighter
