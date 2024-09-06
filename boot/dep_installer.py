import json
import os
import sys

boot_config = {}
try:
    with open('boot_config.json') as file:
        boot_config = json.load(file)
except:
    pass

binary = boot_config['bootloader'].get('binary', 'py -3' if sys.platform == 'win32' else 'python3')

print('\x1b[36;1mInstalling dependencies, this may take a while...\x1b[0m')
code = os.system(f'{binary} -m pip install -U -r requirements.txt')

if not code == 0:
    print('\x1b[31;1mCould not install dependencies.\x1b[0m')
    sys.exit(code)

print('\x1b[36;1mDependencies successfully installed.\x1b[0m')
sys.exit(0)
