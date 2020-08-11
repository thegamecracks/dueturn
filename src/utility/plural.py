def plural(n, suffix='s', natural_only=False):
    """Return a plural suffix if a number should be read as plural.

    Args:
        n (Union[int, float]): The number to check.
        suffix (str): The plural suffix to return
            if `n` should be referred to plurally.
        natural_only (bool): If True, return plural if n != 1.
            Otherwise, return plural if abs(n) != 1.

    Returns:
        str (Union[Literal[''], suffix])

    """
    if natural_only and n == 1:
        return ''
    elif abs(n) == 1:
        return ''
    return suffix
