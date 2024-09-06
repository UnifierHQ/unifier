import os
import sys
import shutil
import json
import time

if os.getcwd().endswith('/boot'):
    print('\x1b[31;1mYou are running the bootloader directly. Please run the run.sh file instead.\x1b[0m')
    sys.exit(1)

with open('boot/internal.json') as file:
    internal = json.load(file)

boot_config = {}
try:
    with open('boot_config.json') as file:
        boot_config = json.load(file)
except:
    pass

binary = boot_config['bootloader'].get('binary', 'py -3' if sys.platform == 'win32' else 'python3')
options = boot_config['bootloader'].get('options')
boot_file = boot_config['bootloader'].get('boot_file', internal["base_bootfile"])
autoreboot = boot_config['bootloader'].get('autoreboot', False)
threshold = boot_config['bootloader'].get('autoreboot_threshold', 60)

if not options:
    options = ''
else:
    options = ' ' + ' '.join(options)

if not '.install.json' in os.listdir():
    if os.path.isdir('update'):
        # unifier was likely updated from v2 or older
        print('\x1b[31;1mLegacy installation detected, skipping installer.\x1b[0m')
    else:
        # this installation is fresh
        print('\x1b[31;1mInstallation not detected, running installer...\x1b[0m')
        exit_code = os.system(f'{binary} boot/dep_installer.py{options}')
        if not exit_code == 0:
            sys.exit(exit_code)

        exit_code = os.system(f'{binary} boot/installer.py{options}')

        if not exit_code == 0:
            print('\x1b[31;1mInstaller has crashed or has been aborted.\x1b[0m')
            sys.exit(exit_code)

if not boot_file in os.listdir():
    if os.path.isdir('update'):
        print(f'\x1b[31;1m{boot_file} is missing, copying from update folder.\x1b[0m')
        try:
            shutil.copy2(f'update/{boot_file}', boot_file)
        except:
            print(f'\x1b[31;1mCould not find {boot_file}. Your installation may be corrupted.\x1b[0m')
            print(f'Please install a fresh copy of {internal["product_name"]} from {internal["repo"]}.')
            sys.exit(1)

first_boot = False
last_boot = time.time()

print(f'\x1b[36;1mStarting {internal["product_name"]}...\x1b[0m')

while True:
    exit_code = os.system(f'{binary} {boot_file}{options}')

    crash_reboot = False
    if not exit_code == 0:
        diff = time.time() - last_boot
        if autoreboot and first_boot or diff < threshold:
            print(f'\x1b[31;1m{internal["product_name"]} has crashed, restarting...\x1b[0m')
            crash_reboot = True
        else:
            print(f'\x1b[31;1m{internal["product_name"]} has crashed.\x1b[0m')
            sys.exit(exit_code)

    if crash_reboot or '.restart' in os.listdir():
        if '.restart' in os.listdir():
            os.remove('.restart')

        print(f'\x1b[33;1mRestarting {internal["product_name"]}...\x1b[0m')
    else:
        print(f'\x1b[36;1m{internal["product_name"]} shutdown successful.\x1b[0m')
        sys.exit(0)

    first_boot = True
    last_boot = time.time()
