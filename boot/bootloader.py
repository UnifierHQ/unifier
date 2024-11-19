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

import os
import sys
import shutil
import json
import time
import getpass
import subprocess
from pathlib import Path

if sys.version_info.major < 3 or sys.version_info.minor < 9:
    print('\x1b[31;1mThis version of Python is unsupported. You need Python 3.9 or newer.\x1b[0m')
    sys.exit(1)

reinstall = '--reinstall' in sys.argv
depinstall = '--install-deps' in sys.argv
manage_tokens = '--tokens' in sys.argv
clear_tokens = '--clear-tokens' in sys.argv

if os.getcwd().endswith('/boot'):
    print('\x1b[31;1mYou are running the bootloader directly. Please run the run.sh file instead.\x1b[0m')
    sys.exit(1)

with open('boot/internal.json') as file:
    internal = json.load(file)

install_options = internal['options']

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

cgroup = Path('/proc/self/cgroup')
uses_docker = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()

class PythonInstallation:
    def __init__(self, major, minor, patch, filepath, default=False, emulated=False, venv=False):
        self.__version = (major, minor, patch)
        self.__filepath = filepath
        self.__default = default
        self.__emulated = emulated
        self.__venv = venv

    def __str__(self):
        extras = ''
        if self.__default:
            extras += ' \U00002B50'
        if self.__emulated:
            extras += ' (Emulated x86_64)'
        return f'Python {self.__version[0]}.{self.__version[1]}.{self.__version[2]} @ {self.__filepath}{extras}'

    @property
    def version(self):
        return self.__version

    @property
    def emulated(self):
        return self.__emulated

    @property
    def filepath(self):
        return self.__filepath

    @property
    def default(self):
        return self.__default

    @property
    def venv(self):
        return self.__venv

    @property
    def supported(self):
        return self.__version >= (3, 9, 0)

def check_for_python(path, found=None, venv=False):
    versions = []
    blacklist = ['-config', 't', 't-config', 't-intel64']

    if not found:
        found = []

    defaults = [
        file for file in
        subprocess.check_output([f'whereis', 'python3']).decode('utf-8').replace('\n','').split(' ')
        if not file == 'python3:'
    ]

    try:
        for item in os.listdir(path):
            emulated = False

            if not item.startswith('python'):
                continue
            if True in [item.endswith(blacklisted) for blacklisted in blacklist]:
                continue

            if item.endswith('-intel64'):
                if not os.uname().machine == 'x86_64':
                    emulated = True

            try:
                output = subprocess.check_output([f'{path}/{item}', '--version'])
            except:
                continue

            versiontext = output.decode('utf-8').replace('\n','').split(' ')[1]
            major, minor, patch = versiontext.split('.')

            if not patch.isdigit():
                fixed = ''
                for char in patch:
                    if not char.isdigit():
                        return
                    fixed += char
                patch = fixed

            installation = PythonInstallation(
                int(major), int(minor), int(patch), f'{path}/{item}', default=f'{path}/{item}' in defaults,
                emulated=emulated, venv=venv
            )
            if not installation in versions and not installation in found:
                versions.append(installation)
    except FileNotFoundError:
        return []

    return versions


if boot_config.get('ptero') is None and uses_docker:
    print('\x1b[33;1mWe detected that you are running Unifier in a Docker container.\x1b[0m')
    print('\x1b[33;1mThis may mean that you are using Pterodactyl/Pelican panel to run your server.\x1b[0m')
    print('\x1b[33;1mIf this is the case, we recommend enabling Pterodactyl support.\x1b[0m')
    print('\x1b[33;1mEnable Pterodactyl support? (y/n)\x1b[0m')

    try:
        answer = input().lower()
        enable_ptero = answer == 'y'

        if answer == 'y':
            boot_config['ptero'] = True
        elif answer == 'n':
            boot_config['ptero'] = False
        else:
            print('\x1b[33;1mInvalid answer, defaulting to no. We will ask you again on next boot.\x1b[0m')

        if answer == 'y' or answer == 'n':
            with open('boot_config.json', 'w+') as file:
                # noinspection PyTypeChecker
                json.dump(boot_config, file, indent=4)
    except KeyboardInterrupt:
        print('\x1b[31;1mAborting.\x1b[0m')
        sys.exit(1)

    ptero_support = uses_docker and enable_ptero
else:
    ptero_support = uses_docker and boot_config.get('ptero', False)

if not options:
    options = ''
else:
    options = ' ' + ' '.join(options)

if not '.install.json' in os.listdir() or reinstall or depinstall:
    if os.path.isdir('update') and not reinstall and not depinstall:
        # unifier was likely updated from v2 or older
        print('\x1b[33;1mLegacy installation detected, skipping installer.\x1b[0m')
        with open('.install.json', 'w+') as file:
            # noinspection PyTypeChecker
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
        if manage_tokens or clear_tokens:
            print(f'\x1b[31;1mNo Unifier installation was detected.\x1b[0m')
            sys.exit(1)
        elif not depinstall:
            if not reinstall:
                print('\x1b[33;1mInstallation not detected, running installer...\x1b[0m')

            if len(install_options) == 1:
                install_option = install_options[0]['id']
            else:
                print(f'\x1b[33;1mYou have {len(install_options)} install options available.\x1b[0m\n')

                for index in range(len(install_options)):
                    option = install_options[index]
                    print(f'\x1b[{option["color"]};1m{option["name"]} (option {index})\x1b[0m')
                    print(f'\x1b[{option["color"]}m{option["description"]}\x1b[0m')

                print(f'\n\x1b[33;1mWhich installation option would you like to install? (0-{len(install_options)-1})\x1b[0m')

                try:
                    install_option = int(input())

                    if install_option < 0 or install_option >= len(install_options):
                        raise ValueError()
                except:
                    print(f'\x1b[31;1mAborting.\x1b[0m')
                    sys.exit(1)

                install_option = install_options[install_option]['id']

            if not uses_docker and not sys.platform == 'win32':
                print('\x1b[33;1mDetecting python installations...\x1b[0m')
                installed = []
                installed.extend(check_for_python('/usr/bin'))
                installed.extend(check_for_python('/usr/local/bin', found=installed))

                for item in os.listdir():
                    if not os.path.isdir(item):
                        continue

                    installed.extend(check_for_python(f'{item}/bin', found=installed, venv=True))

                if len(installed) <= 1:
                    print('\x1b[33;1mOnly the default Python installation was detected, using default.\x1b[0m')
                else:
                    installed.sort(key=lambda x: x.version, reverse=True)
                    print(f'\x1b[33;1mFound {len(installed)} available Python installations:\x1b[0m')
                    for index in range(len(installed)):
                        print(f'\x1b[33m({index+1}) {installed[index]}\x1b[0m')

                    print(f'\n\x1b[33;1mWhich version would you like to use? (1-{len(installed)})\x1b[0m')

                    choice = None
                    while True:
                        try:
                            choice = int(input()) - 1
                            if choice < 0 or choice >= len(installed):
                                raise ValueError()
                        except ValueError:
                            print(f'\x1b[31;1mInvalid answer, try again.\x1b[0m')
                            continue
                        except KeyboardInterrupt:
                            print(f'\x1b[31;1mAborting.\x1b[0m')
                            sys.exit(1)
                        break

                    binary = installed[choice].filepath
                    if installed[choice].venv:
                        if not boot_config.get('bootloader'):
                            boot_config.update({'bootloader': {}})
                        boot_config['bootloader'].update({'binary': binary})
                        boot_config['bootloader'].update({'global_dep_install': True})
                        with open('boot_config.json', 'w+') as file:
                            # noinspection PyTypeChecker
                            json.dump(boot_config, file, indent=4)
                    else:
                        bootloader_exists = os.path.isdir('.venv')

                        if bootloader_exists:
                            print('\n\x1b[33;1mAn existing virtual environment was found. Would you like to use it? (y/n)\x1b[0m')
                        else:
                            print('\n\x1b[33;1mWould you like to use a virtual environment? This is highly recommended as this prevents\x1b[0m')
                            print('\x1b[33;1mglobal packages from breaking and allows for easier recovery. (y/n)\x1b[0m')

                        use_venv = False
                        while True:
                            try:
                                choice = input().lower()
                                if not choice == 'y' and not choice == 'n':
                                    raise ValueError()
                            except ValueError:
                                print(f'\x1b[31;1mInvalid answer, try again.\x1b[0m')
                                continue
                            except KeyboardInterrupt:
                                print(f'\x1b[31;1mAborting.\x1b[0m')
                                sys.exit(1)

                            use_venv = choice == 'y'
                            break

                        if not boot_config.get('bootloader'):
                            boot_config.update({'bootloader': {}})

                        if use_venv:
                            if not bootloader_exists:
                                print(f'\n\x1b[33;1mCreating virtual environment in {os.getcwd()}/.venv...\x1b[0m')
                                code = os.system(f'{binary} -m venv .venv')
                                if code == 0:
                                    print(f'\x1b[36;1mVirtual environment created successfully.\x1b[0m')
                                else:
                                    print(f'\x1b[31;1mFailed to create virtual environment, aborting.\x1b[0m')
                                    sys.exit(1)
                            binary = './.venv/bin/python'
                            boot_config['bootloader'].update({'binary': binary})
                            boot_config['bootloader'].update({'global_dep_install': True})
                        else:
                            boot_config['bootloader'].update({'binary': binary})
                            boot_config['bootloader'].update({'global_dep_install': False})

                        with open('boot_config.json', 'w+') as file:
                            # noinspection PyTypeChecker
                            json.dump(boot_config, file, indent=4)

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
        else:
            try:
                with open('.install.json') as file:
                    install_data = json.load(file)
            except:
                print('\x1b[31;1mPlease install Unifier first.\x1b[0m')
                sys.exit(1)

            print('\x1b[33;1mInstalling dependencies...\x1b[0m')

            install_option = install_data['option']

        exit_code = os.system(f'{binary} boot/dep_installer.py {install_option}{options}')
        if not exit_code == 0:
            sys.exit(exit_code)

        if depinstall:
            sys.exit(0)

        exit_code = os.system(f'{binary} boot/installer.py {install_option}{options}')

        if not exit_code == 0:
            print('\x1b[31;1mInstaller has crashed or has been aborted.\x1b[0m')
            sys.exit(exit_code)

        # sleep to prevent 429s
        time.sleep(5)

encryption_password = ''

if clear_tokens:
    print('\x1b[37;41;1mWARNING: ALL TOKENS WILL BE CLEARED!\x1b[0m')
    print('\x1b[33;1mYou should only clear your tokens if you forgot your password.\x1b[0m')
    print('\x1b[33;1mThis process is irreversible. Once it\'s done, there\'s no going back!\x1b[0m')
    print()
    print('\x1b[33;1mProceed anyways? (y/n)\x1b[0m')

    try:
        confirm = input().lower()
        if not confirm == 'y':
            raise ValueError()
    except:
        print('\x1b[31;1mAborting.\x1b[0m')
        sys.exit(1)

    encryption_password = getpass.getpass('New password: ')
    confirm_password = getpass.getpass('Confirm new password: ')
    if not encryption_password == confirm_password:
        print('\x1b[31;1mPasswords do not match.\x1b[0m')
        sys.exit(1)

    os.remove('.encryptedenv')
    os.environ['UNIFIER_ENCPASS'] = str(encryption_password)
    os.system(f'{binary} boot/tokenmgr.py')
    sys.exit(0)

if manage_tokens:
    encryption_password = getpass.getpass('Password: ')
    os.environ['UNIFIER_ENCPASS'] = str(encryption_password)
    os.system(f'{binary} boot/tokenmgr.py')
    sys.exit(0)

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

restart_options = ''

choice = None

while True:
    plain = os.path.isfile('.env')
    encrypted = os.path.isfile('.encryptedenv')
    if not choice is None and os.environ.get('UNIFIER_ENCPASS') is None:
        # choice is set but not the password, likely due to wrong password
        if ptero_support:
            print(f'\x1b[36;1mPlease enter your encryption password using the console input.\x1b[0m')
        encryption_password = str(getpass.getpass('Password: '))
        os.environ['UNIFIER_ENCPASS'] = str(encryption_password)
    elif not choice is None:
        # choice is set and password is correct
        if choice == 1:
            # do not reencrypt .env
            choice = 0
    elif plain and encrypted:
        print('\x1b[33;1m.env and .encryptedenv are present. What would you like to do?\x1b[0m')
        print('\x1b[33m1. Use .encryptedenv')
        print('2. Replace .encryptedenv with .env\x1b[0m')

        try:
            choice = int(input()) - 1
            if choice < 0 or choice > 1:
                raise ValueError()
        except:
            print(f'\x1b[31;1mAborting.\x1b[0m')
            sys.exit(1)
    elif plain:
        print(
            '\x1b[33;1mNo .encryptedenv file could not be found, but a .env file was found, .env will be encrypted and used.\x1b[0m')
        choice = 1
    elif encrypted:
        choice = 0
    else:
        print('\x1b[31;1mNo .env or .encryptedenv file could be found.\x1b[0m')
        print('More info: https://wiki.unifierhq.org/setup-selfhosted/getting-started/unifier#set-bot-token')
        sys.exit(1)

    if choice == 0:
        encryption_password = os.environ.get('UNIFIER_ENCPASS')
        if not encryption_password:
            encryption_password = getpass.getpass('Password: ')

        os.environ['UNIFIER_ENCPASS'] = str(encryption_password)
    elif choice == 1:
        encryption_password = getpass.getpass('New password: ')
        confirm_password = getpass.getpass('Confirm password: ')
        os.environ['UNIFIER_ENCPASS'] = str(encryption_password)
        del confirm_password
        should_encrypt = True

    os.environ['UNIFIER_ENCOPTION'] = str(choice)

    exit_code = os.system(f'{binary} {boot_file}{restart_options}{options}')

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
            x = open('.restart', 'r', encoding='utf-8')
            data = x.read().split(' ')
            x.close()

            restart_options = (' ' + data[1]) if len(data) > 1 else ''
            os.remove('.restart')

        print(f'\x1b[33;1mRestarting {internal["product_name"]}...\x1b[0m')
        if encryption_password:
            os.environ['UNIFIER_ENCPASS'] = encryption_password
    else:
        print(f'\x1b[36;1m{internal["product_name"]} shutdown successful.\x1b[0m')
        del encryption_password
        sys.exit(0)

    first_boot = True
    last_boot = time.time()

    # sleep to prevent 429s
    time.sleep(5)
