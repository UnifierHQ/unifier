"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import os
import sys

install_option = sys.argv[1] if len(sys.argv) > 1 else None

with open('boot/internal.json') as file:
    internal = json.load(file)

install_options = internal['options']

prefix = None

if not install_option:
    for option in install_options:
        if option['default']:
            install_option = option['id']
            break
else:
    for option in install_options:
        if option['id'] == install_option:
            prefix = option['prefix']
            if prefix == '':
                prefix = None
            break

boot_config = {}
try:
    with open('boot_config.json') as file:
        boot_config = json.load(file)
except:
    pass

binary = boot_config['bootloader'].get('binary', 'py -3' if sys.platform == 'win32' else 'python3')

print('\x1b[36;1mInstalling dependencies, this may take a while...\x1b[0m')

user_arg = ' --user' if not boot_config['bootloader'].get('global_dep_install',False) else ''

if prefix:
    code = os.system(f'{binary} -m pip install{user_arg} -U -r requirements_{prefix}.txt')
else:
    code = os.system(f'{binary} -m pip install{user_arg} -U -r requirements.txt')

for plugin in os.listdir('plugins'):
    if not plugin.endswith('.json') or plugin == 'system.json':
        continue

    try:
        with open(f'plugins/{plugin}') as file:
            plugin_data = json.load(file)
    except:
        continue

    if len(plugin_data.get('requirements', [])) > 0:
        code = os.system(f'{binary} -m pip install{user_arg} -U {" ".join(plugin_data["requirements"])}')
        if not code == 0:
            break

if not code == 0:
    print('\x1b[31;1mCould not install dependencies.\x1b[0m')
    print('\x1b[31;1mIf you\'re using a virtualenv, you might want to set global_dep_install to true in bootloader configuration to fix this.\x1b[0m')
    sys.exit(1)

print('\x1b[36;1mDependencies successfully installed.\x1b[0m')
sys.exit(0)
