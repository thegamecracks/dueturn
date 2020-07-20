"""Provides functions to interact with configuration files.

".json" is automatically appended when a config file is loaded.

Settings are stored in ./config.

===============  =========================================================
Function            Arguments: Description
===============  =========================================================
get_setting      (config_name, key): Get a specific setting.
load_config      (config_name, as_object): Load a config file.
save_config      (config_name, settings, overwrite): Save the config file.
setup_configs    (config_names): Initialize/verify multiple config files.
update_config    (config_name, settings): Update the config file.
verify_config    (config_name): Initialize/verify one config file.
write_setting    (config_name, key, value): Write a new setting.
===============  =========================================================
"""
from .ioutil import *
