"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

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

# WARNING: EDITING THIS FILE MAY BE DANGEROUS!!!
#
# System Manager (sysmgr.py) contains certain admin commands (such as
# eval) which, if used maliciously, may damage your Unifier instance,
# and even your system! These commands are only to be used by the
# instance owner, and NOT anyone else.
#
# We can't stop you from modifying this file (it's licensed under the
# AGPLv3 license anyway), but we still STRONGLY recommend you DO NOT
# modify this, unless you're ABSOLUTELY SURE of what you're doing.

import nextcord
from nextcord.ext import commands, tasks
import inspect
import textwrap
from contextlib import redirect_stdout
from utils import log, ui, langmgr, restrictions as r
import logging
import ujson as json
import os
import sys
import traceback
import io
import re
import ast
import importlib
import math
import asyncio
import discord_emoji
import threading
import hashlib
import orjson
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto import Random as CryptoRandom
from Crypto.Util.Padding import pad, unpad
import base64
import random
import requests
import time
import datetime

restrictions = r.Restrictions()
language = langmgr.partial()
language.load()

# Below are attributions to the works we used to build Unifier (including our own).
# If you've modified Unifier to use more works, please add it here.
attribution = {
    'unifier': {
        'author': 'UnifierHQ',
        'description': 'A fast and versatile Discord bot connecting servers and platforms',
        'repo': 'https://github.com/UnifierHQ/unifier',
        'license': 'AGPLv3',
        'license_url': 'https://github.com/UnifierHQ/unifier/blob/main/LICENSE.txt'
    },
    'nextcord': {
        'author': 'Nextcord',
        'description': 'A Python wrapper for the Discord API forked from discord.py',
        'repo': 'https://github.com/nextcord/nextcord',
        'license': 'MIT',
        'license_url': 'https://github.com/nextcord/nextcord/blob/master/LICENSE'
    },
    'revolt.py': {
        'author': 'Revolt',
        'description': 'Python wrapper for https://revolt.chat',
        'repo': 'https://github.com/revoltchat/revolt.py',
        'license': 'MIT',
        'license_url': 'https://github.com/revoltchat/revolt.py/blob/master/LICENSE'
    },
    'guilded.py': {
        'author': 'shay',
        'description': 'Asynchronous Guilded API wrapper for Python',
        'repo': 'https://github.com/shayypy/guilded.py',
        'license': 'MIT',
        'license_url': 'https://github.com/shayypy/guilded.py/blob/master/LICENSE'
    },
    'aiofiles': {
        'author': 'Tin Tvrtković',
        'description': 'File support for asyncio',
        'repo': 'https://github.com/Tinche/aiofiles',
        'license': 'Apache-2.0',
        'license_url': 'https://github.com/Tinche/aiofiles/blob/main/LICENSE'
    },
    'py-cpuinfo': {
        'author': 'Matthew Jones',
        'description': 'A module for getting CPU info with pure Python',
        'repo': 'https://github.com/workhorsy/py-cpuinfo',
        'license': 'MIT',
        'license_url': 'https://github.com/workhorsy/py-cpuinfo/blob/master/LICENSE'
    },
    'tld': {
        'author': 'Artur Barseghyan',
        'description': 'Extracts the top level domain (TLD) from the URL given.',
        'repo': 'https://github.com/barseghyanartur/tld',
        'license': 'LGPLv2.1',
        'license_url': 'https://github.com/barseghyanartur/tld/blob/master/LICENSE_LGPL_2.1.txt'
    },
    'jellyfish': {
        'author': 'James Turk',
        'description': '\U0001FABC a python library for doing approximate and phonetic matching of strings.',
        'repo': 'https://github.com/jamesturk/jellyfish',
        'license': 'MIT',
        'license_url': 'https://github.com/jamesturk/jellyfish/blob/main/LICENSE'
    },
    'uvloop': {
        'author': 'magicstack',
        'description': 'Ultra fast asyncio event loop.',
        'repo': 'https://github.com/MagicStack/uvloop',
        'license': 'MIT',
        'license_url': 'https://github.com/MagicStack/uvloop/blob/master/LICENSE-MIT'
    },
    'compress_json': {
        'author': 'Luca Cappelletti',
        'description': 'The missing Python utility to read and write large compressed JSONs.',
        'repo': 'https://github.com/LucaCappelletti94/compress_json',
        'license': 'MIT',
        'license_url': 'https://github.com/LucaCappelletti94/compress_json/blob/master/LICENSE'
    },
    'python-dotenv': {
        'author': 'Saurabh Kumar',
        'description': (
            'Reads key-value pairs from a .env file and can set them as environment variables. It helps in developing '+
            'applications following the 12-factor principles.'
        ),
        'repo': 'https://github.com/theskumar/python-dotenv',
        'license': 'BSD-3-Clause',
        'license_url': 'https://github.com/theskumar/python-dotenv/blob/master/LICENSE'
    },
    'requests': {
        'author': 'Python Software Foundation',
        'description': 'A simple, yet elegant, HTTP library.',
        'repo': 'https://github.com/psf/requests',
        'license': 'Apache-2.0',
        'license_url': 'https://github.com/psf/requests/blob/main/LICENSE'
    },
    'ultrajson': {
        'author': 'UltraJSON',
        'description': 'Ultra fast JSON decoder and encoder written in C with Python bindings',
        'repo': 'https://github.com/ultrajson/ultrajson',
        'license': 'Custom',
        'license_url': 'https://github.com/ultrajson/ultrajson/blob/main/LICENSE.txt'
    },
    'emoji': {
        'author': 'Taehoon Kim',
        'description': 'emoji terminal output for Python',
        'repo': 'https://github.com/carpedm20/emoji',
        'license': 'BSD-3-Clause',
        'license_url': 'https://github.com/carpedm20/emoji/blob/main/LICENSE.txt'
    },
    'discord-emoji': {
        'author': 'Nanashi.',
        'description': 'This lib converts discord emoji and unicode emoji.',
        'repo': 'https://github.com/sevenc-nanashi/discord-emoji',
        'license': 'MIT',
        'license_url': 'https://github.com/sevenc-nanashi/discord-emoji/blob/main/LICENSE.txt'
    },
    'pycryptodome': {
        'author': 'Helder Eijs',
        'description': 'A self-contained cryptographic library for Python',
        'repo': 'https://github.com/Legrandin/pycryptodome',
        'license': 'BSD-2-Clause',
        'license_url': 'https://github.com/Legrandin/pycryptodome/blob/main/LICENSE.rst'
    },
    'orjson': {
        'author': 'ijl',
        'description': 'Fast, correct Python JSON library supporting dataclasses, datetimes, and numpy',
        'repo': 'https://github.com/ijl/orjson',
        'license': 'MIT',
        'license_url': 'https://github.com/ijl/orjson/blob/master/LICENSE-MIT'
    }
}

class Colors: # format: 0xHEXCODE
    greens_hair = 0xa19e78
    unifier = 0xed4545
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    purple = 0x9b59b6
    red = 0xe74c3c
    blurple = 0x7289da
    gold = 0xd4a62a
    error = 0xff838c
    warning = 0xe4aa54
    success = 0x11ad79
    critical = 0xff0000

class Emojis:
    def __init__(self, data=None):
        with open('emojis/base.json', 'r') as file:
            base = json.load(file)

        if data:
            for key in base['emojis'].keys():
                if not key in data['emojis'].keys():
                    data['emojis'].update({key: data['emojis'][key]})
        else:
            data = base

        self.back = data['emojis']['back'][0]
        self.prev = data['emojis']['prev'][0]
        self.next = data['emojis']['next'][0]
        self.first = data['emojis']['first'][0]
        self.last = data['emojis']['last'][0]
        self.search = data['emojis']['search'][0]
        self.command = data['emojis']['command'][0]
        self.install = data['emojis']['install'][0]
        self.success = data['emojis']['success'][0]
        self.warning = data['emojis']['warning'][0]
        self.error = data['emojis']['error'][0]
        self.rooms = data['emojis']['rooms'][0]
        self.emoji = data['emojis']['emoji'][0]
        self.leaderboard = data['emojis']['leaderboard'][0]

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = 'data.json'
        self.__save_lock = False

        # Ensure necessary keys exist
        self.update({'rooms': {}, 'emojis': [], 'nicknames': {}, 'blocked': {}, 'banned': {},
                     'moderators': [], 'avatars': {}, 'experiments': {}, 'experiments_info': {}, 'colors': {},
                     'external_bridge': [], 'modlogs': {}, 'spybot': [], 'trusted': [], 'report_threads': {},
                     'fullbanned': [], 'exp': {}, 'squads': {}, 'squads_joined': {}, 'squads_optout': {},
                     'appealban': [], 'languages': {}, 'settings': {}, 'invites': {}})
        self.threads = []

        # Load data
        self.load_data()

    @property
    def save_lock(self):
        return self.__save_lock

    @save_lock.setter
    def save_lock(self, save_lock):
        if self.__save_lock:
            raise RuntimeError('already locked')
        self.__save_lock = save_lock

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            self.update(data)
        except FileNotFoundError:
            pass  # If the file is not found, initialize an empty dictionary

    def save(self):
        if self.__save_lock:
            return
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)
        return

    def cleanup(self):
        for thread in self.threads:
            thread.join()
        count = len(self.threads)
        self.threads.clear()
        return count

    def save_data(self):
        if self.__save_lock:
            return
        thread = threading.Thread(target=self.save)
        thread.start()
        self.threads.append(thread)


def cleanup_code(content):
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    return content.strip('` \n')

def set_author(embed,**kwargs):
    try:
        embed.set_author(name=kwargs['name'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_author(name=kwargs['name'])

def set_footer(embed,**kwargs):
    try:
        embed.set_footer(text=kwargs['text'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_footer(text=kwargs['text'])

def status(code):
    if code != 0:
        raise RuntimeError("install failed")

class CommandExceptionHandler:
    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'exc_handler', self.bot.loglevel)

    async def handle(self, ctx, error):
        try:
            if isinstance(error, commands.MissingRequiredArgument):
                cmdname = ctx.command.name
                cmd = self.bot.get_command(cmdname)
                embed = nextcord.Embed(color=self.bot.colors.unifier)
                embed.title = (
                    f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help / {cmdname}'
                )
                embed.description = (
                    f'# **`{self.bot.command_prefix}{cmdname}`**\n{cmd.description if cmd.description else "No description provided"}'
                )
                if len(cmd.aliases) > 0:
                    aliases = []
                    for alias in cmd.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{alias}`')
                    embed.add_field(
                        name='Aliases', value='\n'.join(aliases) if len(aliases) > 1 else aliases[0], inline=False
                    )
                embed.add_field(name='Usage', value=(
                    f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(
                        cmd.signature) > 0 else f'`{self.bot.command_prefix}{cmdname}`'), inline=False
                                )
                await ctx.send(f'{self.bot.ui_emojis.error} `{error.param}` is a required argument.',embed=embed)
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send(f'{self.bot.ui_emojis.error} {error}')
            elif isinstance(error, commands.CheckFailure):
                await ctx.send(f'{self.bot.ui_emojis.error} You do not have permissions to run this command.')
            elif isinstance(error, commands.NoPrivateMessage):
                await ctx.send(f'{self.bot.ui_emojis.error} You can only run this command in servers.')
            elif isinstance(error, commands.PrivateMessageOnly):
                await ctx.send(f'{self.bot.ui_emojis.error} You can only run this command in DMs.')
            elif isinstance(error, commands.CommandOnCooldown):
                t = int(error.retry_after)
                await ctx.send(f'{self.bot.ui_emojis.error} You\'re on cooldown. Try again in **{t // 60}** minutes and **{t % 60}** seconds.')
            else:
                error_tb = traceback.format_exc()
                self.logger.exception('An error occurred!')
                view = ui.MessageComponents()
                if ctx.author.id==self.bot.config['owner']:
                    view.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label='View error'
                            )
                        )
                    )
                msg = await ctx.send(f'{self.bot.ui_emojis.error} An unexpected error occurred while running this command.',
                                     view=view)

                def check(interaction):
                    return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

                if not ctx.author.id == self.bot.config['owner']:
                    return

                try:
                    interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
                except:
                    view = ui.MessageComponents()
                    view.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label='View error',
                                disabled=True
                            )
                        )
                    )
                    return await msg.edit(view=view)

                view = ui.MessageComponents()
                view.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='View error',
                            disabled=True
                        )
                    )
                )
                await msg.edit(view=view)

                try:
                    await interaction.response.send_message(f'```\n{error_tb}```',ephemeral=True)
                except:
                    await interaction.response.send_message('Could not send traceback.', ephemeral=True)
        except:
            self.logger.exception('An error occurred!')
            await ctx.send(f'{self.bot.ui_emojis.error} An unexpected error occurred while running this command.')

class SysManager(commands.Cog, name=':wrench: System Manager'):
    """An extension that oversees a lot of the bot system.

    Developed by Green"""

    class SysExtensionLoadFailed(Exception):
        pass

    def __init__(self, bot):
        global language
        self.bot = bot
        if not hasattr(self.bot, 'db'):
            self.bot.db = AutoSaveDict({})

        restrictions.attach_bot(self.bot)

        if not hasattr(self.bot, 'colors'):
            self.bot.colors = Colors
            self.bot.colors.unifier = ast.literal_eval(f"0x{self.bot.config['main_color']}")
        if not hasattr(self.bot, 'ui_emojis'):
            if not os.path.exists('emojis'):
                # Upgrader doesn't bring emojis over, so add them manually
                os.mkdir('emojis')
                with open('update/emojis/base.json', 'r') as file:
                    base = json.load(file)
                with open('emojis/base.json', 'w+') as file:
                    json.dump(base, file, indent=2)
            with open('emojis/base.json', 'r') as file:
                base = json.load(file)
            if not base['installed']:
                base.update({'emojis_pre': base['emojis']})
                for emoji in base['emojis'].keys():
                    text = base['emojis'][emoji][0]
                    if text.startswith(':') and text.endswith(':'):
                        base['emojis'][emoji][0] = discord_emoji.to_unicode(text)
                base['installed'] = True
                with open('emojis/base.json', 'w') as file:
                    json.dump(base, file, indent=2)
            try:
                if self.bot.coreboot:
                    raise RuntimeError()
                with open('emojis/current.json', 'r') as file:
                    data = json.load(file)
                self.bot.ui_emojis = Emojis(data=data)
            except:
                self.bot.ui_emojis = Emojis()
        if not hasattr(self.bot, 'pid'):
            self.bot.pid = None
        if not hasattr(self.bot, 'loglevel'):
            self.bot.loglevel = logging.DEBUG if self.bot.config['debug'] else logging.INFO
        if not hasattr(self.bot, 'package'):
            self.bot.package = self.bot.config['package']
        if not hasattr(self.bot, 'admins'):
            self.bot.admins = self.bot.config['admin_ids']
            self.bot.moderators = self.bot.admins + self.bot.db['moderators']

        self.bot.exhandler = CommandExceptionHandler(self.bot)
        self.logger = log.buildlogger(self.bot.package, 'sysmgr', self.bot.loglevel)

        if not hasattr(self.bot, 'langmgr'):
            self.bot.langmgr = langmgr.LanguageManager(self.bot)
            self.bot.langmgr.load()
        language = self.bot.langmgr
        if not hasattr(self.bot,'loaded_plugins'):
            self.bot.loaded_plugins = {}
            if not self.bot.safemode and not self.bot.coreboot:
                for plugin in os.listdir('plugins'):
                    with open('plugins/' + plugin) as file:
                        extinfo = json.load(file)
                        try:
                            if not 'content_protection' in extinfo['services'] and not 'content_processing' in extinfo['services']:
                                continue
                        except:
                            continue
                    script = importlib.import_module('utils.' + plugin[:-5] + '_content_protection')
                    self.bot.loaded_plugins.update({plugin[:-5]: script})
        if not hasattr(self.bot,'platforms'):
            self.bot.platforms_former = {}
            self.bot.platforms = {}

            # This loads the entire plugin script to memory.
            # Plugins will need to create the platform support object themselves when the
            # bot is ready on the platform.
            if not self.bot.safemode and not self.bot.coreboot:
                for plugin in os.listdir('plugins'):
                    with open('plugins/' + plugin) as file:
                        extinfo = json.load(file)
                        try:
                            if not 'bridge_platform' in extinfo['services']:
                                continue
                        except:
                            continue
                    script = importlib.import_module('utils.' + plugin[:-5] + '_bridge_platform')
                    self.bot.platforms_former.update({extinfo['bridge_platform']: script})
        if not hasattr(self.bot, "ut_total"):
            self.bot.ut_total = round(time.time())
        if not hasattr(self.bot, "disconnects"):
            self.bot.disconnects = 0

        if not self.bot.ready and not self.bot.coreboot:
            try:
                with open('plugins/system.json') as file:
                    sysext = json.load(file)
            except:
                self.logger.warning('plugins/system.json is missing. Copying update.json...')
                if not os.path.exists('plugins'):
                    os.mkdir('plugins')
                status(os.system('cp ' + os.getcwd() + '/update.json ' + os.getcwd() + '/plugins/system.json'))
                with open('plugins/system.json') as file:
                    sysext = json.load(file)
            for extension in sysext['modules']:
                try:
                    self.bot.load_extension('cogs.' + extension[:-3])
                    self.logger.debug('Loaded system plugin '+extension)
                except:
                    self.logger.critical('System plugin load failed! (' + extension + ')')
                    raise self.SysExtensionLoadFailed()
            if not self.bot.safemode:
                for plugin in os.listdir('plugins'):
                    if plugin=='system.json':
                        continue
                    if not plugin.endswith('.json'):
                        continue
                    with open('plugins/' + plugin) as file:
                        extinfo = json.load(file)
                    for extension in extinfo['modules']:
                        try:
                            self.bot.load_extension('cogs.' + extension[:-3])
                            self.logger.debug('Loaded plugin ' + extension)
                        except:
                            self.logger.warning('Plugin load failed! (' + extension + ')')

        if not hasattr(self.bot, 'status_rotation_task') and not self.bot.coreboot:
            self.bot.status_rotation_task = self.changestatus
            if not self.bot.status_rotation_task .is_running() and self.bot.config['enable_rotating_status']:
                self.bot.status_rotation_task.start()
        if not hasattr(self.bot, 'antisleep_task') and not self.bot.coreboot:
            self.bot.antisleep_task = self.periodicping
            self.bot.antisleep_task.change_interval(seconds=round(self.bot.config['ping']))
            if not self.bot.antisleep_task.is_running() and round(self.bot.config['ping']) > 0:
                self.bot.antisleep_task.start()
                self.logger.debug(f'Pinging servers every {round(self.bot.config["ping"])} seconds')
        if not hasattr(self.bot, 'backup_local_task') and not self.bot.coreboot:
            self.bot.backup_local_task = self.periodic_backup
            self.bot.backup_local_task.change_interval(seconds=round(
                self.bot.config['periodic_backup_local']
                if 'periodic_backup_local' in self.bot.config.keys() else
                self.bot.config['periodic_backup']
            ))
            if not self.bot.backup_local_task.is_running() and round(
                    self.bot.config['periodic_backup_local']
                    if 'periodic_backup_local' in self.bot.config.keys() else
                    self.bot.config['periodic_backup']
            ) > 0:
                self.bot.backup_local_task.start()
                self.logger.debug(f'Backing up messages every {round(self.bot.config["ping"])} seconds')
        if not hasattr(self.bot, 'backup_cloud_task') and not self.bot.coreboot:
            self.bot.backup_cloud_task = self.periodic_backup_cloud
            self.bot.backup_cloud_task.change_interval(seconds=round(
                self.bot.config['periodic_backup_cloud']
            ))
            if not self.bot.backup_cloud_task.is_running() and round(self.bot.config['periodic_backup_cloud']) > 0:
                self.bot.backup_cloud_task.start()
                self.logger.debug(f'Backing up data to cloud every {round(self.bot.config["ping"])} seconds')

    def encrypt_string(self, hash_string):
        sha_signature = \
            hashlib.sha256(hash_string.encode()).hexdigest()
        return sha_signature

    async def encrypt(self, encoded, password, salt):
        __key = await self.bot.loop.run_in_executor(None, lambda: PBKDF2(password, salt, dkLen=32))

        iv = CryptoRandom.get_random_bytes(16)
        __cipher = AES.new(__key, AES.MODE_CBC, iv=iv)
        result = await self.bot.loop.run_in_executor(None, lambda: __cipher.encrypt(pad(encoded, AES.block_size)))
        del __key
        del __cipher
        return result, base64.b64encode(iv).decode('ascii')

    async def decrypt(self, encrypted, password, salt, iv_string):
        iv = base64.b64decode(iv_string)
        __key = await self.bot.loop.run_in_executor(None, lambda: PBKDF2(password, salt, dkLen=32))
        __cipher = AES.new(__key, AES.MODE_CBC, iv=iv)
        result = await self.bot.loop.run_in_executor(None, lambda: unpad(__cipher.decrypt(encrypted), AES.block_size))
        del __key
        del __cipher
        return result

    async def download(self):
        endpoint = 'https://' + self.bot.config['cloud_backup_endpoint']
        __apikey = os.environ.get('API_KEY')
        __headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {__apikey}"
        }
        try:
            __salt = self.bot.config['cloud_backup_salt']
            __pass = os.environ.get('ENCRYPTION_PASSWORD')
        except:
            return
        resp = await self.bot.loop.run_in_executor(
            None, lambda: requests.get(endpoint + '/api/v1/restore', headers=__headers)
        )
        data = resp.json()
        config_restored = await self.decrypt(
            base64.b64decode(data['config']), __pass, __salt, data['iv'][0]
        )
        data_restored = await self.decrypt(
            base64.b64decode(data['data']), __pass, __salt, data['iv'][1]
        )
        return config_restored.decode("utf-8"), data_restored.decode("utf-8")

    async def check_backup(self):
        endpoint = 'https://' + self.bot.config['cloud_backup_endpoint']
        __apikey = os.environ.get('API_KEY')
        __headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {__apikey}"
        }

        resp = await self.bot.loop.run_in_executor(
            None, lambda: requests.get(endpoint + '/api/v1/info', headers=__headers)
        )

        if not resp.status_code == 200:
            if resp.status_code == 404:
                return None
            raise RuntimeError(f'connected to server but server returned {resp.status_code}')

        return resp.json()

    async def preunload(self, extension):
        """Performs necessary steps before unloading."""
        info = None
        plugin_name = None
        if extension.startswith('cogs.'):
            extension = extension.replace('cogs.','',1)
        for plugin in os.listdir('plugins'):
            if extension + '.json' == plugin:
                plugin_name = plugin[:-5]
                try:
                    with open('plugins/' + plugin) as file:
                        info = json.load(file)
                except:
                    continue
                break
            else:
                try:
                    with open('plugins/' + plugin) as file:
                        info = json.load(file)
                except:
                    continue
                if extension + '.py' in info['modules']:
                    plugin_name = plugin[:-5]
                    break
        if not plugin_name:
            return
        if plugin_name == 'system':
            return
        if not info:
            raise ValueError('Invalid plugin')
        if not info['shutdown']:
            return
        script = importlib.import_module('utils.' + plugin_name + '_check')
        await script.check(self.bot)

    @tasks.loop(seconds=300)
    async def changestatus(self):
        status_messages = [
            ["playing","with the ban hammer"],
            ["playing","with fire"],
            ["playing","with the API"],
            ["playing","hide and seek"],
            ["listening","my own code"],
            ["playing","in debug mode"],
            ["playing","in a parallel universe"],
            ["playing","with commands"],
            ["playing","a game of chess"],
            ["playing","with electrons"],
            ["watching","the matrix"],
            ["watching","cookies bake"],
            ["playing","with the metaverse"],
            ["playing","with emojis"],
            ["playing","with Nevira"],
            ["playing","with green."],
            ["playing","with ItsAsheer"],
            ["watching","webhooks"],
            ["custom","Unifying servers like they're nothing"],
            ["custom","Made for communities, by communities"],
            ["custom","bro nevira stop stealing my code"]
        ]
        new_stat = random.choice(status_messages)
        if new_stat[0] == "watching":
            await self.bot.change_presence(activity=nextcord.Activity(
                type=nextcord.ActivityType.watching, name=new_stat[1]
            ))
        elif new_stat[0] == "listening":
            await self.bot.change_presence(activity=nextcord.Activity(
                type=nextcord.ActivityType.listening, name=new_stat[1]
            ))
        elif new_stat[0] == "playing":
            await self.bot.change_presence(activity=nextcord.Game(name=new_stat[1]))
        elif new_stat[0] == "custom":
            await self.bot.change_presence(activity=nextcord.CustomActivity(
                name="Custom Status", state=new_stat[1]
            ))

    @tasks.loop()
    async def periodic_backup(self):
        if not self.bot.ready:
            return
        try:
            tasks = [self.bot.loop.create_task(self.bot.bridge.backup(limit=10000))]
            await asyncio.wait(tasks)
        except:
            self.logger.exception('Backup failed')

    @tasks.loop()
    async def periodic_backup_cloud(self):
        if not self.bot.ready:
            return
        endpoint = 'https://' + self.bot.config['cloud_backup_endpoint']
        __apikey = os.environ.get('API_KEY')
        __headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {__apikey}"
        }
        try:
            __salt = self.bot.config['cloud_backup_salt']
            __pass = os.environ.get('ENCRYPTION_PASSWORD')
            if not __salt or not __pass:
                return
        except:
            return
        try:
            config_text, config_iv = await self.encrypt(orjson.dumps(self.bot.config), __pass, __salt)
            data_text, data_iv = await self.encrypt(orjson.dumps(self.bot.db), __pass, __salt)
        except:
            self.logger.exception('An error occurred!')
            self.logger.error('Encryption failed, skipping backup.')
            return
        self.logger.debug(f'Encrypted data')
        try:
            resp = await self.bot.loop.run_in_executor(
                None, lambda: requests.post(endpoint + '/api/v1/backup', headers=__headers, json={
                    'config': base64.b64encode(config_text).decode('ascii'),
                    'data': base64.b64encode(data_text).decode('ascii'),
                    'iv': [config_iv, data_iv]
                })
            )
        except requests.exceptions.SSLError:
            self.logger.exception('An error occurred!')
            self.logger.error('Connected to server but could not use TLS, disabling backups.')
            self.bot.backup_cloud_task.stop()
            return
        except:
            self.logger.exception('An error occurred!')
            self.logger.error('Backup failed')
            return
        if resp.status_code == 200:
            self.logger.debug(f'Request successfully sent to server')
            return
        else:
            self.logger.warning(f'Request successfully sent but server returned {resp.status_code}')

    @tasks.loop()
    async def periodicping(self):
        guild = self.bot.guilds[0]
        try:
            await self.bot.fetch_channel(guild.text_channels[0].id)
        except:
            pass

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.bot.disconnects += 1

    @commands.command(aliases=['reload-services'], hidden=True, description=language.desc('sysmgr.reload_services'))
    @restrictions.owner()
    async def reload_services(self,ctx,*,services=None):
        selector = language.get_selector(ctx)
        if not services:
            plugins = self.bot.loaded_plugins
        else:
            plugins = services.split(' ')
        success = []
        failed = []
        errors = []
        text = '```diff'
        msg = await ctx.send(selector.get('in_progress'))
        for plugin in plugins:
            try:
                importlib.reload(self.bot.loaded_plugins[plugin])
                success.append(plugin)
                text = text + f'\n+ [DONE] {plugin}'
            except Exception as e:
                failed.append(plugin)
                errors.append(e)
                text = text + f'\n- [FAIL] {plugin}'
        await msg.edit(selector.fget(
            'completed', values={'success': len(plugins)-len(failed), 'total': len(plugins())}
        ))
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'{selector.get("extension")} `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\n{selector.get("extension")} `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**{selector.get("fail_logs")}**\n{text}')

    @commands.command(hidden=True,description=language.desc('sysmgr.eval'))
    @restrictions.owner()
    async def eval(self, ctx, *, body):
        selector = language.get_selector(ctx)
        env = {
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'source': inspect.getsource,
            'session': self.bot.session,
            'bot': self.bot
        }

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            if 'bot.token' in body or 'dotenv' in body or '.env' in body or 'environ' in body:
                raise ValueError('Blocked phrase')
            exec(to_compile, env)
        except:
            pass

        try:
            func = env['func']
        except Exception as e:
            await ctx.send(selector.get('error'), reference=ctx.message)
            await ctx.author.send(
                f'```py\n{e.__class__.__name__}: {e}\n```\n{selector.get("syntaxerror")}')
            return
        token_start = base64.b64encode(bytes(str(self.bot.user.id), 'utf-8')).decode('utf-8')
        try:
            with redirect_stdout(stdout):
                # ret = await func() to return output
                await func()
        except:
            value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
            await ctx.send(selector.get('error'), reference=ctx.message)
            if token_start in value:
                return await ctx.author.send(selector.get('blocked'))
            await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
            if token_start in value:
                return await ctx.send(selector.get('blocked'))
            if value == '':
                pass
            else:
                #  here, cause is if haves value
                await ctx.send('```%s```' % value)

    @eval.error
    async def eval_error(self, ctx, error):
        selector = language.get_selector(ctx)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(selector.get('nocode'))
        else:
            raise

    @commands.command(aliases=['stop', 'poweroff', 'kill'], hidden=True, description=language.desc('sysmgr.shutdown'))
    @restrictions.owner()
    async def shutdown(self, ctx):
        selector = language.get_selector(ctx)
        self.logger.info("Attempting graceful shutdown...")
        self.bot.bridge.backup_lock = True
        try:
            if self.bot.bridge.backup_running:
                self.logger.info('Waiting for backups to complete...(Press Ctrl+C to abort)')
                try:
                    while self.bot.bridge.backup_running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
            for extension in self.bot.extensions:
                await self.preunload(extension)
            self.logger.info("Backing up message cache...")
            self.bot.db.save_data()
            self.bot.bridge.backup_lock = False
            await self.bot.bridge.backup(limit=10000)
            self.logger.info("Backup complete")
            await ctx.send(selector.get('success'))
        except:
            self.logger.exception("Graceful shutdown failed")
            await ctx.send(selector.get('failed'))
            return
        self.logger.info("Closing bot session")
        await self.bot.session.close()
        self.logger.info("Shutdown complete")
        await self.bot.close()
        sys.exit(0)

    @commands.command(hidden=True,description=language.desc('sysmgr.plugins'))
    @restrictions.owner()
    async def plugins(self, ctx, *, plugin=None):
        selector = language.get_selector(ctx)
        if plugin:
            plugin = plugin.lower()
        page = 0
        try:
            page = int(plugin) - 1
            if page < 0:
                page = 0
            plugin = None
        except:
            pass
        pluglist = [plugin for plugin in os.listdir('plugins') if plugin.endswith('.json')]
        if not plugin:
            offset = page * 20
            embed = nextcord.Embed(title=selector.get('title'), color=self.bot.colors.unifier)
            text = ''
            if offset > len(pluglist):
                page = len(pluglist) // 20 - 1
                offset = page * 20
            for x in range(offset, 20 + offset):
                if x == len(pluglist):
                    break
                with open('plugins/'+pluglist[x]) as file:
                    pluginfo = json.load(file)
                if text == '':
                    text = f'- {pluginfo["name"]} (`{pluginfo["id"]}`)'
                else:
                    text = f'{text}\n- {pluginfo["name"]} (`{pluginfo["id"]}`)'
            embed.description = text
            embed.set_footer(text=selector.rawfget(
                'page', 'sysmgr.extensions', values={'page': page + 1}
            ))
            return await ctx.send(embed=embed)
        found = False
        index = 0
        for plugname in pluglist:
            if plugname[:-5] == plugin:
                found = True
                break
            index += 1
        if found:
            with open('plugins/' + plugin + '.json') as file:
                pluginfo = json.load(file)
        else:
            return await ctx.send(selector.rawget('notfound', 'sysmgr.extensions'))
        embed = nextcord.Embed(
            title=pluginfo["name"],
            description=(selector.fget('version',values={'version':pluginfo['version'],'release':pluginfo['release']})
                         + '\n\n' + pluginfo["description"]),
            color=self.bot.colors.unifier
        )
        if plugin == 'system':
            embed.description = embed.description + selector.get('system_plugin')
        try:
            embed.url = str(pluginfo['repository'])[:-4]
        except:
            pass
        modtext = 'None'
        for module in pluginfo['modules']:
            if modtext=='None':
                modtext = '- ' + module
            else:
                modtext = modtext + '\n- ' + module
        embed.add_field(name=selector.get('modules'),value=modtext,inline=False)
        modtext = 'None'
        for module in pluginfo['utils']:
            if modtext == 'None':
                modtext = '- ' + module
            else:
                modtext = modtext + '\n- ' + module
        embed.add_field(name=selector.get('utilities'), value=modtext, inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True, aliases=['cogs'], description=language.desc('sysmgr.extensions'))
    @restrictions.owner()
    async def extensions(self, ctx, *, extension=None):
        selector = language.get_selector(ctx)
        if extension:
            extension = extension.lower()
        page = 0
        try:
            page = int(extension) - 1
            if page < 0:
                page = 0
            extension = None
        except:
            pass
        if not extension:
            offset = page * 20
            embed = nextcord.Embed(title=selector.get('title'), color=self.bot.colors.unifier)
            text = ''
            extlist = list(self.bot.extensions)
            if offset > len(extlist):
                page = len(extlist) // 20 - 1
                offset = page * 20
            for x in range(offset, 20 + offset):
                if x == len(list(self.bot.cogs)):
                    break
                cog = self.bot.cogs[list(self.bot.cogs)[x]]
                ext = list(self.bot.extensions)[x]
                if text == '':
                    text = f'- {cog.qualified_name} (`{ext}`)'
                else:
                    text = f'{text}\n- {cog.qualified_name} (`{ext}`)'
            embed.description = text
            embed.set_footer(text=selector.fget('page',values={'page':page + 1}))
            return await ctx.send(embed=embed)
        found = False
        index = 0
        for ext in list(self.bot.extensions):
            if ext.replace('cogs.', '', 1) == extension or ext == extension:
                found = True
                break
            index += 1
        if found:
            ext_info = self.bot.cogs[list(self.bot.cogs)[index]]
        else:
            return await ctx.send(selector.get('notfound'))
        embed = nextcord.Embed(
            title=ext_info.qualified_name,
            description=ext_info.description,
            color=self.bot.colors.unifier
        )
        if (extension == 'cogs.sysmgr' or extension == 'cogs.lockdown' or
                extension == 'sysmgr' or extension == 'lockdown'):
            embed.description = embed.description + selector.get('system_module')
        await ctx.send(embed=embed)

    @commands.command(hidden=True,description=language.desc('sysmgr.reload'))
    @restrictions.owner()
    async def reload(self, ctx, *, extensions):
        selector = language.get_selector(ctx)
        if self.bot.update:
            return await ctx.send(selector.get('disabled'))

        extensions = extensions.split(' ')
        msg = await ctx.send(selector.get('in_progress'))
        failed = []
        errors = []
        text = ''
        for extension in extensions:
            try:
                if extension == 'lockdown':
                    raise ValueError('Cannot unload lockdown extension for security purposes.')
                await self.preunload(extension)
                self.bot.reload_extension(f'cogs.{extension}')
                if len(text) == 0:
                    text = f'```diff\n+ [DONE] {extension}'
                else:
                    text += f'\n+ [DONE] {extension}'
            except Exception as e:
                failed.append(extension)
                errors.append(e)
                if len(text) == 0:
                    text = f'```diff\n- [FAIL] {extension}'
                else:
                    text += f'\n- [FAIL] {extension}'
        await msg.edit(content=selector.rawfget(
            'completed', 'sysmgr.reload_services', values={
                'success': len(extensions)-len(failed), 'total': len(extensions), 'text': text
            }
        ))
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'{selector.rawget("extension","sysmgr.reload_servies")} `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\n{selector.rawget("extension","sysmgr.reload_servies")} `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_servies")}**\n{text}')

    @commands.command(hidden=True,description=language.desc('sysmgr.load'))
    @restrictions.owner()
    async def load(self, ctx, *, extensions):
        selector = language.get_selector(ctx)
        if self.bot.update:
            return await ctx.send(selector.rawget('disabled','sysmgr.reload'))

        extensions = extensions.split(' ')
        msg = await ctx.send(selector.get('in_progress'))
        failed = []
        errors = []
        text = ''
        for extension in extensions:
            try:
                self.bot.load_extension(f'cogs.{extension}')
                if len(text) == 0:
                    text = f'```diff\n+ [DONE] {extension}'
                else:
                    text += f'\n+ [DONE] {extension}'
            except Exception as e:
                failed.append(extension)
                errors.append(e)
                if len(text) == 0:
                    text = f'```diff\n- [FAIL] {extension}'
                else:
                    text += f'\n- [FAIL] {extension}'
        await msg.edit(content=selector.fget(
            'completed',
            values={'success': len(extensions)-len(failed), 'total': len(extensions), 'text': text}
        ))
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'Extension `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_servies")}**\n{text}')

    @commands.command(hidden=True,description='Unloads an extension.')
    @restrictions.owner()
    async def unload(self, ctx, *, extensions):
        selector = language.get_selector(ctx)
        if self.bot.update:
            return await ctx.send(selector.rawget('disabled','sysmgr.reload'))

        extensions = extensions.split(' ')
        msg = await ctx.send('Unloading extensions...')
        failed = []
        errors = []
        text = ''
        for extension in extensions:
            try:
                if extension == 'sysmgr':
                    raise ValueError('Cannot unload the sysmgr extension, let\'s not break the bot here!')
                if extension == 'lockdown':
                    raise ValueError('Cannot unload lockdown extension for security purposes.')
                await self.preunload(extension)
                self.bot.unload_extension(f'cogs.{extension}')
                if len(text) == 0:
                    text = f'```diff\n+ [DONE] {extension}'
                else:
                    text += f'\n+ [DONE] {extension}'
            except Exception as e:
                failed.append(extension)
                errors.append(e)
                if len(text) == 0:
                    text = f'```diff\n- [FAIL] {extension}'
                else:
                    text += f'\n- [FAIL] {extension}'
        await msg.edit(content=selector.fget(
            'completed',
            values={'success': len(extensions)-len(failed), 'total': len(extensions), 'text': text}
        ))
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'Extension `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_servies")}**\n{text}')

    @commands.command(hidden=True,description='Installs a plugin.')
    @restrictions.owner()
    async def install(self, ctx, url):
        selector = language.get_selector(ctx)
        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

        if os.name == "nt":
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.error} Can\'t install Plugins',
                description=('Unifier cannot install Plugins on Windows. Please use an OS with the bash console (Linux'+
                             '/macOS/etc).'),
                color=self.bot.colors.error
            )
            return await ctx.send(embed=embed)

        if url.endswith('/'):
            url = url[:-1]
        if not url.endswith('.git'):
            url = url + '.git'
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.install} {selector.get("downloading_title")}', description=selector.get("downloading_body"))
        embed.set_footer(text='Only install plugins from trusted sources!')
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/plugin_install')
            await self.bot.loop.run_in_executor(None, lambda: status(os.system(
                'git clone ' + url + ' ' + os.getcwd() + '/plugin_install')))
            with open('plugin_install/plugin.json', 'r') as file:
                new = json.load(file)
            if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                embed.title = f'{self.bot.ui_emojis.error} Invalid plugin.json file'
                embed.description = 'Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.'
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
            if new['id']+'.json' in os.listdir('plugins'):
                with open('plugins/'+new['id']+'.json', 'r') as file:
                    current = json.load(file)
                embed.title = f'{self.bot.ui_emojis.error} Plugin already installed'
                embed.description = f'This plugin is already installed!\n\nName: `{current["name"]}`\nVersion: `{current["version"]}`'
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
            plugin_id = new['id']
            name = new['name']
            desc = new['description']
            version = new['version']
            minimum = new['minimum']
            modules = new['modules']
            utilities = new['utils']
            try:
                nups_platform = new['bridge_platform']
                if nups_platform == '':
                    nups_platform = None
            except:
                nups_platform = None
            try:
                services = new['services']
            except:
                services = []

            with open('plugins/system.json', 'r') as file:
                vinfo = json.load(file)

            if vinfo['release'] < minimum:
                embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
                embed.description = f'Your Unifier does not support this plugin. Release `{minimum}` or later is required.'
                embed.colour = self.bot.colors.error
                return await msg.edit(embed=embed)

            conflicts = []
            for module in modules:
                if module in os.listdir('cogs'):
                    conflicts.append('cogs/'+module)
            for util in utilities:
                if util in os.listdir('utils'):
                    conflicts.append('utils/'+util)
            if f'{plugin_id}.json' in os.listdir('emojis') and 'emojis' in services:
                conflicts.append(f'emojis/{plugin_id}.json')
            if len(conflicts) > 1:
                embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
                embed.description = 'Conflicting files were found:\n'
                for conflict in conflicts:
                    embed.description = embed.description + f'\n`{conflict}`'
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
        except:
            embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
            embed.description = 'The repository URL or the plugin.json file is invalid.'
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return
        embed.title = f'{self.bot.ui_emojis.install} Install `{plugin_id}`?'
        embed.description = f'Name: `{name}`\nVersion: `{version}`\n\n{desc}'
        embed.colour = 0xffcc00

        services_text = ''
        for service in services:
            if service=='content_protection':
                text = (
                    ':shield: **Content protection**\n'+
                    'The plugin will be able to analyze messages for malicious content, as well as ban users if '+
                    'necessary. Non-permanent bans are reset on Bridge reload.'
                )
            elif service=='content_processing':
                text = (
                    ':art: **Content stylizing**\n'+
                    'The plugin will be able to modify message content and author information before bridging to '+
                    'other servers.'
                )
            elif service=='bridge_platform':
                text = (
                    ':handshake: **Bridge platform support**\n'+
                    'The plugin will be able to provide native Unifier Bridgesupport for an external platform.'
                )
                if not nups_platform or nups_platform.lower()=='meta':
                    embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
                    embed.description = 'The plugin provided an invalid platform name.'
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)
            elif service=='emojis':
                text = (
                    ':joy: **Emojis**\n'+
                    'The plugin contains an emoji pack which will be installed onto the bot. You can enable the pack '+
                    f'using `{self.bot.command_prefix}uiemojis {plugin_id}`.'
                )
                with open('plugin_install/emoji.json', 'r') as file:
                    emojipack = json.load(file)
                emojis = len(emojipack['emojis'].keys())
                home_guild = self.bot.get_guild(self.bot.config['home_guild'])
                if emojis > home_guild.emoji_limit - len(home_guild.emojis):
                    embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
                    embed.description = f'Your home server does not have enough emoji slots available. {emojis} is required, but you only have {home_guild.emoji_limit - len(home_guild.emojis)}.'
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)
            else:
                text = (
                    f':grey_question: `{service}`\n',
                    'This is an unknown service.'
                )
            if len(services_text)==0:
                services_text = text
            else:
                services_text = f'{services_text}\n\n{text}'

        embed.add_field(
            name='Services',
            value=services_text
        )
        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.green, label='Install', custom_id=f'accept', disabled=False),
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        await msg.edit(embed=embed, view=components)
        embed.clear_fields()

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            return await msg.edit(view=components)
        if interaction.data['custom_id'] == 'reject':
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            return await interaction.response.edit_message(view=components)

        await interaction.response.edit_message(embed=embed, view=None)
        try:
            try:
                if 'requirements' in list(new.keys()):
                    self.logger.debug('Installing dependencies')
                    newdeps = new['requirements']
                    if len(newdeps) > 0:
                        self.logger.debug('Installing: ' + ' '.join(newdeps))
                        await self.bot.loop.run_in_executor(None, lambda: status(
                            os.system('python3 -m pip install --no-dependencies ' + ' '.join(newdeps))
                        ))
            except:
                self.logger.exception('Dependency installation failed')
                raise RuntimeError()
            self.logger.info('Installing Plugin')
            for module in modules:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+module)
                status(os.system(
                    'cp ' + os.getcwd() + '/plugin_install/' + module + ' ' + os.getcwd() + '/cogs/' + module))
            for util in utilities:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+util)
                status(os.system(
                    'cp ' + os.getcwd() + '/plugin_install/' + util + ' ' + os.getcwd() + '/utils/' + util))
            if 'emojis' in services:
                self.logger.info('Installing Emoji Pack')
                home_guild = self.bot.get_guild(self.bot.config['home_guild'])
                with open('plugin_install/emoji.json', 'r') as file:
                    emojipack = json.load(file)
                for emojiname in list(emojipack['emojis'].keys()):
                    self.logger.debug(
                        'Installing: ' + os.getcwd() + '/plugin_install/emojis/' + emojipack['emojis'][emojiname][0])
                    file = 'plugin_install/emojis/' + emojipack['emojis'][emojiname][0]
                    emoji = await home_guild.create_custom_emoji(name=emojiname, image=nextcord.File(fp=file))
                    emojipack['emojis'][
                        emojiname][0] = f'<a:{emoji.name}:{emoji.id}>' if emoji.animated else f'<:{emoji.name}:{emoji.id}>'
                emojipack['installed'] = True
                with open(f'emojis/{plugin_id}.json', 'w+') as file:
                    json.dump(emojipack, file, indent=2)
            self.logger.info('Registering plugin')
            status(
                os.system('cp ' + os.getcwd() + '/plugin_install/plugin.json' + ' ' + os.getcwd() + '/plugins/' + plugin_id + '.json'))
            with open('plugins/' + plugin_id + '.json') as file:
                plugin_info = json.load(file)
                plugin_info.update({'repository':url})
            with open('plugins/' + plugin_id + '.json', 'w') as file:
                json.dump(plugin_info,file)
            self.logger.info('Activating extensions')
            for module in modules:
                modname = 'cogs.' + module[:-3]
                self.logger.debug('Activating extension: '+modname)
                self.bot.load_extension(modname)
            self.logger.debug('Installation complete')
            embed.title = f'{self.bot.ui_emojis.success} Installation successful'
            embed.description = 'The installation was successful! :partying_face:'
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Install failed')
            embed.title = f'{self.bot.ui_emojis.error} Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Uninstalls a plugin.')
    @restrictions.owner()
    async def uninstall(self, ctx, plugin):
        if not ctx.author.id == self.bot.config['owner']:
            return

        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

        plugin = plugin.lower()
        if plugin=='system':
            return await ctx.send('System plugin cannot be uninstalled!')
        embed = nextcord.Embed(title='placeholder', description='This will uninstall all of the plugin\'s files. This cannot be undone!')
        embed.colour = 0xffcc00
        try:
            with open('plugins/' + plugin + '.json') as file:
                plugin_info = json.load(file)
        except:
            embed.title = f'{self.bot.ui_emojis.error} Plugin not found'
            embed.description = 'The plugin could not be found.'
            embed.colour = self.bot.colors.error
            await ctx.send(embed=embed)
            return
        embed.title = f'{self.bot.ui_emojis.install} Uninstall plugin `'+plugin_info['id']+'`?'
        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.red, label='Uninstall', custom_id=f'accept', disabled=False),
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        msg = await ctx.send(embed=embed, view=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            return await msg.edit(view=components)
        if interaction.data['custom_id'] == 'reject':
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            return await interaction.response.edit_message(view=components)

        await interaction.response.edit_message(embed=embed, view=None)
        try:
            plugin_id = plugin_info['id']
            modules = plugin_info['modules']
            utilities = plugin_info['utils']
            self.logger.info('Uninstalling Plugin')
            for module in modules:
                self.logger.debug('Uninstalling: ' + os.getcwd() + '/cogs/' + module)
                os.remove('cogs/'+module)
            for util in utilities:
                self.logger.debug('Uninstalling: ' + os.getcwd() + '/utils/' + util)
                os.remove('utils/'+util)
            self.logger.info('Deleting plugin entry')
            os.remove('plugins/' + plugin_id + '.json')
            self.logger.info('Unloading extensions')
            for module in modules:
                modname = 'cogs.' + module[:-3]
                if modname in list(self.bot.extensions):
                    self.logger.debug('Unloading extension: ' + modname)
                    await self.preunload(modname)
                    self.bot.unload_extension(modname)
            self.logger.debug('Uninstallation complete')
            embed.title = f'{self.bot.ui_emojis.success} Uninstallation successful'
            embed.description = 'The plugin was successfully uninstalled.'
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Uninstall failed')
            embed.title = f'{self.bot.ui_emojis.error} Uninstallation failed'
            embed.description = 'The uninstallation failed.'
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Upgrades Unifier or a plugin.')
    @restrictions.owner()
    async def upgrade(self, ctx, plugin='system', *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return

        selector = language.get_selector(ctx)

        if self.bot.update:
            return await ctx.send(selector.rawget('disabled','sysmgr.reload'))

        if os.name == "nt":
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.error} {selector.get("windows_title")}',
                description=selector.get('windows_body'),
                color=self.bot.colors.error
            )
            return await ctx.send(embed=embed)

        args = args.split(' ')
        force = False
        ignore_backup = False
        no_backup = False
        if 'force' in args:
            force = True
        if 'ignore-backup' in args:
            ignore_backup = True
        if 'no-backup' in args:
            no_backup = True

        plugin = plugin.lower()

        if plugin=='system':
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.install} {selector.get("checking_title")}',
                description=selector.get('checking_body')
            )
            msg = await ctx.send(embed=embed)
            available = []
            try:
                os.system('rm -rf ' + os.getcwd() + '/update_check')
                await self.bot.loop.run_in_executor(None, lambda: os.system(
                    'git clone --branch ' + self.bot.config['branch'] + ' ' + self.bot.config[
                        'check_endpoint'] + ' ' + os.getcwd() + '/update_check'))
                with open('plugins/system.json', 'r') as file:
                    current = json.load(file)
                with open('update_check/update.json', 'r') as file:
                    new = json.load(file)
                if new['release'] > current['release'] or force:
                    available.append([new['version'], 'Release version', new['release'], -1, new['reboot']])
                index = 0
                for legacy in new['legacy']:
                    if (
                            legacy['lower'] <= current['release'] <= legacy['upper'] and (
                                legacy['release'] > (
                                    current['legacy'] if 'legacy' in current.keys() else -1
                                ) or force
                            )
                    ):
                        available.append([legacy['version'], 'Legacy version', legacy['release'], index, legacy['reboot']])
                    index += 1
                update_available = len(available) >= 1
            except:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("checkfail_title")}'
                embed.description = selector.get("checkfail_body")
                embed.colour = self.bot.colors.error
                return await msg.edit(embed=embed)
            if not update_available:
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("noupdates_title")}'
                embed.description = selector.get("noupdates_body")
                embed.colour = self.bot.colors.success
                return await msg.edit(embed=embed)
            selected = 0
            interaction = None
            while True:
                release = available[selected][2]
                version = available[selected][0]
                legacy = available[selected][3] > -1
                reboot = available[selected][4]
                embed.title = f'{self.bot.ui_emojis.install} {selector.get("available_title")}'
                embed.description = selector.fget('available_body',values={
                    'current_ver':current['version'],'current_rel':current['release'],'new_ver':version,'new_rel':release
                })
                embed.remove_footer()
                embed.colour = 0xffcc00
                if legacy:
                    should_reboot = reboot >= (current['legacy'] if 'legacy' in current.keys() and
                                               type(current['legacy']) is int else -1)
                else:
                    should_reboot = reboot >= current['release']
                if should_reboot:
                    embed.set_footer(text=selector.get("reboot_required"))
                selection = nextcord.ui.StringSelect(
                    placeholder=selector.get("version"),
                    max_values=1,
                    min_values=1,
                    custom_id='selection',
                    disabled=len(available)==1
                )
                index = 0
                for update_option in available:
                    selection.add_option(
                        label=update_option[0],
                        description=update_option[1],
                        value=f'{index}',
                        default=index==selected
                    )
                    index += 1
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green, label=selector.get("upgrade"), custom_id=f'accept',
                        disabled=False
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray, label=selector.rawget('nevermind','sysmgr.install'), custom_id=f'reject',
                        disabled=False
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.link, label=selector.get("moreinfo"),
                        url=f'https://github.com/UnifierHQ/unifier/releases/tag/{version}'
                    )
                )
                components = ui.MessageComponents()
                components.add_rows(ui.ActionRow(selection),btns)
                if not interaction:
                    await msg.edit(embed=embed, view=components)
                else:
                    await interaction.response.edit_message(embed=embed, view=components)

                def check(interaction):
                    return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

                try:
                    interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
                except:
                    return await msg.edit(view=None)
                if interaction.data['custom_id'] == 'reject':
                    return await interaction.response.edit_message(view=None)
                elif interaction.data['custom_id'] == 'accept':
                    break
                elif interaction.data['custom_id'] == 'selection':
                    selected = int(interaction.data['values'][0])
            self.logger.info('Upgrade confirmed, preparing...')
            if not no_backup:
                embed.title = f'{self.bot.ui_emojis.install} {selector.get("backup_title")}'
                embed.description = selector.get("backup_body")
                await interaction.response.edit_message(embed=embed, view=None)
            try:
                if no_backup:
                    raise ValueError()
                folder = os.getcwd() + '/old'
                try:
                    os.mkdir(folder)
                except:
                    pass
                folder = os.getcwd() + '/old/cogs'
                try:
                    os.mkdir(folder)
                except:
                    pass
                for file in os.listdir(os.getcwd() + '/cogs'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/cogs/' + file)
                    os.system('cp ' + os.getcwd() + '/cogs/' + file + ' ' + os.getcwd() + '/old/cogs/' + file)
                self.logger.debug('Backing up: ' + os.getcwd() + '/unifier.py')
                os.system('cp ' + os.getcwd() + '/unifier.py ' + os.getcwd() + '/old/unifier.py')
                self.logger.debug('Backing up: ' + os.getcwd() + '/data.json')
                os.system('cp ' + os.getcwd() + '/data.json ' + os.getcwd() + '/old/data.json')
                self.logger.debug('Backing up: ' + os.getcwd() + '/config.json')
                os.system('cp ' + os.getcwd() + '/config.json ' + os.getcwd() + '/old/config.json')
                self.logger.debug('Backing up: ' + os.getcwd() + '/update.json')
                os.system('cp ' + os.getcwd() + '/update.json ' + os.getcwd() + '/old/update.json')
            except:
                if no_backup:
                    self.logger.warning('Backup skipped, requesting final confirmation.')
                    embed.description = f'- :x: {selector.get("skipped_backup")}\n- :wrench: {selector.get("modification_wipe")}\n- :warning: {selector.get("no_abort")}'
                elif ignore_backup:
                    self.logger.warning('Backup failed, continuing anyways')
                    embed.description = f'- :x: {selector.get("failed_backup")}\n- :wrench: {selector.get("modification_wipe")}\n- :warning: {selector.get("no_abort")}'
                else:
                    self.logger.error('Backup failed, abort upgrade.')
                    embed.title = f'{self.bot.ui_emojis.error} {selector.get("backupfail_title")}'
                    embed.description = selector.get("backupfail_body")
                    embed.colour = self.bot.colors.error
                    await msg.edit(embed=embed)
                    raise
            else:
                self.logger.info('Backup complete, requesting final confirmation.')
                embed.description = f'- :inbox_tray: {selector.get("normal_backup")}\n- :wrench: {selector.get("modification_wipe")}\n- :warning: {selector.get("no_abort")}'
            embed.title = f'{self.bot.ui_emojis.install} {selector.get("start")}'
            components = ui.MessageComponents()
            components.add_row(btns)
            if no_backup:
                await interaction.response.edit_message(embed=embed, view=components)
            else:
                await msg.edit(embed=embed, view=components)
            try:
                interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
            except:
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                return await msg.edit(view=components)
            if interaction.data['custom_id'] == 'reject':
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                return await interaction.response.edit_message(view=components)
            self.logger.debug('Upgrade confirmed, beginning upgrade')
            embed.title = f'{self.bot.ui_emojis.install} {selector.get("upgrading")}'
            embed.description = f':hourglass_flowing_sand: {selector.get("downloading")}\n:x: {selector.get("installing")}\n:x: {selector.get("reloading")}'
            await interaction.response.edit_message(embed=embed, view=None)
            self.logger.info('Starting upgrade')
            try:
                self.logger.debug('Purging old update files')
                os.system('rm -rf ' + os.getcwd() + '/update')
                self.logger.info('Downloading from remote repository...')
                await self.bot.loop.run_in_executor(None, lambda: os.system(
                    'git clone --branch ' + new['version'] + ' --single-branch --depth 1 ' + self.bot.config[
                        'files_endpoint'] + '/unifier.git ' + os.getcwd() + '/update'
                ))
                self.logger.debug('Confirming download...')
                x = open(os.getcwd() + '/update/plugins/system.json', 'r')
                x.close()
                self.logger.debug('Download confirmed, proceeding with upgrade')
            except:
                self.logger.exception('Download failed, no rollback required')
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.description = selector.get("download_fail")
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
            try:
                self.logger.debug('Installing dependencies')
                x = open('update/requirements.txt')
                newdeps = x.read().split('\n')
                x.close()
                try:
                    x = open('requirements.txt')
                    olddeps = x.read().split('\n')
                    x.close()
                except:
                    self.logger.warning('Could not find requirements.txt, installing all dependencies')
                    olddeps = []
                for dep in olddeps:
                    try:
                        newdeps.remove(dep)
                    except:
                        pass
                if len(newdeps) > 0:
                    self.logger.debug('Installing: ' + ' '.join(newdeps))
                    await self.bot.loop.run_in_executor(None, lambda: status(
                        os.system('python3 -m pip install ' + ' '.join(newdeps))
                    ))
            except:
                self.logger.exception('Dependency installation failed, no rollback required')
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.description = selector.get("dependency_fail")
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
            try:
                self.logger.info('Installing upgrades')
                embed.description = f':white_check_mark: {selector.get("downloading")}\n:hourglass_flowing_sand: {selector.get("installing")}\n:x: {selector.get("reloading")}'
                await msg.edit(embed=embed)
                self.logger.debug('Installing: ' + os.getcwd() + '/update/unifier.py')
                status(os.system('cp ' + os.getcwd() + '/update/unifier.py ' + os.getcwd() + '/unifier.py'))
                self.logger.debug('Installing: ' + os.getcwd() + '/update/requirements.txt')
                status(os.system('cp ' + os.getcwd() + '/update/requirements.txt ' + os.getcwd() + '/requirements.txt'))
                self.logger.debug('Installing: ' + os.getcwd() + '/update_check/update.json')
                if legacy:
                    current['version'] = version
                    current['legacy'] = release
                    with open('plugins/system.json', 'w+') as file:
                        json.dump(current,file)
                else:
                    status(os.system('cp ' + os.getcwd() + '/update_check/update.json ' + os.getcwd() + '/plugins/system.json'))
                    with open('plugins/system.json', 'r') as file:
                        newcurrent = json.load(file)
                    newcurrent.pop('legacy')
                    with open('plugins/system.json', 'w+') as file:
                        json.dump(newcurrent, file)
                for file in os.listdir(os.getcwd() + '/update/cogs'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/cogs/' + file)
                    status(
                        os.system('cp ' + os.getcwd() + '/update/cogs/' + file + ' ' + os.getcwd() + '/cogs/' + file))
                for file in os.listdir(os.getcwd() + '/update/utils'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/utils/' + file)
                    status(
                        os.system('cp ' + os.getcwd() + '/update/utils/' + file + ' ' + os.getcwd() + '/utils/' + file))
                self.logger.debug('Updating config.json')
                with open('config.json', 'r') as file:
                    oldcfg = json.load(file)
                with open('update/config.json', 'r') as file:
                    newcfg = json.load(file)
                for key in newcfg:
                    if not key in list(oldcfg.keys()):
                        oldcfg.update({key: newcfg[key]})
                with open('config.json', 'w') as file:
                    json.dump(oldcfg, file, indent=4)
                if should_reboot:
                    self.bot.update = True
                    self.logger.info('Upgrade complete, reboot required')
                    embed.title = f'{self.bot.ui_emojis.success} {selector.get("restart_title")}'
                    embed.description =selector.get("restart_body")
                    embed.colour = self.bot.colors.success
                    await msg.edit(embed=embed)
                else:
                    self.logger.info('Restarting extensions')
                    f':white_check_mark: {selector.get("downloading")}\n:white_check_mark: {selector.get("installing")}\n:hourglass_flowing_sand: {selector.get("reloading")}'
                    await msg.edit(embed=embed)
                    for cog in list(self.bot.extensions):
                        self.logger.debug('Restarting extension: ' + cog)
                        await self.preunload(cog)
                        self.bot.reload_extension(cog)
                    self.logger.info('Upgrade complete')
                    embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
                    embed.description = selector.get("success_body")
                    embed.colour = self.bot.colors.success
                    await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed, attempting rollback')
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.colour = self.bot.colors.error
                try:
                    self.logger.debug('Reverting: ' + os.getcwd() + '/unifier.py')
                    status(os.system('cp ' + os.getcwd() + '/old/unifier.py ' + os.getcwd() + '/unifier.py'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/data.json')
                    status(os.system('cp ' + os.getcwd() + '/old/data.json ' + os.getcwd() + '/data.json'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/plugins/system.json')
                    status(os.system('cp ' + os.getcwd() + '/old/plugins/system.json ' + os.getcwd() + '/plugins/system.json'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/config.json')
                    status(os.system('cp ' + os.getcwd() + '/old/config.json ' + os.getcwd() + '/config.json'))
                    for file in os.listdir(os.getcwd() + '/old/cogs'):
                        self.logger.debug('Reverting: ' + os.getcwd() + '/cogs/' + file)
                        status(
                            os.system('cp ' + os.getcwd() + '/old/cogs/' + file + ' ' + os.getcwd() + '/cogs/' + file))
                    self.logger.info('Rollback success')
                    embed.description = selector.get("rollback")
                except:
                    self.logger.exception('Rollback failed')
                    self.logger.critical(
                        'The rollback failed. Visit https://unichat-wiki.pixels.onl/setup-selfhosted/upgrading-unifier/manual-rollback for recovery steps.')
                    embed.description = selector.get("rollback_fail")
                await msg.edit(embed=embed)
                return
        else:
            embed = nextcord.Embed(title=f'{self.bot.ui_emojis.install} {selector.rawget("downloading_title","sysmgr.install")}', description=selector.rawget("downloading_body",'sysmgr.install'))

            try:
                with open('plugins/'+plugin+'.json') as file:
                    plugin_info = json.load(file)
            except:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("notfound_title")}'
                embed.description = selector.get("notfound_body")
                if plugin=='force':
                    embed.description = embed.description + selector.fget('hint_force',values={'prefix':self.bot.command_prefix})
                embed.colour = self.bot.colors.error
                await ctx.send(embed=embed)
                return
            embed.set_footer(text=selector.rawget("trust",'sysmgr.install'))
            msg = await ctx.send(embed=embed)
            url = plugin_info['repository']
            try:
                os.system('rm -rf ' + os.getcwd() + '/plugin_install')
                await self.bot.loop.run_in_executor(None, lambda: status(os.system(
                    'git clone ' + url + ' ' + os.getcwd() + '/plugin_install')))
                with open('plugin_install/plugin.json', 'r') as file:
                    new = json.load(file)
                if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                    embed.title = f'{self.bot.ui_emojis.error} {selector.rawget("alphanumeric_title","sysmgr.install")}'
                    embed.description = selector.rawget("alphanumeric_body",'sysmgr.install')
                    embed.colour = self.bot.colors.error
                    await msg.edit(embed=embed)
                    return
                if new['release'] <= plugin_info['release'] and not force:
                    embed.title = f'{self.bot.ui_emojis.success} {selector.get("pnoupdates_title")}'
                    embed.description = selector.get("pnoupdates_body")
                    embed.colour = self.bot.colors.success
                    await msg.edit(embed=embed)
                    return
                plugin_id = new['id']
                name = new['name']
                desc = new['description']
                version = new['version']
                modules = new['modules']
                utilities = new['utils']
                services = new['services'] if 'services' in new.keys() else []
            except:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("pfailed")}'
                embed.description = selector.rawget("invalid_repo",'sysmgr.install')
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                raise
            embed.title = f'{self.bot.ui_emojis.install} {selector.fget("question",values={"plugin":plugin_id})}'
            embed.description = selector.rawfget('plugin_info','sysmgr.install',values={'name':name,'version':version,'desc':desc})
            embed.colour = 0xffcc00
            btns = ui.ActionRow(
                nextcord.ui.Button(style=nextcord.ButtonStyle.green, label=selector.get("upgrade"), custom_id=f'accept', disabled=False),
                nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label=selector.rawfget("nevermind","sysmgr.install"), custom_id=f'reject', disabled=False)
            )
            components = ui.MessageComponents()
            components.add_row(btns)
            await msg.edit(embed=embed, view=components)

            def check(interaction):
                return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

            try:
                interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
            except:
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                return await msg.edit(view=components)
            if interaction.data['custom_id'] == 'reject':
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                return await interaction.response.edit_message(view=components)

            await interaction.response.edit_message(embed=embed, view=None)
            try:
                try:
                    if 'requirements' in list(new.keys()):
                        self.logger.debug('Installing dependencies')
                        newdeps = new['requirements']
                        try:
                            olddeps = plugin_info['requirements']
                        except:
                            olddeps = []
                        for dep in olddeps:
                            if dep in newdeps:
                                newdeps.remove(dep)
                        if len(newdeps) > 0:
                            self.logger.debug('Installing: ' + ' '.join(newdeps))
                            await self.bot.loop.run_in_executor(None, lambda: status(
                                os.system('python3 -m pip install --no-dependencies ' + ' '.join(newdeps))
                            ))
                except:
                    self.logger.exception('Dependency installation failed')
                    raise RuntimeError()
                self.logger.info('Upgrading Plugin')
                for module in modules:
                    self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/' + module)
                    status(os.system(
                        'cp ' + os.getcwd() + '/plugin_install/' + module + ' ' + os.getcwd() + '/cogs/' + module))
                for util in utilities:
                    self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/' + util)
                    status(os.system(
                        'cp ' + os.getcwd() + '/plugin_install/' + util + ' ' + os.getcwd() + '/utils/' + util))
                if 'emojis' in services:
                    self.logger.info('Uninstalling previous Emoji Pack')
                    home_guild = self.bot.get_guild(self.bot.config['home_guild'])
                    with open(f'emojis/{plugin_id}.json', 'r') as file:
                        oldemojipack = json.load(file)
                    with open('plugin_install/emoji.json', 'r') as file:
                        emojipack = json.load(file)
                    toreplace = []
                    for emojiname in oldemojipack['emojis']:
                        oldversion = oldemojipack['emojis'][emojiname][1]
                        ignore_replace = False
                        try:
                            newversion = emojipack['emojis'][emojiname][1]
                        except:
                            ignore_replace = True
                            newversion = oldversion + 1
                        if oldversion < newversion:
                            emoji = oldemojipack['emojis'][emojiname][0]
                            if (emoji.startswith('<:') or emoji.startswith('<a:')) and emoji.endswith('>'):
                                emoji_id = int(emoji.split(':')[2].replace('>',''))
                                self.logger.debug(f'Removing: {emoji_id}')
                                for emoji_obj in home_guild.emojis:
                                    if emoji_obj.id==emoji_id:
                                        await emoji_obj.delete()
                            if not ignore_replace:
                                toreplace.append(emojiname)

                    self.logger.info('Installing new Emoji Pack')
                    home_guild = self.bot.get_guild(self.bot.config['home_guild'])
                    for emojiname in emojipack['emojis']:
                        if emojiname in toreplace or not emojiname in oldemojipack['emojis'].keys():
                            self.logger.debug(
                                'Installing: ' + os.getcwd() + '/plugin_install/emojis/' + emojipack['emojis'][emojiname][0])
                            file = 'plugin_install/emojis/' + emojipack['emojis'][emojiname][0]
                            emoji = await home_guild.create_custom_emoji(name=emojiname, image=nextcord.File(fp=file))
                            emojipack['emojis'][
                                emojiname][0] = f'<a:{emoji.name}:{emoji.id}>' if emoji.animated else f'<:{emoji.name}:{emoji.id}>'
                        else:
                            emojipack['emojis'][emojiname][0] = oldemojipack['emojis'][emojiname][0]
                    emojipack['installed'] = True
                    with open(f'emojis/{plugin_id}.json', 'w+') as file:
                        json.dump(emojipack, file, indent=2)
                    with open(f'emojis/current.json', 'r') as file:
                        currentdata = json.load(file)
                    if currentdata['id']==plugin_id:
                        emojipack.update({'id': plugin_id})
                        with open(f'emojis/current.json', 'w+') as file:
                            json.dump(emojipack, file, indent=2)
                        self.bot.ui_emojis = Emojis(data=emojipack)
                self.logger.info('Registering plugin')
                status(
                    os.system(
                        'cp ' + os.getcwd() + '/plugin_install/plugin.json' + ' ' + os.getcwd() + '/plugins/' + plugin_id + '.json'))
                with open('plugins/' + plugin_id + '.json') as file:
                    plugin_info = json.load(file)
                    plugin_info.update({'repository': url})
                with open('plugins/' + plugin_id + '.json', 'w') as file:
                    json.dump(plugin_info, file)
                self.logger.info('Reloading extensions')
                for module in modules:
                    modname = 'cogs.' + module[:-3]
                    if modname in list(self.bot.extensions):
                        self.logger.debug('Reloading extension: ' + modname)
                        await self.preunload(modname)
                        self.bot.reload_extension(modname)
                self.logger.debug('Upgrade complete')
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
                embed.description = selector.get("success_body")
                embed.colour = self.bot.colors.success
                await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed')
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.description = selector.get("plugin_fail")
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return

    @commands.command(
        description='Activates an emoji pack. Activating the "base" emoji pack resets emojis back to vanilla.',
        aliases=['emojipack']
    )
    @restrictions.owner()
    async def uiemojis(self, ctx, *, emojipack):
        selector = language.get_selector(ctx)

        emojipack = emojipack.lower()
        if emojipack=='base':
            os.remove('emojis/current.json')
            self.bot.ui_emojis = Emojis()
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("reset")}')
        else:
            try:
                with open(f'emojis/{emojipack}.json', 'r') as file:
                    data = json.load(file)
                data.update({'id':emojipack})
                with open('emojis/current.json', 'w+') as file:
                    json.dump(data, file, indent=2)
                self.bot.ui_emojis = Emojis(data=data)
                await ctx.send(f'{self.bot.ui_emojis.success} Emoji pack {emojipack} activated.')
            except:
                self.logger.exception('An error occurred!')
                await ctx.send(f'{self.bot.ui_emojis.error} Could not activate emoji pack.')

    @commands.command(description=language.desc('sysmgr.help'))
    async def help(self,ctx):
        selector = language.get_selector(ctx)
        panel = 0
        limit = 20
        page = 0
        match = 0
        namematch = False
        descmatch = False
        cogname = ''
        cmdname = ''
        query = ''
        msg = None
        interaction = None

        # Command overrides - these commands will be shown regardless of permissions.
        # Useful if cooldowns cause checks to fail
        overrides = {
            'admin': [],
            'mod': [],
            'user': ['modping']
        }

        overrides['mod'] += overrides['user']
        overrides['admin'] += overrides['mod']

        permissions = 'user'
        if ctx.author.id in self.bot.moderators:
            permissions = 'mod'
        elif ctx.author.id in self.bot.admins:
            permissions = 'admin'
        elif ctx.author.id == self.bot.config['owner']:
            permissions = 'owner'

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel==0:
                extlist = list(self.bot.extensions)
                maxpage = math.ceil(len(extlist)/limit)-1
                if interaction:
                    if page > maxpage:
                        page = maxpage
                embed.title = f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help'
                embed.description = 'Choose an extension to get started!'
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Extension...'
                )

                selection.add_option(
                    label='All commands',
                    description='Shows commands from all extensions.',
                    value='all'
                )

                for x in range(limit):
                    index = (page*limit)+x
                    if index >= len(self.bot.cogs):
                        break
                    cog = self.bot.cogs[list(self.bot.cogs)[index]]
                    ext = list(self.bot.extensions)[index]
                    if not ext in extlist:
                        continue
                    if not cog.description:
                        description = 'No description provided'
                    else:
                        split = False
                        description = cog.description
                        if '\n' in cog.description:
                            description = description.split('\n',1)[0]
                            split = True
                        if len(description) > 100:
                            description = description[:-(len(description)-97)]+'...'
                        elif split:
                            description = description + '\n...'

                    name = cog.qualified_name
                    parts = name.split(' ')
                    offset = 0
                    for i in range(len(parts)):
                        index = i - offset
                        if len(parts)==1:
                            break
                        if parts[index].startswith(':') and parts[index].endswith(':'):
                            parts.pop(index)
                            offset += 1
                    if len(parts)==1:
                        name = parts[0]
                    else:
                        name = ' '.join(parts)

                    embed.add_field(
                        name=f'{cog.qualified_name} (`{ext}`)',
                        value=description,
                        inline=False
                    )
                    selection.add_option(
                        label=name,
                        description=description,
                        value=ext
                    )

                components.add_rows(
                    ui.ActionRow(
                        selection
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Previous',
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Next',
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label='Search',
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search
                        )
                    )
                )
            elif panel==1:
                cmds = []
                if cogname=='' or cogname=='search':
                    cmds = list(self.bot.commands)
                else:
                    for x in range(len(self.bot.extensions)):
                        if list(self.bot.extensions)[x]==cogname:
                            cmds = list(self.bot.cogs[list(self.bot.cogs)[x]].get_commands())

                offset = 0

                def search_filter(query, query_cmd):
                    if match==0:
                        return (
                            query.lower() in query_cmd.qualified_name and namematch or
                            query.lower() in query_cmd.description.lower() and descmatch
                        )
                    elif match==1:
                        return (
                            ((query.lower() in query_cmd.qualified_name and namematch) or not namematch) and
                            ((query.lower() in query_cmd.description.lower() and descmatch) or not descmatch)
                        )

                for index in range(len(cmds)):
                    cmd = cmds[index-offset]
                    if permissions=='owner':
                        canrun = True
                    else:
                        try:
                            canrun = await cmd.can_run(ctx)
                        except:
                            canrun = False or cmd.qualified_name in overrides[permissions]
                    if not canrun or (cogname=='search' and not search_filter(query,cmd)):
                        cmds.pop(index-offset)
                        offset += 1

                embed.title = (
                    f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help / {cogname}' if not cogname == '' else
                    f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help / all'
                )
                embed.description = 'Choose a command to view its info!'

                if len(cmds)==0:
                    maxpage = 0
                    embed.add_field(
                        name='No commands',
                        value=(
                            'There are no commands matching your search query.' if cogname=='search' else
                            'There are no commands in this extension.'
                        ),
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder='Command...',disabled=True
                    )
                    selection.add_option(
                        label='No commands'
                    )
                else:
                    maxpage = math.ceil(len(cmds) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder='Command...'
                    )

                    cmds = await self.bot.loop.run_in_executor(
                        None,lambda: sorted(
                            cmds,
                            key=lambda x: x.qualified_name.lower()
                        )
                    )

                    for x in range(limit):
                        index = (page * limit) + x
                        if index >= len(cmds):
                            break
                        cmd = cmds[index]
                        embed.add_field(
                            name=f'`{cmd.qualified_name}`',
                            value=cmd.description if cmd.description else 'No description provided',
                            inline=False
                        )
                        selection.add_option(
                            label=cmd.qualified_name,
                            description=(cmd.description if len(
                                cmd.description
                            ) <= 100 else cmd.description[:-(len(cmd.description) - 97)] + '...'
                                         ) if cmd.description else 'No description provided',
                            value=cmd.qualified_name
                        )

                if cogname=='search':
                    embed.description = f'Searching: {query} (**{len(cmds)}** results)'
                    maxcount = (page+1)*limit
                    if maxcount > len(cmds):
                        maxcount = len(cmds)
                    embed.set_footer(
                        text=f'Page {page + 1} of {maxpage + 1} | {page*limit+1}-{maxcount} of {len(cmds)} results'
                    )

                components.add_row(
                    ui.ActionRow(
                        selection
                    )
                )

                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Previous',
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Next',
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label='Search',
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search
                        )
                    )
                )
                if cogname=='search':
                    components.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                custom_id='match',
                                label=(
                                    'Matches any of' if match==0 else
                                    'Matches both'
                                ),
                                style=(
                                    nextcord.ButtonStyle.green if match==0 else
                                    nextcord.ButtonStyle.blurple
                                ),
                                emoji=(
                                    '\U00002194' if match==0 else
                                    '\U000023FA'
                                )
                            ),
                            nextcord.ui.Button(
                                custom_id='name',
                                label='Command name',
                                style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                            ),
                            nextcord.ui.Button(
                                custom_id='desc',
                                label='Command description',
                                style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                            )
                        )
                    )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel==2:
                cmd = self.bot.get_command(cmdname)
                embed.title = (
                    f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help / {cogname} / {cmdname}' if not cogname=='' else
                    f'{self.bot.ui_emojis.command} {self.bot.user.global_name or self.bot.user.name} help / all / {cmdname}'
                )
                embed.description =(
                    f'# **`{self.bot.command_prefix}{cmdname}`**\n{cmd.description if cmd.description else "No description provided"}'
                )
                if len(cmd.aliases) > 0:
                    aliases = []
                    for alias in cmd.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{alias}`')
                    embed.add_field(
                        name='Aliases',value='\n'.join(aliases) if len(aliases) > 1 else aliases[0],inline=False
                    )
                embed.add_field(name='Usage', value=(
                    f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(cmd.signature) > 0 else f'`{self.bot.command_prefix}{cmdname}`'), inline=False
                )
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if not cogname=='search' and panel==1:
                embed.set_footer(text=f'Page {page+1} of {maxpage+1}')
            if not msg:
                msg = await ctx.send(embed=embed,view=components,reference=ctx.message,mention_author=False)
            else:
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed,view=components)
            embed.clear_fields()

            def check(interaction):
                return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

            try:
                interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
            except:
                await msg.edit(view=None)
                break
            if interaction.type==nextcord.InteractionType.component:
                if interaction.data['custom_id']=='selection':
                    if panel==0:
                        cogname = interaction.data['values'][0]
                    elif panel==1:
                        cmdname = interaction.data['values'][0]
                    if cogname=='all':
                        cogname = ''
                    panel += 1
                    page = 0
                elif interaction.data['custom_id'] == 'back':
                    panel -= 1
                    if panel < 0:
                        panel = 0
                    page = 0
                elif interaction.data['custom_id'] == 'prev':
                    page -= 1
                elif interaction.data['custom_id'] == 'next':
                    page += 1
                elif interaction.data['custom_id'] == 'search':
                    modal = nextcord.ui.Modal(title='Search...',auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label='Search query',
                            style=nextcord.TextInputStyle.short,
                            placeholder='Type a command...'
                        )
                    )
                    await interaction.response.send_modal(modal)
                elif interaction.data['custom_id'] == 'match':
                    match += 1
                    if match > 1:
                        match = 0
                elif interaction.data['custom_id'] == 'name':
                    namematch = not namematch
                    if not namematch and not descmatch:
                        namematch = True
                elif interaction.data['custom_id'] == 'desc':
                    descmatch = not descmatch
                    if not namematch and not descmatch:
                        descmatch = True
            elif interaction.type==nextcord.InteractionType.modal_submit:
                panel = 1
                page = 0
                cogname = 'search'
                query = interaction.data['components'][0]['components'][0]['value']
                namematch = True
                descmatch = True
                match = 0

    @commands.command(hidden=True, description='Registers commands.')
    @restrictions.owner()
    async def forcereg(self, ctx, *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return
        if 'dereg' in args:
            await self.bot.delete_application_commands(*self.bot.get_all_application_commands())
            return await ctx.send('gone, reduced to atoms (hopefully)')
        await self.bot.sync_application_commands()
        return await ctx.send(f'Registered commands to bot')

    @commands.command(hidden=True, description='Views cloud backup status.')
    @restrictions.owner()
    async def cloud(self, ctx):
        embed = nextcord.Embed(
            title='Fetching backup...',description='Getting backup information from backup servers'
        )
        embed.set_footer(text='All your backups are encrypted in transit and at rest.')
        rootmsg = await ctx.send(embed=embed)
        try:
            response = (await self.check_backup())['data']
        except:
            embed.title = f'{self.bot.ui_emojis.error} Failed to fetch backup'
            embed.description = 'The server did not respond or returned an invalid response.'
            embed.colour = self.bot.colors.error
            return await rootmsg.edit(embed=embed)
        if not response:
            embed.title = f'{self.bot.ui_emojis.error} No backups'
            embed.description = 'There\'s no backups yet.'
            return await rootmsg.edit(embed=embed)

        embed.title = f'Backup info'
        embed.description = f'Saved at: <t:{response["time"]}:F>'
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    label='Restore',
                    custom_id='restore'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label='Cancel',
                    custom_id='cancel'
                )
            )
        )
        await rootmsg.edit(embed=embed,view=components)

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==rootmsg.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await rootmsg.edit(view=None)

        if interaction.data['custom_id']=='cancel':
            return await interaction.response.edit_message(view=None)

        embed.title = f'{self.bot.ui_emojis.warning} Restore this backup?'
        embed.description = (
            '- :arrow_down: config.json and data.json files will be downloaded from the backup server.\n'+
            '- :wastebasket: Existing config.json and data.json files will be **overwritten**.\n'+
            '- :warning: You **cannot** undo this operation.'
        )
        await interaction.response.edit_message(embed=embed)

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await rootmsg.edit(view=None)

        await interaction.response.edit_message(view=None)

        if interaction.data['custom_id']=='cancel':
            return

        try:
            config_restored, data_restored = await self.download()

            # convert to dict so they can be saved indented
            data_restored = orjson.loads(data_restored)
            config_restored = orjson.loads(config_restored)
            with open('data.json','w+') as file:
                json.dump(data_restored, file, indent=2)
            with open('config.json','w+') as file:
                json.dump(config_restored, file, indent=2)

            embed.title = f'{self.bot.ui_emojis.success} Restore completed'
            embed.description = 'Please reboot the bot for the changes to take effect.'
            embed.colour = self.bot.colors.success
            await rootmsg.edit(embed=embed)
        except:
            self.logger.exception('An error occurred!')
            embed.title = f'{self.bot.ui_emojis.error} Restore failed'
            embed.description = 'Data could not be restored. Please ensure your encryption password and salt is correct.'
            embed.colour = self.bot.colors.error
            await rootmsg.edit(embed=embed)

    @commands.command(description='Shows bot uptime.')
    async def uptime(self, ctx):
        embed = nextcord.Embed(
            title=f'{self.bot.user.global_name} uptime',
            description=f'The bot has been up since <t:{self.bot.ut_total}:f>.',
            color=self.bot.colors.unifier
        )
        t = round(time.time()) - self.bot.ut_total
        td = datetime.timedelta(seconds=t)
        d = td.days
        h, m, s = str(td).split(',')[len(str(td).split(',')) - 1].replace(' ', '').split(':')
        embed.add_field(
            name='Total uptime',
            value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
            inline=False
        )
        embed.add_field(
            name='Disconnects/hr',
            value=f'{round(self.bot.disconnects / (t / 3600), 2)}',
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(description='Shows bot info.')
    async def about(self, ctx):
        attr_limit = 10
        page = 0
        maxpage = math.ceil(len(attribution.keys())/attr_limit)-1
        show_attr = False
        interaction = None
        msg = None

        try:
            with open('plugins/system.json') as file:
                vinfo = json.load(file)
        except:
            vinfo = None

        while True:
            if self.bot.user.id == 1187093090415149056:
                embed = nextcord.Embed(
                    title="Unifier",
                    description="Unify servers, make worthwhile conversations.",
                    color=self.bot.colors.unifier)
            else:
                embed = nextcord.Embed(
                    title=self.bot.user.name,
                    description="Powered by Unifier",
                    color=self.bot.colors.unifier
                )
            if vinfo:
                embed.set_footer(text="Version " + vinfo['version'] + " | Made with \u2764\ufe0f by UnifierHQ")
            else:
                embed.set_footer(text="Unknown version | Made with \u2764\ufe0f by UnifierHQ")

            if not show_attr:
                embed.add_field(name="Developers", value="@green.\n@itsasheer", inline=False)
                if self.bot.user.id == 1187093090415149056:
                    embed.add_field(name="PFP made by", value="@green.\n@thegodlypenguin", inline=False)
                embed.add_field(name="View source code", value=self.bot.config['repo'], inline=False)
                view = ui.MessageComponents()
                view.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            label='Open source attribution',
                            style=nextcord.ButtonStyle.gray,
                            custom_id='attribution'
                        )
                    )
                )

                if not msg:
                    msg = await ctx.send(embed=embed,view=view)
                else:
                    await interaction.response.edit_message(embed=embed, view=view)
            else:
                embed.clear_fields()
                for index in range(
                        page*attr_limit,
                        (page+1)*attr_limit if (page+1)*attr_limit < len(attribution.keys()) else len(attribution.keys())
                ):
                    attr_data = attribution[list(attribution.keys())[index]]
                    embed.add_field(
                        name=f'{list(attribution.keys())[index]} by {attr_data["author"]}',
                        value=(
                                  f'{attr_data["description"]}\n[Source code]({attr_data["repo"]}) • '+
                                  f'[{attr_data["license"]} license]({attr_data["license_url"]})'
                        ),
                        inline=False
                    )
                view = ui.MessageComponents()
                view.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Previous',
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Next',
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
                embed.set_footer(text=f'Page {page+1} of {maxpage+1 if maxpage >= 1 else 1} | '+embed.footer.text)
                await interaction.response.edit_message(embed=embed, view=view)

            def check(interaction):
                return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
            except:
                return await msg.edit(view=None)

            if interaction.data['custom_id'] == 'attribution':
                show_attr = True
            elif interaction.data['custom_id'] == 'back':
                show_attr = False
            elif interaction.data['custom_id'] == 'prev':
                page -= 1
                if page < 0:
                    page = 0
            elif interaction.data['custom_id'] == 'next':
                page += 1
                if page > maxpage:
                    page = maxpage

    @commands.command(hidden=True, description='A command that intentionally fails.')
    @restrictions.owner()
    async def raiseerror(self, ctx):
        raise RuntimeError('here\'s your error, anything else?')

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(SysManager(bot))
