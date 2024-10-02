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

import asyncio
import sys
import getpass
import json
import nextcord
import tomli
import tomli_w
import traceback
from nextcord.ext import commands
from utils import secrets

install_option = sys.argv[1] if len(sys.argv) > 1 else None

with open('boot/internal.json') as file:
    internal = json.load(file)

install_options = internal['options']

if not install_option:
    for option in install_options:
        if option['default']:
            install_option = option['id']
            break

bot = commands.Bot(
    command_prefix='u!',
    intents=nextcord.Intents.all()
)

user_id = 0
server_id = 0

if sys.version_info.minor < internal['required_py_version']:
    print(f'\x1b[31;49mCannot install {internal["product_name"]}. Python 3.{internal["required_py_version"]} or later is required.\x1b[0m')
    sys.exit(1)

@bot.event
async def on_ready():
    global server_id

    print(f'\x1b[33;1mIs {bot.user.name} ({bot.user.id}) the correct bot? (y/n)\x1b[0m')
    answer = input().lower()

    if not answer == 'y':
        print(f'\x1b[31;1mAborting.\x1b[0m')
        sys.exit(1)

    print(f'\x1b[36;1mAttempting to DM user {user_id}...\x1b[0m')

    user = bot.get_user(user_id)

    for guild in bot.guilds:
        for member in guild.members:
            if member.id == user_id:
                server_id = guild.id
                break

        if not server_id == 0:
            break

    available = 10
    tries = 0

    while True:
        try:
            await user.send('If you can see this message, please return to the console, then type "y".')
            break
        except:
            tries += 1

            if tries >= available:
                print(f'\x1b[31;1mCould not DM user after {available} attempts, aborting.\x1b[0m')
                sys.exit(1)
            if user:
                print(f'\x1b[33;1mCould not DM user. Please enable your DMs for a server you and the bot share.\x1b[0m')
            else:
                print(f'\x1b[33;1mCould not find user. Please add the bot to a server you are in.\x1b[0m')
                print(f'Use this link to add the bot: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=537259008&scope=bot')
            print(f'\x1b[33;1mTrying again in 30 seconds, {available-tries} tries remaining. Press Ctrl+C to abort.\x1b[0m')

            try:
                await asyncio.sleep(30)
            except:
                print(f'\x1b[31;1mAborting.\x1b[0m')
                sys.exit(1)

    print(f'\x1b[33;1mDid you receive a DM from the bot? (y/n)\x1b[0m')
    answer = input().lower()

    if not answer == 'y':
        print(f'\x1b[31;1mAborting.\x1b[0m')
        sys.exit(1)

    print('\x1b[36;1mOwner verified successfully, closing bot.\x1b[0m')
    await bot.close()

print('\x1b[33;1mWe need the ID of the user who will be the instance owner. In most cases this is your user ID.\x1b[0m')
print(f'\x1b[33;1mThe owner will have access to special commands for maintaining your {internal["product_name"]} instance.\x1b[0m')
print('\x1b[33;1mTo copy your ID, go to your Discord settings, then Advanced, then enable Developer mode.\x1b[0m')

while True:
    try:
        user_id = int(input())
        break
    except KeyboardInterrupt:
        print('\x1b[31;49mAborted.\x1b[0m')
        sys.exit(1)
    except:
        print('\x1b[31;49mThis isn\'t an integer, try again.\x1b[0m')

print('\x1b[33;1mWe will now ask for your bot token.\x1b[0m')
print('\x1b[33;1mThe user verifier will use this token to log on to Discord.\x1b[0m\n')
print(f'\x1b[37;41;1mWARNING: DO NOT SHARE THIS TOKEN, NOT EVEN WITH {internal["maintainer"].upper()}.\x1b[0m')
print(f'\x1b[31;49m{internal["maintainer"]} will NEVER ask for your token. Please keep this token to yourself and only share it with trusted instance maintainers.\x1b[0m')
print('\x1b[31;49mFor security reasons, the installer will hide the input.\x1b[0m')

token = getpass.getpass()

encryption_password = ''
salt = ''

print('\x1b[33;1mWe will now ask for the token encryption salt. This must be an integer.\x1b[0m')
print('\x1b[33;1mAs of Unifier v3.2.0, all tokens must be stored encrypted, even if it\'s stored as an environment variable.\x1b[0m')

while True:
    try:
        salt = int(input())
        break
    except KeyboardInterrupt:
        print('\x1b[31;49mAborted.\x1b[0m')
        sys.exit(1)
    except:
        print('\x1b[31;49mThis isn\'t an integer, try again.\x1b[0m')

print('\x1b[33;1mWe will now ask for the token encryption password. This is NOT your bot token.\x1b[0m')
print(f'\x1b[37;41;1mWARNING: DO NOT SHARE THIS TOKEN, NOT EVEN WITH {internal["maintainer"].upper()}.\x1b[0m')
print(f'\x1b[31;49m{internal["maintainer"]} will NEVER ask for your encryption password. Please keep this password to yourself and only share it with trusted instance maintainers.\x1b[0m')
print('\x1b[31;49mFor security reasons, the installer will hide the input.\x1b[0m')

encryption_password = getpass.getpass()

print('\x1b[36;1mStarting bot...\x1b[0m')

try:
    bot.run(token)
except:
    traceback.print_exc()
    print('\x1b[31;49mLogin failed. Perhaps your token is invalid?\x1b[0m')
    print('\x1b[31;49mMake sure all privileged intents are enabled for the bot.\x1b[0m')
    sys.exit(1)

tokenstore = secrets.TokenStore(False, password=encryption_password, salt=salt, content_override={'TOKEN': token})
print('\x1b[36;1mYour tokens have been stored securely.\x1b[0m')

with open('config.toml', 'rb') as file:
    config = tomli.load(file)

config['roles']['owner'] = user_id
config['moderation']['home_guild'] = server_id

with open('config.toml', 'wb') as file:
    tomli_w.dump(config, file)

with open('.install.json','w+') as file:
    # noinspection PyTypeChecker
    json.dump({'product': internal["product"],'setup': False,'option': install_option}, file)

print(f'\x1b[36;1m{internal["product_name"]} installed successfully.\x1b[0m')
