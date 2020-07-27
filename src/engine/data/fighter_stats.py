"""Contains the standard stats that Fighters use."""
from ..stat import Stat
from ..bound import Bound

ALL_STATS = {
    'hp': Stat(
        'hp',
        'health',
        'hp',
        'health',
        'FLgree',
        100,
        Bound(0, 100),
        1
    ),
    'st': Stat(
        'st',
        'stamina',
        'st',
        'stamina',
        'FLyell',
        100,
        Bound(0, 100),
        10
    ),
    'mp': Stat(
        'mp',
        'mana',
        'mp',
        'mana',
        'FLcyan',
        100,
        Bound(0, 100),
        10
    ),
}
ALL_STAT_INFOS = {k: v.to_stat_info() for k, v in ALL_STATS.items()}


def get_defaults():
    """Return a copy of ALL_STATS."""
    return {k: v.copy() for k, v in ALL_STATS.items()}


def get_stat(int_short):
    """Return a copy of one of the stats in ALL_STATS."""
    result = ALL_STATS.get(int_short)
    if result is None:
        raise ValueError(f'Unknown stat {int_short}')
    return result.copy()


def create_stat(int_short, value, bound, rate):
    """Copy a stat in ALL_STATS and assign a new value, bound, and rate."""
    result = ALL_STATS.get(int_short)
    if result is None:
        return
    return result.copy(value, bound, rate)


def create_default_stats(**kwargs):
    """Create new stats based on ALL_STAT_INFOS.

    Args:
        **kwargs (Dict[str, Tuple[int, Bound, int]]):
            A dictionary with the keys specifying `int_short` and the values
            specifiying each stat's value, bound, and rate.

    """
    stats = {}
    for int_short, args in kwargs.items():
        value, bound, rate = args

        if isinstance(bound, int):
            # Convert int into a Bound object, assuming left bound to be 0
            bound = Bound(0, bound)
        elif not isinstance(bound, Bound):
            raise TypeError('Expected bound argument to be of type '
                            f'{Bound.__class__.__name__} but received '
                            f'{bound!r} of type {type(bound)}')

        result = ALL_STAT_INFOS.get(int_short)
        if result is None:
            raise ValueError(f'Unknown stat {int_short}')

        stats[int_short] = result.to_stat(value, bound, rate)

    return stats
