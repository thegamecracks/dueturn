import random


def update_player_names(
        firstPlayer, secondPlayer,
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
        if nameSet is None:
            raise TypeError('nameSet argument not provided to fill in '
                            'unspecified player names')
        set_random_player_names(nameSet)
