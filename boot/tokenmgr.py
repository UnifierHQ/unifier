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

import traceback
import tomli
import tomli_w
import sys
import os
import getpass

try:
    sys.path.insert(0, '.')
    from utils import secrets
except:
    print('\x1b[31;1mSomething went wrong.\x1b[0m')
    sys.exit(1)


with open('config.toml', 'rb') as file:
    # noinspection PyTypeChecker
    config = tomli.load(file)

salt = config['system']['encrypted_env_salt']

try:
    tokenmgr = secrets.TokenStore(True, password=os.environ.get('UNIFIER_ENCPASS'))
except ValueError:
    print('\x1b[31;1mYou must provide a password.\x1b[0m')
    sys.exit(1)

if not tokenmgr.test_decrypt():
    print('\x1b[31;1mInvalid password. Your encryption password is needed to manage tokens.\x1b[0m')
    print('\x1b[31;1mIf you\'ve forgot your password, run the bootscript again with --clear-tokens\x1b[0m')
    sys.exit(1)

def add_token():
    identifier = input('Token identifier: ').upper()
    if identifier == '':
        print('\x1b[31;1mIdentifier cannot be empty.\x1b[0m')
        return
    token = getpass.getpass('Token: ')

    try:
        tokens = tokenmgr.add_token(identifier, token)
    except KeyError:
        print('\x1b[31;1mToken already exists.\x1b[0m')
        return

    print(f'\x1b[36;1mToken added successfully. You now have {tokens-1} tokens.\x1b[0m')

def replace_token():
    identifier = input('Token identifier: ').upper()
    if identifier == '':
        print('\x1b[31;1mIdentifier cannot be empty.\x1b[0m')
        return
    token = getpass.getpass('New token: ')
    password = getpass.getpass('Encryption password: ')

    print('\x1b[37;41;1mWARNING: THIS TOKEN WILL BE REPLACED!\x1b[0m')
    print('\x1b[33;1mThis process is irreversible. Once it\'s done, there\'s no going back!\x1b[0m')
    print()
    print('\x1b[33;1mProceed anyways? (y/n)\x1b[0m')

    try:
        confirm = input().lower()
        if not confirm == 'y':
            raise ValueError()
    except:
        print('\x1b[31;1mAborting.\x1b[0m')
        return

    try:
        tokenmgr.replace_token(identifier, token, password)
    except KeyError:
        print('\x1b[31;1mToken does not exist.\x1b[0m')
        return
    except ValueError:
        print('\x1b[31;1mInvalid password. Your encryption password is needed to replace or delete tokens.\x1b[0m')
        return

    print('\x1b[36;1mToken replaced successfully.\x1b[0m')


def delete_token():
    identifier = input('Token identifier: ').upper()
    if identifier == '':
        print('\x1b[31;1mIdentifier cannot be empty.\x1b[0m')
        return
    password = getpass.getpass('Encryption password: ')

    print('\x1b[37;41;1mWARNING: THIS TOKEN WILL BE DELETED!\x1b[0m')
    print('\x1b[33;1mThis process is irreversible. Once it\'s done, there\'s no going back!\x1b[0m')
    print()
    print('\x1b[33;1mProceed anyways? (y/n)\x1b[0m')

    try:
        confirm = input().lower()
        if not confirm == 'y':
            raise ValueError()
    except:
        print('\x1b[31;1mAborting.\x1b[0m')
        return

    try:
        tokens = tokenmgr.delete_token(identifier, password)
    except KeyError:
        print('\x1b[31;1mToken does not exist.\x1b[0m')
        return
    except ValueError:
        print('\x1b[31;1mInvalid password. Your encryption password is needed to replace or delete tokens.\x1b[0m')
        return

    print(f'\x1b[36;1mToken deleted successfully. You now have {tokens-1} tokens.\x1b[0m')

def list_tokens():
    print(f'\x1b[36;1mYou have {len(tokenmgr.tokens)} tokens.\x1b[0m')

    for index in range(len(tokenmgr.tokens)):
        token = tokenmgr.tokens[index]
        print(f'\x1b[36m{index + 1}. {token}\x1b[0m')

def reencrypt_tokens():
    salt = input('New salt integer (leave empty to keep current): ')
    if salt == '':
        salt = config['system']['encrypted_env_salt']
    else:
        try:
            salt = int(salt)
        except:
            print('\x1b[31;1mSalt must be an integer.\x1b[0m')
            return

    current_password = getpass.getpass('Current encryption password: ')
    password = getpass.getpass('New encryption password: ')
    confirm_password = getpass.getpass('Confirm encryption password: ')

    if not password == confirm_password:
        print('\x1b[31;1mPasswords do not match.\x1b[0m')
        return

    del confirm_password

    print('\x1b[37;41;1mWARNING: YOUR TOKENS WILL BE RE-ENCRYPTED!\x1b[0m')
    print('\x1b[33;1mYou will need to use your new encryption password to start Unifier.\x1b[0m')
    print('\x1b[33;1mThis process is irreversible. Once it\'s done, there\'s no going back!\x1b[0m')
    print()
    print('\x1b[33;1mProceed anyways? (y/n)\x1b[0m')

    try:
        confirm = input().lower()
        if not confirm == 'y':
            raise ValueError()
    except:
        print('\x1b[31;1mAborting.\x1b[0m')
        return

    try:
        tokenmgr.reencrypt(current_password, password)
    except ValueError:
        print('\x1b[31;1mInvalid password. Your current encryption password is needed to re-encrypt tokens.\x1b[0m')
        return

    if not salt == config['system']['encrypted_env_salt']:
        config['system']['encrypted_env_salt'] = salt
        with open('config.toml', 'wb') as file:
            tomli_w.dump(config, file)

    print('\x1b[36;1mTokens have been re-encrypted successfully.\x1b[0m')

def command_help():
    print('\x1b[36;1mCommands:\x1b[0m')
    for command in commands:
        print(f'\x1b[36m{command}\x1b[0m')


commands = {
    'add-token': add_token,
    'replace-token': replace_token,
    'delete-token': delete_token,
    'list-tokens': list_tokens,
    'reencrypt-tokens': reencrypt_tokens,
    'help': command_help,
    'exit': lambda: sys.exit(0)
}


list_tokens()

print('Type "help" for a list of commands.')

while True:
    try:
        command = input('> ').lower()
    except KeyboardInterrupt:
        break

    try:
        commands[command]()
    except KeyError:
        print('\x1b[33;1mInvalid command. Type "help" for a list of commands.\x1b[0m')
    except KeyboardInterrupt:
        pass
    except SystemExit:
        break
    except:
        traceback.print_exc()
        print('\x1b[31;1mAn error occurred.\x1b[0m')
