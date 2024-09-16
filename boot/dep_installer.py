import json
import os
import sys

install_option = sys.argv[1] if len(sys.argv) > 1 else None

install_options = [
    {
        'id': 'optimized',
        'name': '\U000026A1 Optimized',
        'description': 'Uses the latest Nextcord version and includes performance optimizations. Recommended for most users.',
        'default': True,
        'prefix': '',
        'color': '\x1b[35'
    },
    {
        'id': 'stable',
        'name': '\U0001F48E Stable',
        'description': 'Uses the latest stable Nextcord version without performance optimizations for best stability.',
        'default': False,
        'prefix': 'stable',
        'color': '\x1b[32'
    }
]

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

if prefix:
    code = os.system(f'{binary} -m pip install --user -U -r requirements_{prefix}.txt')
else:
    code = os.system(f'{binary} -m pip install --user -U -r requirements.txt')

if not code == 0:
    print('\x1b[31;1mCould not install dependencies.\x1b[0m')
    sys.exit(code)

print('\x1b[36;1mDependencies successfully installed.\x1b[0m')
sys.exit(0)
