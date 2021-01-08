"""Provides functions to interact with configuration files.

".json" is automatically appended to config_name.

Settings are stored in /config.

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

__copyright__ = """
    Dueturn - A text-based two-player battle engine.
    Copyright (C) 2020  thegamecracks

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
