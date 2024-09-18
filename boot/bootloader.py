import os
import sys
import shutil
import json
import time

reinstall = '--reinstall' in sys.argv

install_options = [
    {
        'id': 'optimized',
        'name': '\U000026A1 Optimized',
        'description': (
            'Uses the latest Nextcord version and includes performance optimizations. Recommended for most users.\n'+
            'Note: Due to an issue with Nextcord, this option temporarily uses the latest stable Nextcord version.'
        ),
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
    if os.path.exists('update'):
        shutil.copy2('update/boot_config.json', 'boot_config.json')
    with open('boot_config.json') as file:
        boot_config = json.load(file)

bootloader_config = boot_config.get('bootloader', {})

binary = bootloader_config.get('binary', 'py -3' if sys.platform == 'win32' else 'python3')
options = bootloader_config.get('options')
boot_file = bootloader_config.get('boot_file', internal["base_bootfile"])
autoreboot = bootloader_config.get('autoreboot', False)
threshold = bootloader_config.get('autoreboot_threshold', 60)

if not options:
    options = ''
else:
    options = ' ' + ' '.join(options)

if not '.install.json' in os.listdir() or reinstall:
    if os.path.isdir('update') and not reinstall:
        # unifier was likely updated from v2 or older
        print('\x1b[33;1mLegacy installation detected, skipping installer.\x1b[0m')
        with open('.install.json', 'w+') as file:
            json.dump(
                {
                    'product': internal["product"],
                    'setup': False,
                    'option': 'optimized'
                },
                file
            )
    else:
        # this installation is fresh
        if not reinstall:
            print('\x1b[33;1mInstallation not detected, running installer...\x1b[0m')

        if len(install_options) == 1:
            install_option = install_options[0]['id']
        else:
            print(f'\x1b[33;1mYou have {len(install_options)} install options available.\x1b[0m\n')

            for index in range(len(install_options)):
                option = install_options[index]
                print(f'{option["color"]};1m{option["name"]} (option {index})\x1b[0m')
                print(f'{option["color"]}m{option["description"]}\x1b[0m')

            print(f'\n\x1b[33;1mWhich installation option would you like to install? (0-{len(install_options)-1})\x1b[0m')

            try:
                install_option = int(input())

                if install_option < 0 or install_option >= len(install_options):
                    raise ValueError()
            except:
                print(f'\x1b[31;1mAborting.\x1b[0m')
                sys.exit(1)

            install_option = install_options[install_option]['id']

        print('\x1b[33;1mPlease review the following before continuing:\x1b[0m')
        print(f'- Product to install: {internal["product_name"]}')
        print(f'- Installation option: {install_option}')
        print(f'- Install directory: {os.getcwd()}')
        print(f'- Python command/binary: {binary}\n')
        print('\x1b[33;1mProceed with installation? (y/n)\x1b[0m')

        try:
            answer = input().lower()
        except:
            print(f'\x1b[31;1mAborting.\x1b[0m')
            sys.exit(1)

        if not answer == 'y':
            print(f'\x1b[31;1mAborting.\x1b[0m')
            sys.exit(1)

        exit_code = os.system(f'{binary} boot/dep_installer.py {install_option}{options}')
        if not exit_code == 0:
            sys.exit(exit_code)

        exit_code = os.system(f'{binary} boot/installer.py {install_option}{options}')

        if not exit_code == 0:
            print('\x1b[31;1mInstaller has crashed or has been aborted.\x1b[0m')
            sys.exit(exit_code)

        # sleep to prevent 429s
        time.sleep(5)

if not boot_file in os.listdir():
    if os.path.isdir('update'):
        print(f'\x1b[33;1m{boot_file} is missing, copying from update folder.\x1b[0m')
        try:
            shutil.copy2(f'update/{boot_file}', boot_file)
        except:
            print(f'\x1b[31;1mCould not find {boot_file}. Your installation may be corrupted.\x1b[0m')
            print(f'Please install a fresh copy of {internal["product_name"]} from {internal["repo"]}.')
            sys.exit(1)

first_boot = False
last_boot = time.time()

print(f'\x1b[36;1mStarting {internal["product_name"]}...\x1b[0m')

if '.restart' in os.listdir():
    os.remove('.restart')
    print('\x1b[33;1mAn incomplete restart was detected.\x1b[0m')

while True:
    exit_code = os.system(f'{binary} {boot_file}{options}')

    crash_reboot = False
    if not exit_code == 0:
        diff = time.time() - last_boot
        if autoreboot and first_boot and diff > threshold:
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

    # sleep to prevent 429s
    time.sleep(5)
