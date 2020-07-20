import collections.abc
import json
import os
import pathlib

from src import logs

CONFIG_FILES = [
    'engine',
    'interface',
]

DEFAULT_ENGINE = {
    'GAME_AUTOPLAY_NORMAL_DELAY': 1,
    # RealNum: How long to wait when AI is automatically moving
    'GAME_AUTOPLAY_AI_DELAY': 2,
    # How long to pause when two AIs are fighting each other.

    'GAME_DISPLAY_PRINT_MOVES': False,
    # Automatically display moves for the player on their turn.
    'GAME_DISPLAY_SHOW_STAT_DIFFERENCE': True,
    # Show difference in stats from previous move
    #     instead of just stat regeneration.
    'GAME_DISPLAY_SPEED': 1,
    # The speed multiplier for pauses.
    'GAME_DISPLAY_STAT_GAP': 9,
    # The least amount of characters the fighters should be spaced apart
    # in fighter messages.
    'GAME_DISPLAY_STATS_COLOR_MODE': 1,
    # The color mode when displaying stats.
    # 0 = No colours on stats
    # 1 = Colour the stat number
    # 2 = Colour the line
    'GAME_DISPLAY_STATS_SHIFT': 8,
    # The amount of leading spaces when displaying the battle.
    'GAME_DISPLAY_TAB_LENGTH': 4,  # 8 console, 4 Discord
    # Length of tabs for when replacing spaces.
    'GAME_DISPLAY_USE_TABS': False,
    # Replace spaces with tabs when printing.

    'GAME_SETUP_INPUT_COLOR': '{FLcyan}'
    # The color to use when prompting at the start of a game.
}
DEFAULT_INTERFACE = {
    'AUTOCOMPLETE_KEY': 'tab',
    # The key to press for auto-completing commands.
    'MOVES_REQUIRE_EXACT_SEARCH': False,
    # Disable auto-completing move names.
}
DEFAULTS = {
    'engine': DEFAULT_ENGINE,
    'interface': DEFAULT_INTERFACE
}

logger = logs.get_logger()


class Configuration:
    pass


def _backup_settings(config_name):
    location = _make_config_location(config_name)
    location_backup = location + '.backup'

    logger.debug(f'Backing up {location}')

    with open(location_backup, 'w') as backup:
        with open(location) as broken:
            for line in iter(broken.readline, ''):
                backup.write(line)

    logger.debug(f'Backed up {location} to {location_backup}')


def _make_config_location(config_name):
    """Provide the location of a configuration file.
    
    Checks to make sure `config_name` is a known config.
    
    """
    if config_name not in CONFIG_FILES:
        raise ValueError(f'{config_name!r} is not a known configuration file')

    return f'./config/{config_name}.json'


def get_setting(config_name: str, key: str):
    """Get a specific value from a configuration."""
    logger.debug(f'Getting {key} from {config_name} config')
    settings = load_config(config_name, as_object=False)
    return settings[key]


def load_config(config_name: str, *, as_object=True, auto_setup=True):
    """Load a configuration."""
    logger.debug(f'Loading {config_name} config')

    location = _make_config_location(config_name)

    if not pathlib.Path(location).exists():
        if auto_setup:
            verify_config(config_name)
        # Else, let `open()` raise the FileNotFoundError

    with open(location) as f:
        config = json.load(f)
    
    if as_object:
        config_obj = Configuration()
        for k, v in config.items():
            setattr(config_obj, k, v)
        return config_obj
    return config


def save_config(config_name: str, settings: dict, overwrite=True):
    """Saves settings to a .json file."""

    def dump_json(location, settings):
        with open(location, mode='w') as f:
            json.dump(
                settings, f,
                indent=4,
                sort_keys=True
            )

    location = _make_config_location(config_name)

    logger.debug(f'Saving settings to {config_name} config')

    if not overwrite and pathlib.Path(location).exists():
        raise FileExistsError('Config file already exists')

    try:
        dump_json(location, settings)
    except FileNotFoundError:
        # Create directory and retry
        logger.debug('Config directory does not exist; '
                     'creating directory and retrying')
        os.mkdir('./config')
        dump_json(location, settings)


def update_config(config_name: str, settings: dict):
    """Update a config file with new settings."""
    logger.debug(f'Updating {config_name} config')

    config = load_config(config_name)
    config.update(obj)
    save_config(config_name, config)

    logger.debug(f'Updated {config_name} config')


def verify_config(config_name):
    location = _make_config_location(config_name)

    logger.debug(f'Verifying {config_name} config')

    # Get default settings
    default_settings = DEFAULTS[config_name]

    try:
        # Check that file can be found and parsed
        with open(location) as f:
            settings = json.load(f)
    except FileNotFoundError:
        logger.warning(f'Could not find {location};'
                       ' will create default config')
        save_config(config_name, default_settings)
    except json.decoder.JSONDecodeError as e:
        logger.warning(f'Failed to parse {location}: {e}')
        backup(config_name)
        save_config(config_name, default_settings)
    else:
        # Check that every key in the default settings exists in the file
        # If a key is missing, add it
        backed_up = False
        for k, v in default_settings.items():
            if k not in settings:
                logger.debug(f'Missing key {k!r}, adding default')
                if not backed_up:
                    _backup_settings(config_name)
                    backed_up = True
                settings[k] = v
        else:
            if backed_up:
                save_config(config_name, settings)
                logger.debug(f'Rebuilt {config_name}')
            else:
                logger.debug(f'Verified integrity of {config_name} config')

            return settings


def write_setting(config_name: str, key: str, value):
    """Write a new value to a given setting in the config file."""
    logger.debug(f'Writing {value!r} to {key} in {config_name}')
    config = load_config(config_name)
    config[key] = value
    save_config(config_name, config)


def setup_configs(config_names=None):
    """Generate/verify the settings.

    Args:
        config_names (Optional[Iterable[str]]): An optional iterable of
            config files to generate/verify. ".json" is automatically
            appended. If None, generates/verifies all known config files.

    """

    if config_names is None:
        # All settings
        logger.debug('Verifying all configurations')

        for fn in CONFIG_FILES:
            verify_config(fn)

        logger.debug('All configurations verified')
    elif (
                isinstance(config_names, collections.abc.Iterable)
                and not isinstance(config_names, str)
            ):
        # Several config files
        logger.debug(f'Verifying configurations: {config_names!r}')

        for fn in config_names:
            if fn in CONFIG_FILES:
                verify_config(fn)
            else:
                raise ValueError(f'Unknown config file {fn}')

        # Write to log
        count = len(config_names)
        if count == len(CONFIG_FILES):
            logger.debug('All configurations verified')
        else:
            s = 's' if count != 1 else ''
            logger.debug('{count} configuration file{s} verified')
    else:
        raise TypeError(f'Unknown config_names argument given: {config_names!r}')
