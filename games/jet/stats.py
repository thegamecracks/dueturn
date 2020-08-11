from src.engine import Bound, Stat
from src.engine.data.fighter_stats import get_defaults

stats = {
    'hp': Stat(
        'hp',
        'health',
        'hp',
        'health',
        'FLgree',
        1000,
        Bound(0, 1000),
        0
    ),
    'lo': Stat(
        'lo',
        'lockon',
        'lo',
        'lock-on',
        'Fred',
        0,
        Bound(0, 100),
        0
    )
}
evading_stats = {
    'fl': Stat(
        'fl',
        'flares',
        'fl',
        'flares',
        'FLyell',
        240,
        Bound(0, 240),
        0
    ),
    'ch': Stat(
        'ch',
        'chaff',
        'ch',
        'chaff',
        'Fwhite',
        240,
        Bound(0, 240),
        0
    )
}
missile_stats = {
    'di': Stat(
        'di',
        'distance',
        'di',
        'distance',
        'FLyell',
        1000,
        Bound(0, 1000),
        0
    ),
    'er': Stat(
        'er',
        'error',
        'er',
        'error',
        'FLred',
        0,
        Bound(0, 3600),
        0
    )
}
