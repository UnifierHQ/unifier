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
import json
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
import hashlib
import orjson
import tomli
import tomli_w
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto import Random as CryptoRandom
from Crypto.Util.Padding import pad, unpad
import base64
import random
import requests
import time
import shutil
import datetime

# import ujson if installed
try:
    import ujson as json  # pylint: disable=import-error
except:
    pass

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
    'uvloop': {
        'author': 'magicstack',
        'description': 'Ultra fast asyncio event loop.',
        'repo': 'https://github.com/MagicStack/uvloop',
        'license': 'MIT',
        'license_url': 'https://github.com/MagicStack/uvloop/blob/master/LICENSE-MIT'
    },
    'winloop': {
        'author': 'Vizonex',
        'description': 'An Alternative library for uvloop compatability with windows',
        'repo': 'https://github.com/Vizonex/Winloop',
        'license': 'MIT',
        'license_url': 'https://github.com/Vizonex/winloop/blob/main/LICENSE-MIT'
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
    },
    'tomli': {
        'author': 'Taneli Hukkinen',
        'description': 'A lil\' TOML parser',
        'repo': 'https://github.com/hukkin/tomli',
        'license': 'MIT',
        'license_url': 'https://github.com/hukkin/tomli-w/blob/master/LICENSE'
    },
    'tomli-w': {
        'author': 'Taneli Hukkinen',
        'description': 'A lil\' TOML writer (counterpart to https://github.com/hukkin/tomli)',
        'repo': 'https://github.com/hukkin/tomli-w',
        'license': 'MIT',
        'license_url': 'https://github.com/hukkin/tomli-w/blob/master/LICENSE'
    },
    'setuptools': {
        'author': 'Python Packaging Authority',
        'description': 'Official project repository for the Setuptools build system',
        'repo': 'https://github.com/pypa/setuptools',
        'license': 'MIT',
        'license_url': 'https://github.com/pypa/setuptools/blob/master/LICENSE'
    },
    'aiomultiprocess': {
        'author': 'The Omnilib Project',
        'description': 'Take a modern Python codebase to the next level of performance.',
        'repo': 'https://github.com/omnilib/aiomultiprocess',
        'license': 'MIT',
        'license_url': 'https://github.com/omnilib/aiomultiprocess/blob/main/LICENSE'
    },
    'aiodns': {
        'author': 'aio-libs',
        'description': 'Simple DNS resolver for asyncio',
        'repo': 'https://github.com/aio-libs/aiodns',
        'license': 'MIT',
        'license_url': 'https://github.com/aio-libs/aiodns/blob/master/LICENSE'
    },
    'brotli': {
        'author': 'Google',
        'description': 'Brotli compression format',
        'repo': 'https://github.com/google/brotli',
        'license': 'MIT',
        'license_url': 'https://github.com/google/brotli/blob/master/LICENSE'
    },
    'brotlicffi': {
        'author': 'Hyper',
        'description': 'Python bindings to the Brotli compression library',
        'repo': 'https://github.com/python-hyper/brotlicffi',
        'license': 'MIT',
        'license_url': 'https://github.com/python-hyper/brotlicffi/blob/main/LICENSE'
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
    def __init__(self, data=None, devmode=False):
        if devmode:
            with open('emojis/devbase.json', 'r') as file:
                base = json.load(file)
        else:
            with open('emojis/base.json', 'r') as file:
                base = json.load(file)

        if not base['installed']:
            base.update({'emojis_pre': base['emojis']})
            for emoji in base['emojis'].keys():
                text = base['emojis'][emoji][0]
                if text.startswith(':') and text.endswith(':'):
                    base['emojis'][emoji][0] = discord_emoji.to_unicode(text)
            base['installed'] = True
            if devmode:
                with open('emojis/devbase.json', 'w+') as file:
                    # noinspection PyTypeChecker
                    json.dump(base, file, indent=2)
            else:
                with open('emojis/base.json', 'w+') as file:
                    # noinspection PyTypeChecker
                    json.dump(base, file, indent=2)

        if data:
            for key in base['emojis'].keys():
                if not key in data['emojis'].keys():
                    data['emojis'].update({key: base['emojis'][key]})
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
        self.info = data['emojis']['info'][0]
        self.safety = data['emojis']['safety'][0]
        self.gear = data['emojis']['gear'][0]
        self.loading = data['emojis']['loading'][0]

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
        selector = language.get_selector('sysmgr.error_handler', userid=ctx.author.id)
        try:
            if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, restrictions.CustomMissingArgument):
                cmdname = ctx.command.name
                cmd = self.bot.get_command(cmdname)
                embed = nextcord.Embed(color=self.bot.colors.unifier)

                helptext = selector.rawget("title", "sysmgr.help", values={"botname": self.bot.user.global_name or self.bot.user.name})

                embed.title = f'{self.bot.ui_emojis.command} {helptext} / {cmdname}'
                embed.description = (
                    f'# **`{self.bot.command_prefix}{cmdname}`**\n{cmd.description if cmd.description else selector.rawget("no_desc","sysmgr.help")}'
                )
                if len(cmd.aliases) > 0:
                    aliases = []
                    for alias in cmd.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{alias}`')
                    embed.add_field(
                        name=selector.rawget("aliases","sysmgr.help"), value='\n'.join(aliases) if len(aliases) > 1 else aliases[0], inline=False
                    )
                embed.add_field(name='Usage', value=(
                    f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(
                        cmd.signature) > 0 else f'`{self.bot.command_prefix}{cmdname}`'), inline=False
                                )
                if isinstance(error, commands.MissingRequiredArgument):
                    await ctx.send(f'{self.bot.ui_emojis.error} {selector.fget("argument",values={"arg": error.param})}',embed=embed)
                else:
                    await ctx.send(f'{self.bot.ui_emojis.error} {error}', embed=embed)
            elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.BotMissingPermissions):
                await ctx.send(f'{self.bot.ui_emojis.error} {error}')
            elif isinstance(error, commands.NoPrivateMessage):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("servers_only")}')
            elif isinstance(error, commands.PrivateMessageOnly):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("dms_only")}')
            elif isinstance(error, restrictions.NoRoomManagement):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_room_management")}')
            elif isinstance(error, restrictions.NoRoomJoin):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_room_join")}')
            elif isinstance(error, restrictions.UnknownRoom):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawfget("invalid","commons.rooms",values={"prefix": self.bot.command_prefix})}')
            elif isinstance(error, restrictions.GlobalBanned):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.fget("banned",values={"prefix": self.bot.command_prefix})}')
            elif isinstance(error, restrictions.UnderAttack):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("under_attack")}')
            elif isinstance(error, restrictions.TooManyPermissions):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.fget("too_many_perms",values={"permission": error})}')
            elif isinstance(error, commands.CheckFailure):
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("permissions")}')
            elif isinstance(error, commands.CommandOnCooldown):
                t = int(error.retry_after)
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.fget("cooldown",values={"min":t//60,"sec":t%60})}')
            else:
                error_tb = traceback.format_exc()
                self.logger.exception('An error occurred!')
                view = ui.MessageComponents()
                if ctx.author.id==self.bot.config['owner']:
                    view.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label=selector.get("view")
                            )
                        )
                    )
                msg = await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("unexpected")}',
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
                                label=selector.get("view"),
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
                            label=selector.get("view"),
                            disabled=True
                        )
                    )
                )
                await msg.edit(view=view)

                try:
                    await interaction.response.send_message(f'```\n{error_tb}```',ephemeral=True)
                except:
                    await interaction.response.send_message(selector.get("tb_sendfail"), ephemeral=True)
        except:
            self.logger.exception('An error occurred!')
            await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("handler_error")}')

class SysManager(commands.Cog, name=':wrench: System Manager'):
    """An extension that oversees a lot of the bot system.

    Developed by Green"""

    class SysExtensionLoadFailed(Exception):
        pass

    def __init__(self, bot):
        global language
        self.bot = bot

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
                    # noinspection PyTypeChecker
                    json.dump(base, file, indent=2)
            try:
                if self.bot.coreboot or self.bot.devmode:
                    raise RuntimeError()
                with open('emojis/current.json', 'r') as file:
                    data = json.load(file)
                self.bot.ui_emojis = Emojis(data=data)
            except:
                self.bot.ui_emojis = Emojis(devmode=self.bot.devmode)
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
                    try:
                        script = importlib.import_module('utils.' + plugin[:-5] + '_bridge_platform')
                        self.bot.platforms_former.update({extinfo['bridge_platform']: script})
                    except:
                        self.logger.warning('Platform support load failed! (' + extinfo["bridge_platform"] + ')')
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
                shutil.copy2('update.json', 'plugins/system.json')
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

    async def copy(self, src, dst):
        await self.bot.loop.run_in_executor(None, lambda: shutil.copy2(src,dst))

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

    async def bot_shutdown(self, ctx, restart=False):
        selector = language.get_selector('sysmgr.shutdown', userid=ctx.author.id)

        embed = nextcord.Embed(color=self.bot.colors.warning)

        if restart:
            if self.bot.b_update:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("restart_locked_title")}'
                embed.description = selector.get('restart_locked_body')
                return await ctx.send(embed=embed)
            else:
                embed.title = f'{self.bot.ui_emojis.warning} {selector.get("restart_title")}'
                embed.description = selector.get('restart_body')
        else:
            embed.title = f'{self.bot.ui_emojis.warning} {selector.get("shutdown_title")}'
            embed.description = selector.get('shutdown_body')

        components = ui.MessageComponents()

        btns_row = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red,
                label=selector.get('restart') if restart else selector.get('shutdown'),
                custom_id='shutdown'
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray,
                label=selector.rawget('nevermind','commons.navigation'),
                custom_id='cancel'
            )
        )

        options = []

        if restart:
            options = [
                nextcord.SelectOption(
                    default=True,
                    value='normal',
                    label=selector.get('normal_title'),
                    description=selector.get('normal_desc'),
                    emoji=self.bot.ui_emojis.success
                ),
                nextcord.SelectOption(
                    value='safemode',
                    label=selector.get('safemode_title'),
                    description=selector.get('safemode_desc'),
                    emoji=self.bot.ui_emojis.safety
                ),
                nextcord.SelectOption(
                    value='core',
                    label=selector.get('core_title'),
                    description=selector.get('core_desc'),
                    emoji=self.bot.ui_emojis.gear
                )
            ]
            selection = nextcord.ui.StringSelect(
                placeholder=selector.get('select'),
                max_values=1,
                min_values=1,
                custom_id='selection',
                options=options
            )

            components.add_row(
                ui.ActionRow(selection)
            )

        components.add_row(btns_row)

        msg = await ctx.send(embed=embed, view=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        mode = 'normal'

        while True:
            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)

                if interaction.data['custom_id'] == 'cancel':
                    await interaction.response.edit_message(view=None)
                    return
                elif interaction.data['custom_id'] == 'shutdown':
                    await interaction.response.edit_message(view=None)
                    break
                else:
                    mode = interaction.data['values'][0]
                    for index in range(len(options)):
                        option = options[index]
                        if option.value == mode:
                            options[index].default = True
                        else:
                            options[index].default = False

                    selection = nextcord.ui.StringSelect(
                        placeholder=selector.get('select'),
                        max_values=1,
                        min_values=1,
                        custom_id='selection',
                        options=options
                    )

                    components = ui.MessageComponents()
                    components.add_rows(ui.ActionRow(selection), btns_row)
                    await interaction.response.edit_message(view=components)
            except:
                return await msg.edit(view=None)

        embed.title = embed.title.replace(self.bot.ui_emojis.warning, self.bot.ui_emojis.loading, 1)
        await msg.edit(embed=embed)

        self.logger.info("Attempting graceful shutdown...")
        if not self.bot.coreboot:
            self.bot.bridge.backup_lock = True
        try:
            if not self.bot.coreboot:
                if self.bot.bridge.backup_running:
                    self.logger.info('Waiting for backups to complete...(Press Ctrl+C to force stop)')
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
            if restart:
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("rsuccess_title")}'
                embed.description = selector.get('rsuccess_body')
            else:
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("shutdown_title")}'
                embed.description = selector.get('success_body')
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception("Graceful shutdown failed")
            if restart:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("rfailed_title")}'
                embed.description = selector.get('rfailed_body')
            else:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed_title")}'
                embed.description = selector.get('failed_body')
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

        if restart:
            x = open('.restart', 'w+')
            if mode == 'normal':
                x.write(f'{time.time()}')
            else:
                x.write(f'{time.time()} {mode}')
            x.close()

        self.logger.info("Closing bot session")
        await self.bot.session.close()
        self.logger.info("Shutdown complete")
        await self.bot.close()
        sys.exit(0)

    @tasks.loop(seconds=300)
    async def changestatus(self):
        dt = datetime.datetime.now(datetime.timezone.utc)
        month = dt.month
        status_messages = {
            'regular': [
                ["playing", "with the API"],
                ["listening", "my own code"],
                ["playing", "with commands"],
                ["watching", "the matrix"],
                ["playing", "with emojis"],
                ["watching", "webhooks"],
                ["custom", "Unifying servers like they're nothing"],
                ["custom", "Communities, connected."],
                ["custom", "Made for communities, by communities"],
                ["custom", "it's unifying time"],
                ["custom", "Made with \u2764\ufe0f by UnifierHQ"]
            ],
            'spooky': [
                ["custom", "PUMP, IT IS DA SPOOKEH MONTH"],
                ["custom", "ooooOOOOOOOooooo"],
                ["custom", "spooky scary skeletons"],
                ["custom", "no it's not christmas season yet"],
                ["custom", "WARNING: messages may be haunted"]
            ],
            'christmas': [
                ["custom", "ho ho ho"],
                ["listening", "All I Want For Christmas Is You"],
                ["playing", "with snow"],
                ["watching", "a snowman"],
                ["custom", "waiting for santa"],
                ["custom", f"preparing for {dt.year + 1}"],
                ["custom", "Fun fact: Unifier was born on Dec 20"]
            ]
        }

        bounds = {
            'spooky': {
                'min': 10,
                'max': 10
            },
            'christmas': {
                'min': 12,
                'max': 12
            }
        }

        option = 'regular'

        if self.bot.config['enable_seasonal_status']:
            for key in bounds.keys():
                bound = bounds[key]
                if bound['min'] <= month <= bound['max']:
                    option = key
                    break

        if len(self.bot.config['custom_status_messages']) > 0:
            status_messages['regular'] = self.bot.config['custom_status_messages']

        new_stat = random.choice(status_messages[option])
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
            x = open('config.toml','r',encoding='utf-8')
            contents = x.read()
            x.close()
            config_text, config_iv = await self.encrypt(str.encode(contents), __pass, __salt)
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
            except:
                e = traceback.format_exc()
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

    @commands.command(hidden=True, description=language.desc('sysmgr.eval'))
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
            if 'bot.token' in body or 'dotenv' in body or '.env' in body or 'environ' in body or 'tokenstore' in body:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("phrase_blocked")}')
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
        tstart = time.time()
        try:
            with redirect_stdout(stdout):
                # ret = await func() to return output
                await func()
        except:
            value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
            await ctx.send(f'{self.bot.ui_emojis.error} ' + selector.get('error'), reference=ctx.message)
            if token_start in value:
                return await ctx.author.send(selector.get('output_blocked'))
            await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            exec_time = round(time.time() - tstart, 4)
            value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
            if token_start in value:
                return await ctx.send(f'{self.bot.ui_emojis.error} ' + selector.get('blocked'))
            if value == '':
                await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"exec_time": exec_time})}')
            else:
                await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"exec_time": exec_time})}\n```\n{value}```')

    @commands.command(aliases=['poweroff'], hidden=True, description=language.desc('sysmgr.shutdown'))
    @restrictions.owner()
    async def shutdown(self, ctx):
        await self.bot_shutdown(ctx)

    @commands.command(aliases=['reboot'], hidden=True, description=language.desc('sysmgr.restart'))
    @restrictions.owner()
    async def restart(self, ctx):
        await self.bot_shutdown(ctx, restart=True)

    @commands.command(aliases=['plugins'],hidden=True,description=language.desc('sysmgr.modifiers'))
    @restrictions.owner()
    async def modifiers(self, ctx, *, plugin=None):
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
                    text = f'- {selector.rawget('name', f'{ext.replace('cogs.','',1)}.cogmeta',default='') or cog.qualified_name} (`{ext}`)'
                else:
                    text = f'{text}\n- {selector.rawget('name', f'{ext.replace('cogs.','',1)}.cogmeta',default='') or cog.qualified_name} (`{ext}`)'
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
            title=selector.rawget('name', f'{extension}.cogmeta',default='') or ext_info.qualified_name,
            description=selector.rawget('description', f'{extension}.cogmeta',default='') or ext_info.description,
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
        cmds = len(self.bot.get_application_commands())
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
            except:
                e = traceback.format_exc()
                failed.append(extension)
                errors.append(e)
                if len(text) == 0:
                    text = f'```diff\n- [FAIL] {extension}'
                else:
                    text += f'\n- [FAIL] {extension}'
        if len(self.bot.get_all_application_commands()) < cmds and self.bot.uses_v3:
            # update local commands
            await self.bot.sync_application_commands(update_known=False, delete_unknown=False)
        await msg.edit(content=selector.rawfget(
            'completed', 'sysmgr.reload_services', values={
                'success': len(extensions)-len(failed), 'total': len(extensions), 'text': text
            }
        ))
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'{selector.rawget("extension","sysmgr.reload_services")} `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\n{selector.rawget("extension","sysmgr.reload_services")} `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_services")}**\n{text}')

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
            except:
                e = traceback.format_exc()
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
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_services")}**\n{text}')

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
            except:
                e = traceback.format_exc()
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
            await ctx.author.send(f'**{selector.rawget("fail_logs","sysmgr.reload_services")}**\n{text}')

    @commands.command(hidden=True,description='Installs a plugin.')
    @restrictions.owner()
    async def install(self, ctx, url):
        if self.bot.devmode:
            return await ctx.send('Command unavailable in devmode')
        selector = language.get_selector(ctx)
        if self.bot.update:
            return await ctx.send(selector.rawget('locked','commons.plugins'))

        if url.endswith('/'):
            url = url[:-1]
        if not url.endswith('.git'):
            url = url + '.git'
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.loading} {selector.get("downloading_title")}', description=selector.get("downloading_body"))
        embed.set_footer(text=selector.get("trust"))
        msg = await ctx.send(embed=embed)
        try:
            try:
                await self.bot.loop.run_in_executor(None, lambda: shutil.rmtree('plugin_install'))
            except:
                pass
            await self.bot.loop.run_in_executor(None, lambda: status(os.system(
                'git clone ' + url + ' plugin_install')))
            with open('plugin_install/plugin.json', 'r') as file:
                new = json.load(file)
            if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("alphanumeric_title")}'
                embed.description = selector.get("alphanumeric_body")
                embed.colour = self.bot.colors.error
                await msg.edit(embed=embed)
                return
            if new['id']+'.json' in os.listdir('plugins'):
                with open('plugins/'+new['id']+'.json', 'r') as file:
                    current = json.load(file)
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("exists_title")}'
                embed.description = selector.fget("exists_body", values={"name": current["name"], "version": current["version"]})
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
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.description = selector.fget('unsupported', values={'minimum': minimum})
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
            try:
                await self.bot.loop.run_in_executor(None, lambda: status(os.system('git --version')))
            except:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                embed.description = selector.rawget("git","commons.navigation")
                embed.colour = self.bot.colors.error
                return await msg.edit(embed=embed)

            embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
            embed.description = selector.get('invalid_repo')
            embed.colour = self.bot.colors.error
            return await msg.edit(embed=embed)

        embed.title = f'{self.bot.ui_emojis.install} Install `{plugin_id}`?'
        embed.description = f'Name: `{name}`\nVersion: `{version}`\n\n{desc}'
        embed.colour = 0xffcc00

        services_text = ''
        for service in services:
            if service=='content_protection':
                text = f':shield: **{selector.get("content_protection_title")}**\n{selector.get("content_protection_desc")}'
            elif service=='content_processing':
                text = f':art: **{selector.get("content_processing_title")}**\n{selector.get("content_processing_desc")}'
            elif service=='bridge_platform':
                text = f':handshake: **{selector.get("bridge_platform_title")}**\n{selector.get("bridge_platform_desc")}'
                if not nups_platform or nups_platform.lower()=='meta' or not bool(re.match("^[a-z0-9_-]*$", nups_platform.lower())):
                    embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                    embed.description = selector.get("invalid_platform")
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)
            elif service=='emojis':
                text = (
                    f':joy: **{selector.get("emojis_title")}**\n'+
                    selector.fget("emojis_desc",values={'prefix': self.bot.command_prefix, 'plugin_id':plugin_id})
                )
                with open('plugin_install/emoji.json', 'r') as file:
                    emojipack = json.load(file)
                emojis = len(emojipack['emojis'].keys())
                home_guild = self.bot.get_guild(self.bot.config['home_guild'])
                if emojis > home_guild.emoji_limit - len(home_guild.emojis):
                    embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'
                    embed.description = selector.fget("no_emoji_slots", values={"required": emojis, "available": home_guild.emoji_limit - len(home_guild.emojis)})
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)
            else:
                text = f':grey_question: `{service}`\n{selector.get("unknown_desc")}'
            if len(services_text)==0:
                services_text = text
            else:
                services_text = f'{services_text}\n\n{text}'

        embed.add_field(
            name=selector.get("services"),
            value=services_text
        )
        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.green, label=selector.get("install"), custom_id=f'accept', disabled=False),
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label=selector.rawget("nevermind", "commons.navigation"), custom_id=f'reject', disabled=False)
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

        embed.title = embed.title.replace(self.bot.ui_emojis.install, self.bot.ui_emojis.loading, 1)

        await interaction.response.edit_message(embed=embed, view=None)
        try:
            try:
                if 'requirements' in list(new.keys()):
                    self.logger.debug('Installing dependencies')
                    newdeps = new['requirements']
                    if len(newdeps) > 0:
                        self.logger.debug('Installing: ' + ' '.join(newdeps))
                        bootloader_config = self.bot.boot_config.get('bootloader', {})
                        if sys.platform == 'win32':
                            binary = bootloader_config.get('binary', 'py -3')
                            await self.bot.loop.run_in_executor(None, lambda: status(
                                os.system(f'{binary} -m pip install --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                            ))
                        else:
                            binary = bootloader_config.get('binary', 'python3')
                            await self.bot.loop.run_in_executor(None, lambda: status(
                                os.system(f'{binary} -m pip install --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                            ))
            except:
                self.logger.exception('Dependency installation failed')
                raise RuntimeError()
            self.logger.info('Installing Plugin')
            for module in modules:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+module)
                await self.copy('plugin_install/' + module, 'cogs/' + module)
            for util in utilities:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+util)
                await self.copy('plugin_install/' + util, 'utils/' + util)
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
                    # noinspection PyTypeChecker
                    json.dump(emojipack, file, indent=2)
            if 'config.toml' in os.listdir('plugin_install'):
                self.logger.debug('Installing config.toml')
                if not os.path.exists('plugin_config'):
                    os.mkdir('plugin_config')
                await self.copy('plugin_install/config.toml', 'plugin_config/' + plugin_id + '.toml')
            self.logger.info('Registering plugin')
            await self.copy('plugin_install/plugin.json', 'plugins/' + plugin_id + '.json')
            with open('plugins/' + plugin_id + '.json') as file:
                plugin_info = json.load(file)
                plugin_info.update({'repository':url})
            with open('plugins/' + plugin_id + '.json', 'w') as file:
                # noinspection PyTypeChecker
                json.dump(plugin_info,file)
            self.logger.info('Activating extensions')
            for module in modules:
                modname = 'cogs.' + module[:-3]
                self.logger.debug('Activating extension: '+modname)
                try:
                    self.bot.load_extension(modname)
                except:
                    self.logger.warning(modname + ' could not be activated.')
                    embed.set_footer(text=f':warning: {selector.get("load_failed")}')
            self.logger.debug('Installation complete')
            embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
            embed.description = selector.get("success_body")
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Install failed')
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("postfail_title")}'
            embed.description = selector.get("postfail_body")
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Uninstalls a plugin.')
    @restrictions.owner()
    async def uninstall(self, ctx, plugin):
        if self.bot.devmode:
            return await ctx.send('Command unavailable in devmode')
        if not ctx.author.id == self.bot.config['owner']:
            return

        selector = language.get_selector(ctx)

        if self.bot.update:
            return await ctx.send(selector.rawget('locked','commons.plugins'))

        plugin = plugin.lower()
        if plugin=='system':
            return await ctx.send(selector.get("system"))
        embed = nextcord.Embed(title='placeholder', description=selector.get("warning"))
        embed.colour = 0xffcc00
        try:
            with open('plugins/' + plugin + '.json') as file:
                plugin_info = json.load(file)
        except:
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("notfound_title")}'
            embed.description = selector.get("notfound_body")
            embed.colour = self.bot.colors.error
            await ctx.send(embed=embed)
            return
        embed.title = selector.fget("question", values={"plugin": plugin_info['id']})
        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.red, label=selector.get("uninstall"), custom_id=f'accept', disabled=False),
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label=selector.rawget("nevermind", "commons.navigation"), custom_id=f'reject', disabled=False)
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
            embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
            embed.description = selector.get("success_body")
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Uninstall failed')
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("postfail_title")}'
            embed.description = selector.get("postfail_body")
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Upgrades Unifier or a plugin.')
    @restrictions.owner()
    async def upgrade(self, ctx, plugin='system', *, args=''):
        if self.bot.devmode:
            return await ctx.send('Command unavailable in devmode')
        if not ctx.author.id == self.bot.config['owner']:
            return

        selector = language.get_selector(ctx)

        if self.bot.update:
            return await ctx.send(selector.rawget('disabled','sysmgr.reload'))

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
                title=f'{self.bot.ui_emojis.loading} {selector.get("checking_title")}',
                description=selector.get('checking_body')
            )
            msg = await ctx.send(embed=embed)
            available = []
            clone_success = False
            try:
                try:
                    await self.bot.loop.run_in_executor(None, lambda: shutil.rmtree('update_check'))
                except:
                    pass
                await self.bot.loop.run_in_executor(None, lambda: status(os.system(
                    'git clone --branch ' + self.bot.config['branch'] + ' ' + self.bot.config[
                        'check_endpoint'] + ' update_check')))
                clone_success = True
                with open('plugins/system.json', 'r') as file:
                    current = json.load(file)
                with open('update_check/update.json', 'r') as file:
                    new = json.load(file)
                if new['release'] > current['release'] or force:
                    available.append(
                        [new['version'], selector.get("latest"), new['release'], -1, new['reboot'], new['b_reboot']]
                    )
                index = 0
                for legacy in new['legacy']:
                    if (
                            legacy['lower'] <= current['release'] <= legacy['upper'] and (
                                legacy['release'] > (
                                    current['legacy'] if 'legacy' in current.keys() else -1
                                ) or force
                            )
                    ):
                        available.append(
                            [legacy['version'], selector.get("legacy"), legacy['release'], index, legacy['reboot'], legacy['b_reboot']]
                        )
                    index += 1
                update_available = len(available) >= 1
            except:
                self.logger.exception('An error occurred!')
                try:
                    await self.bot.loop.run_in_executor(None, lambda: status(os.system('git --version')))
                except:
                    embed.title = f'{self.bot.ui_emojis.error} {selector.get("checkfail_title")}'
                    embed.description = selector.rawget("git","commons.navigation")
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)

                embed.title = f'{self.bot.ui_emojis.error} {selector.get("checkfail_title")}'
                embed.description = selector.get("checkfail_body")

                if not clone_success:
                    embed.description = selector.get('clonefail_body')

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
                b_reboot = available[selected][5]
                embed.title = f'{self.bot.ui_emojis.install} {selector.get("available_title")}'
                embed.description = selector.fget('available_body',values={
                    'current_ver':current['version'],'current_rel':current['release'],'new_ver':version,'new_rel':release
                })
                embed.remove_footer()
                embed.colour = 0xffcc00
                if legacy:
                    should_reboot = reboot >= (current['legacy'] if 'legacy' in current.keys() and
                                               type(current['legacy']) is int else -1)
                    should_b_reboot = b_reboot >= (current['legacy'] if 'legacy' in current.keys() and
                                                   type(current['legacy']) is int else -1)
                else:
                    should_reboot = reboot >= current['release']
                    should_b_reboot = b_reboot >= current['release']
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
                embed.title = f'{self.bot.ui_emojis.loading} {selector.get("backup_title")}'
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
                folder = os.getcwd() + '/old/utils'
                try:
                    os.mkdir(folder)
                except:
                    pass
                folder = os.getcwd() + '/old/languages'
                try:
                    os.mkdir(folder)
                except:
                    pass
                folder = os.getcwd() + '/old/plugins'
                try:
                    os.mkdir(folder)
                except:
                    pass
                folder = os.getcwd() + '/old/boot'
                try:
                    os.mkdir(folder)
                except:
                    pass
                for file in os.listdir(os.getcwd() + '/cogs'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/cogs/' + file)
                    try:
                        await self.copy('cogs/' + file, 'old/cogs/' + file)
                    except IsADirectoryError:
                        continue
                for file in os.listdir(os.getcwd() + '/utils'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/utils/' + file)
                    try:
                        await self.copy('utils/' + file, 'old/utils/' + file)
                    except IsADirectoryError:
                        continue
                for file in os.listdir(os.getcwd() + '/plugins'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/plugins/' + file)
                    try:
                        await self.copy('plugins/' + file, 'old/plugins/' + file)
                    except IsADirectoryError:
                        continue
                for file in os.listdir(os.getcwd() + '/languages'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/languages/' + file)
                    try:
                        await self.copy('languages/' + file, 'old/languages/' + file)
                    except IsADirectoryError:
                        continue
                for file in os.listdir(os.getcwd() + '/boot'):
                    self.logger.debug('Backing up: ' + os.getcwd() + '/boot/' + file)
                    try:
                        await self.copy('boot/' + file, 'old/boot/' + file)
                    except IsADirectoryError:
                        continue
                self.logger.debug('Backing up: ' + os.getcwd() + '/unifier.py')
                await self.copy('unifier.py', 'old/unifier.py')
                self.logger.debug('Backing up: ' + os.getcwd() + '/data.json')
                await self.copy('data.json', 'old/data.json')
                self.logger.debug('Backing up: ' + os.getcwd() + '/config.toml')
                await self.copy('config.toml', 'old/config.toml')
                self.logger.debug('Backing up: ' + os.getcwd() + '/boot_config.json')
                await self.copy('boot_config.json', 'old/boot_config.json')
            except:
                if no_backup:
                    self.logger.warning('Backup skipped, requesting final confirmation.')
                    embed.description = f'- :x: {selector.get("skipped_backup")}\n- :wrench: {selector.get("modification_wipe")}\n- :warning: {selector.get("no_abort")}'
                elif ignore_backup:
                    self.logger.warning('Backup failed, continuing anyways')
                    embed.description = f'- :x: {selector.get("failed_backup")}\n- :wrench: {selector.get("modification_wipe")}\n- :warning: {selector.get("no_abort")}'
                else:
                    self.logger.exception('An error occurred!')
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
            embed.title = f'{self.bot.ui_emojis.loading} {selector.get("upgrading")}'
            embed.description = f'{self.bot.ui_emojis.loading} {selector.get("downloading")}\n:x: {selector.get("installing")}\n:x: {selector.get("reloading")}'
            await interaction.response.edit_message(embed=embed, view=None)
            self.logger.info('Starting upgrade')
            try:
                self.logger.debug('Purging old update files')
                try:
                    await self.bot.loop.run_in_executor(None, lambda: shutil.rmtree('update'))
                except:
                    pass
                self.logger.info('Downloading from remote repository...')
                await self.bot.loop.run_in_executor(None, lambda: os.system(
                    'git clone --branch ' + version + ' --single-branch --depth 1 ' + self.bot.config[
                        'files_endpoint'] + '/unifier.git update'
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

                with open('.install.json') as file:
                    install_data = json.load(file)

                if install_data == 'stable':
                    x = open('update/requirements_stable.txt')
                    newdeps = x.read().split('\n')
                    x.close()
                else:
                    x = open('update/requirements.txt')
                    newdeps = x.read().split('\n')
                    x.close()

                try:
                    if install_data == 'stable':
                        x = open('requirements_stable.txt')
                        olddeps = x.read().split('\n')
                        x.close()
                    else:
                        x = open('requirements.txt')
                        olddeps = x.read().split('\n')
                        x.close()
                except:
                    self.logger.warning('Could not find requirements.txt, installing all dependencies')
                    olddeps = []
                for dep in olddeps:
                    if dep.startswith('git+'):
                        continue
                    try:
                        newdeps.remove(dep)
                    except:
                        pass
                if len(newdeps) > 0:
                    self.logger.debug('Installing: ' + ' '.join(newdeps))
                    bootloader_config = self.bot.boot_config.get('bootloader', {})
                    if sys.platform == 'win32':
                        binary = bootloader_config.get('binary', 'py -3')
                        await self.bot.loop.run_in_executor(None, lambda: status(
                            os.system(f'{binary} -m pip install -U ' + '"' + '" "'.join(newdeps) + '"')
                        ))
                    else:
                        binary = bootloader_config.get('binary', 'python3')
                        await self.bot.loop.run_in_executor(None, lambda: status(
                            os.system(f'{binary} -m pip install -U ' + '"' + '" "'.join(newdeps) + '"')
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
                embed.description = f'{self.bot.ui_emojis.success} {selector.get("downloading")}\n{self.bot.ui_emojis.loading} {selector.get("installing")}\n:x: {selector.get("reloading")}'
                await msg.edit(embed=embed)
                self.logger.debug('Installing: ' + os.getcwd() + '/update/unifier.py')
                await self.copy('update/unifier.py', 'unifier.py')
                self.logger.debug('Installing: ' + os.getcwd() + '/update/requirements.txt')
                await self.copy('update/requirements.txt', 'requirements.txt')
                self.logger.debug('Installing: ' + os.getcwd() + '/update/requirements_stable.txt')
                await self.copy('update/requirements_stable.txt', 'requirements_stable.txt')
                self.logger.debug('Installing: ' + os.getcwd() + '/update_check/plugins/system.json')
                if legacy:
                    current['version'] = version
                    current['legacy'] = release
                    with open('plugins/system.json', 'w+') as file:
                        # noinspection PyTypeChecker
                        json.dump(current,file)
                else:
                    await self.copy('update/plugins/system.json', 'plugins/system.json')
                for file in os.listdir(os.getcwd() + '/update/cogs'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/cogs/' + file)
                    await self.copy('update/cogs/' + file, 'cogs/' + file)
                for file in os.listdir(os.getcwd() + '/update/utils'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/utils/' + file)
                    await self.copy('update/utils/' + file, 'utils/' + file)
                for file in os.listdir(os.getcwd() + '/update/boot'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/boot/' + file)
                    await self.copy('update/boot/' + file, 'boot/' + file)
                self.logger.debug('Installing: ' + os.getcwd() + '/update/run.sh')
                await self.copy('update/run.sh', 'run.sh')
                self.logger.debug('Installing: ' + os.getcwd() + '/update/run.bat')
                await self.copy('update/run.bat', 'run.bat')
                self.logger.debug('Installing: ' + os.getcwd() + '/update/emojis/base.json')
                await self.copy('update/emojis/base.json', 'emojis/base.json')
                self.logger.debug('Updating languages')
                for file in os.listdir(os.getcwd() + '/update/languages'):
                    if not file.endswith('.json'):
                        continue

                    self.logger.debug('Installing: ' + os.getcwd() + '/update/languages/' + file)
                    await self.copy('update/languages/' + file, 'languages/' + file)
                self.logger.debug('Updating config.toml')
                with open('config.toml','rb') as file:
                    oldcfg = tomli.load(file)
                with open('update/config.toml', 'rb') as file:
                    newcfg = tomli.load(file)

                newdata = {}

                for key in oldcfg:
                    if type(oldcfg[key]) is dict:
                        for newkey in oldcfg[key]:
                            newdata.update({newkey: oldcfg[key][newkey]})
                    else:
                        newdata.update({key: oldcfg[key]})

                oldcfg = newdata

                def update_toml(old, new):
                    for key in new:
                        for newkey in new[key]:
                            if newkey in old.keys():
                                new[key].update({newkey: old[newkey]})
                    return new

                oldcfg = update_toml(oldcfg, newcfg)

                with open('config.toml', 'wb+') as file:
                    tomli_w.dump(oldcfg, file)
                if should_reboot:
                    self.bot.update = True
                    self.logger.info('Upgrade complete, reboot required')
                    embed.title = f'{self.bot.ui_emojis.success} {selector.get("restart_title")}'
                    if should_b_reboot:
                        self.bot.b_update = True
                        embed.description = selector.get("shutdown_body")
                    else:
                        embed.description = selector.get("restart_body")
                    embed.colour = self.bot.colors.success
                    await msg.edit(embed=embed)
                else:
                    self.logger.info('Reloading extensions')
                    embed.description = f'{self.bot.ui_emojis.success} {selector.get("downloading")}\n{self.bot.ui_emojis.success} {selector.get("installing")}\n{self.bot.ui_emojis.loading} {selector.get("reloading")}'
                    await msg.edit(embed=embed)
                    for cog in list(self.bot.extensions):
                        self.logger.debug('Reloading extension: ' + cog)
                        try:
                            await self.preunload(cog)
                            self.bot.reload_extension(cog)
                        except:
                            self.logger.warning(cog+' could not be reloaded.')
                            embed.set_footer(text=f':warning: {selector.get("reload_warning")}')
                    if self.bot.uses_v3:
                        await self.bot.sync_application_commands(update_known=False, delete_unknown=False)
                    self.logger.info('Updating localization')
                    self.bot.langmgr = langmgr.LanguageManager(self.bot)
                    self.bot.langmgr.load()
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
                    await self.copy('old/unifier.py', 'unifier.py')
                    self.logger.debug('Reverting: ' + os.getcwd() + '/data.json')
                    await self.copy('old/data.json', 'data.json')
                    self.logger.debug('Reverting: ' + os.getcwd() + '/plugins/system.json')
                    await self.copy('old/plugins/system.json', 'plugins/system.json')
                    self.logger.debug('Reverting: ' + os.getcwd() + '/config.toml')
                    await self.copy('old/config.toml', 'config.toml')
                    for file in os.listdir(os.getcwd() + '/old/cogs'):
                        self.logger.debug('Reverting: ' + os.getcwd() + '/cogs/' + file)
                        await self.copy('old/cogs/' + file, 'cogs/' + file)
                    self.logger.info('Rollback success')
                    embed.description = selector.get("rollback")
                except:
                    self.logger.exception('Rollback failed')
                    self.logger.critical(
                        'The rollback failed. Visit https://unichat-wiki.pixels.onl/setup-selfhosted/upgrading-unifier/manual-rollback for recovery steps.'
                    )
                    embed.description = selector.get("rollback_fail")
                await msg.edit(embed=embed)
                return
        else:
            embed = nextcord.Embed(title=f'{self.bot.ui_emojis.loading} {selector.rawget("downloading_title","sysmgr.install")}', description=selector.rawget("downloading_body",'sysmgr.install'))

            try:
                with open('plugins/'+plugin+'.json') as file:
                    plugin_info = json.load(file)
            except:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("notfound_title")}'
                embed.description = selector.get("notfound_body")
                if plugin=='force':
                    embed.description = embed.description + '\n' + selector.fget('hint_force',values={'prefix':self.bot.command_prefix})
                embed.colour = self.bot.colors.error
                await ctx.send(embed=embed)
                return
            embed.set_footer(text=selector.rawget("trust",'sysmgr.install'))
            msg = await ctx.send(embed=embed)
            url = plugin_info['repository']
            try:
                try:
                    await self.bot.loop.run_in_executor(None, lambda: shutil.rmtree('plugin_install'))
                except:
                    pass
                await self.bot.loop.run_in_executor(None, lambda: status(os.system(
                    'git clone ' + url + ' plugin_install')))
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
                try:
                    await self.bot.loop.run_in_executor(None, lambda: status(os.system('git --version')))
                except:
                    embed.title = f'{self.bot.ui_emojis.error} {selector.get("pfailed")}'
                    embed.description = 'Git is not installed.'
                    embed.colour = self.bot.colors.error
                    return await msg.edit(embed=embed)

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
                nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label=selector.rawfget("nevermind","commons.navigation"), custom_id=f'reject', disabled=False)
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
                            bootloader_config = self.bot.boot_config.get('bootloader', {})
                            if sys.platform == 'win32':
                                binary = bootloader_config.get('binary', 'py -3')
                                await self.bot.loop.run_in_executor(None, lambda: status(
                                    os.system(f'{binary} -m pip install --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                                ))
                            else:
                                binary = bootloader_config.get('binary', 'python3')
                                await self.bot.loop.run_in_executor(None, lambda: status(
                                    os.system(f'{binary} -m pip install --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                                ))
                except:
                    self.logger.exception('Dependency installation failed')
                    raise RuntimeError()
                self.logger.info('Upgrading Plugin')
                for module in modules:
                    self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/' + module)
                    await self.copy('plugin_install/' + module, 'cogs/' + module)
                for util in utilities:
                    self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/' + util)
                    await self.copy('plugin_install/' + util, 'utils/' + util)
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
                        # noinspection PyTypeChecker
                        json.dump(emojipack, file, indent=2)
                    with open(f'emojis/current.json', 'r') as file:
                        currentdata = json.load(file)
                    if currentdata['id']==plugin_id:
                        emojipack.update({'id': plugin_id})
                        with open(f'emojis/current.json', 'w+') as file:
                            # noinspection PyTypeChecker
                            json.dump(emojipack, file, indent=2)
                        self.bot.ui_emojis = Emojis(data=emojipack)

                if not os.path.exists('plugin_config'):
                    os.mkdir('plugin_config')

                if 'config.toml' in os.listdir('plugin_install'):
                    if f'{plugin_id}.toml' in os.listdir('plugin_config'):
                        self.logger.debug('Updating config.toml')
                        with open(f'plugin_config/{plugin_id}.toml', 'rb') as file:
                            oldcfg = tomli.load(file)
                        with open('plugin_install/config.toml', 'rb') as file:
                            newcfg = tomli.load(file)

                        newdata = {}

                        for key in oldcfg:
                            if type(oldcfg[key]) is dict:
                                for newkey in oldcfg[key]:
                                    newdata.update({newkey: oldcfg[key][newkey]})
                            else:
                                newdata.update({key: oldcfg[key]})

                        oldcfg = newdata

                        def update_toml(old, new):
                            for key in new:
                                for newkey in new[key]:
                                    if newkey in old.keys():
                                        new[key].update({newkey: old[newkey]})
                            return new

                        oldcfg = update_toml(oldcfg, newcfg)

                        with open(f'plugin_config/{plugin_id}.toml', 'wb+') as file:
                            tomli_w.dump(oldcfg, file)
                    else:
                        self.logger.debug('Installing config.toml')
                        if not os.path.exists('plugin_config'):
                            os.mkdir('plugin_config')
                        await self.copy('plugin_install/config.toml', 'plugin_config/' + plugin_id + '.toml')

                self.logger.info('Registering plugin')
                await self.copy('plugin_install/plugin.json', 'plugins/' + plugin_id + '.json')
                with open('plugins/' + plugin_id + '.json') as file:
                    plugin_info = json.load(file)
                    plugin_info.update({'repository': url})
                with open('plugins/' + plugin_id + '.json', 'w') as file:
                    # noinspection PyTypeChecker
                    json.dump(plugin_info, file)
                self.logger.info('Reloading extensions')
                for module in modules:
                    modname = 'cogs.' + module[:-3]
                    if modname in list(self.bot.extensions):
                        self.logger.debug('Reloading extension: ' + modname)
                        try:
                            await self.preunload(modname)
                            self.bot.reload_extension(modname)
                        except:
                            self.logger.warning(modname+' could not be reloaded.')
                            embed.set_footer(text=f':warning: {selector.get("reload_warning")}')
                self.logger.debug('Upgrade complete')
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
                embed.description = selector.get("success_body")

                if 'bridge_platform' in plugin_info['services']:
                    embed.description = embed.description + '\n' + selector.get('success_rpossible')

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
        if self.bot.devmode:
            return await ctx.send('Command unavailable in devmode')
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
                    # noinspection PyTypeChecker
                    json.dump(data, file, indent=2)
                self.bot.ui_emojis = Emojis(data=data)
                await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("activated",values={"emojipack":emojipack})}')
            except:
                self.logger.exception('An error occurred!')
                await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("error")}')

    @commands.command(description=language.desc('sysmgr.help'))
    async def help(self,ctx,query=None):
        selector = language.get_selector(ctx)
        panel = 0
        limit = 20
        page = 0
        match = 0
        namematch = False
        descmatch = False
        cogname = ''
        cmdname = ''
        msg = None
        interaction = None
        if not query:
            query = ''
        else:
            panel = 1
            cogname = 'search'
            namematch = True
            descmatch = True
            match = 0

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

        helptext = selector.fget("title", values={"botname": self.bot.user.global_name or self.bot.user.name})

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
                embed.title = f'{self.bot.ui_emojis.command} {helptext}'
                embed.description = selector.get("choose_ext")
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_ext")
                )

                selection.add_option(
                    label=selector.get("all_title"),
                    description=selector.get("all_body"),
                    value='all'
                )

                for x in range(limit):
                    index = (page*limit)+x
                    if index >= len(self.bot.cogs):
                        break
                    cog = self.bot.cogs[list(self.bot.cogs)[index]]
                    ext = list(self.bot.extensions)[index]
                    extname = ext.replace('cogs.','',1)

                    if not ext in extlist:
                        continue
                    if not cog.description:
                        description = selector.get("no_desc")
                    else:
                        split = False

                        try:
                            description = selector.rawget('description', f'{extname}.cogmeta',default='') or cog.description
                        except:
                            description = cog.description

                        if '\n' in cog.description:
                            description = description.split('\n',1)[0]
                            split = True
                        if len(description) > 100:
                            description = description[:-(len(description)-97)]+'...'
                        elif split:
                            description = description + '\n...'

                    localized_name = selector.rawget('name', f'{extname}.cogmeta',default='') or cog.qualified_name

                    parts = localized_name.split(' ')
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
                        name=f'{localized_name} (`{ext}`)',
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
                            label=selector.rawget("prev","commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next","commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget("search","commons.search"),
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

                def in_aliases(query, query_cmd):
                    for alias in query_cmd.aliases:
                        if query.lower() in alias.lower():
                            return True

                def search_filter(query, query_cmd):
                    if match==0:
                        return (
                            (query.lower() in query_cmd.qualified_name.lower() or
                             in_aliases(query,query_cmd)) and namematch or
                            query.lower() in query_cmd.description.lower() and descmatch
                        )
                    elif match==1:
                        return (
                            (((query.lower() in query_cmd.qualified_name.lower() or
                               in_aliases(query,query_cmd)) and namematch) or not namematch) and
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

                localized_cogname = selector.get("search_nav") if cogname == 'search' else cogname

                embed.title = (
                    f'{self.bot.ui_emojis.command} {helptext} / {localized_cogname}' if not cogname == '' else
                    f'{self.bot.ui_emojis.command} {helptext} / {selector.get("all")}'
                )
                embed.description = selector.get("choose_cmd")

                if len(cmds)==0:
                    maxpage = 0
                    embed.add_field(
                        name=selector.get("noresults_title"),
                        value=(
                            selector.get("noresults_body_search") if cogname=='search' else
                            selector.get("noresults_body_ext")
                        ),
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_cmd"),disabled=True
                    )

                    # this doesn't need to be localized, as it's merely a placeholder and can't be selected
                    selection.add_option(label='No commands')
                else:
                    maxpage = math.ceil(len(cmds) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_cmd")
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

                        cmddesc = (
                                selector.rawget('description', f'{cogname.replace('cogs.', '', 1)}.{cmd.qualified_name}', default='')
                                or
                                selector.desc_from_all(cmd.qualified_name)
                                or
                                cmd.description or selector.get("no_desc")
                        )
                        
                        embed.add_field(
                            name=f'`{cmd.qualified_name}`',
                            value=cmddesc,
                            inline=False
                        )
                        selection.add_option(
                            label=cmd.qualified_name,
                            description=(cmddesc if len(cmddesc) <= 100 else cmddesc[:-(len(cmddesc) - 97)] + '...'),
                            value=cmd.qualified_name
                        )

                if cogname=='search':
                    embed.description = selector.rawfget("search_results", "commons.search", values={"query": query, "results": len(cmds)})
                    maxcount = (page+1)*limit
                    if maxcount > len(cmds):
                        maxcount = len(cmds)
                    embed.set_footer(
                        text=f'Page {page + 1} of {maxpage + 1} | {page*limit+1}-{maxcount} of {len(cmds)} results'
                    )
                    embed.set_footer(
                        text=f'{selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1})}'+
                             ' | '+
                             f'{selector.rawfget("result_count","commons.search",values={"lower":page*limit+1,"upper":maxcount,"total":len(cmds)})}'
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
                            label=selector.rawget('prev','commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget('next','commons.navigation'),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget('search','commons.search'),
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
                                    selector.rawget('match_any','commons.search') if match==0 else
                                    selector.rawget('match_both','commons.search')
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
                                label=selector.get("cmd_name"),
                                style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                            ),
                            nextcord.ui.Button(
                                custom_id='desc',
                                label=selector.get("cmd_desc"),
                                style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                            )
                        )
                    )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget('back','commons.navigation'),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel==2:
                cmd = self.bot.get_command(cmdname)
                localized_cogname = selector.get("search_nav") if cogname == 'search' else cogname
                embed.title = (
                    f'{self.bot.ui_emojis.command} {helptext} / {localized_cogname} / {cmdname}' if not cogname=='' else
                    f'{self.bot.ui_emojis.command} {helptext} / {selector.get("all")} / {cmdname}'
                )

                cmddesc = cmd.description if cmd.description else selector.get("no_desc")

                try:
                    cmddesc = selector.desc_from_all(cmd.qualified_name)
                except:
                    pass

                embed.description =f'# **`{self.bot.command_prefix}{cmdname}`**\n{cmddesc}'
                if len(cmd.aliases) > 0:
                    aliases = []
                    for alias in cmd.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{alias}`')
                    embed.add_field(
                        name=selector.get("aliases"),value='\n'.join(aliases) if len(aliases) > 1 else aliases[0],inline=False
                    )
                embed.add_field(name=selector.get("usage"), value=(
                    f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(cmd.signature) > 0 else f'`{self.bot.command_prefix}{cmdname}`'), inline=False
                )
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget('back','commons.navigation'),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if not cogname=='search' and panel==1:
                embed.set_footer(text=selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1}))
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
                try:
                    await msg.edit(view=None)
                except:
                    pass
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
                    modal = nextcord.ui.Modal(title=selector.rawget('search_title','commons.search'),auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label=selector.rawget('query','commons.search'),
                            style=nextcord.TextInputStyle.short,
                            placeholder=selector.get("search_prompt")
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

    @commands.command(name='register-commands', hidden=True, description='Registers commands.')
    @restrictions.owner()
    async def register_commands(self, ctx, *, args=''):
        selector = language.get_selector(ctx)
        if 'dereg' in args:
            await self.bot.delete_application_commands(*self.bot.get_all_application_commands())
            return await ctx.send(selector.get("atoms"))
        await self.bot.sync_application_commands()
        return await ctx.send(selector.get("registered"))

    @commands.command(hidden=True, description='Views cloud backup status.')
    @restrictions.owner()
    async def cloud(self, ctx):
        selector = language.get_selector(ctx)
        embed = nextcord.Embed(
            title=selector.get("fetching_title"),description=selector.get("fetching_body")
        )
        embed.set_footer(text=selector.get("encrypted"))
        rootmsg = await ctx.send(embed=embed)
        try:
            response = (await self.check_backup())['data']
        except:
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("invalid_title")}'
            embed.description = selector.get("invalid_body")
            embed.colour = self.bot.colors.error
            return await rootmsg.edit(embed=embed)
        if not response:
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("nobackup_title")}'
            embed.description = selector.get("nobackup_body")
            return await rootmsg.edit(embed=embed)

        embed.title = selector.get("info_title")
        embed.description = selector.fget("backup_body",values={"unix":response["time"]})
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    label=selector.get("restore"),
                    custom_id='restore'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
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

        embed.title = f'{self.bot.ui_emojis.warning} {selector.get("question")}'
        embed.description = (
            f'- :arrow_down: {selector.get("download")}\n'+
            f'- :wastebasket: {selector.get("overwrite")}\n'+
            f'- :warning: {selector.get("noundo")}'
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
                # noinspection PyTypeChecker
                json.dump(data_restored, file, indent=2)

            x = open('config.toml','w+')
            x.write(config_restored)
            x.close()

            self.bot.db.load_data()

            embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
            embed.description = selector.get("success_body")
            embed.colour = self.bot.colors.success
            await rootmsg.edit(embed=embed)
        except:
            self.logger.exception('An error occurred!')
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed_title")}'
            embed.description = selector.get("failed_body")
            embed.colour = self.bot.colors.error
            await rootmsg.edit(embed=embed)

    @commands.command(description='Shows bot uptime.')
    async def uptime(self, ctx):
        selector = language.get_selector(ctx)
        embed = nextcord.Embed(
            title=selector.fget("title",values={"botname":self.bot.user.global_name or self.bot.user.name}),
            description=selector.fget("body",values={"unix":self.bot.ut_total}),
            color=self.bot.colors.unifier
        )
        t = round(time.time()) - self.bot.ut_total
        td = datetime.timedelta(seconds=t)
        d = td.days
        h, m, s = str(td).split(',')[len(str(td).split(',')) - 1].replace(' ', '').split(':')
        embed.add_field(
            name=selector.get("total_title"),
            value=selector.fget("total_body",values={"days":d,"hours":int(h),"minutes":int(m),"seconds":int(s)}),
            inline=False
        )
        embed.add_field(
            name=selector.get("disconnects"),
            value=f'{round(self.bot.disconnects / (t / 3600), 2)}',
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(description='Shows bot info.')
    async def about(self, ctx):
        selector = language.get_selector(ctx)
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
                    description=selector.get("slogan"),
                    color=self.bot.colors.unifier)
            else:
                embed = nextcord.Embed(
                    title=self.bot.user.global_name or self.bot.user.name,
                    description="Powered by Unifier",
                    color=self.bot.colors.unifier
                )
            if vinfo:
                embed.set_footer(text="Version " + vinfo['version'] + " | Made with \u2764\ufe0f by UnifierHQ")
            else:
                embed.set_footer(text="Unknown version | Made with \u2764\ufe0f by UnifierHQ")

            if not show_attr:
                embed.add_field(name=selector.get("developers"), value="@green.\n@itsasheer", inline=False)
                if self.bot.user.id == 1187093090415149056:
                    embed.add_field(name=selector.get("profile_pic"), value="@green.\n@thegodlypenguin", inline=False)
                embed.add_field(name=selector.get("source_code"), value=self.bot.config['repo'], inline=False)
                view = ui.MessageComponents()
                view.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            label=selector.get("oss_attrib"),
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
                                  f'{attr_data["description"]}\n[{selector.get("repo_link")}]({attr_data["repo"]}) • '+
                                  f'[{selector.fget("license",values={"license": attr_data["license"]})}]({attr_data["license_url"]})'
                        ),
                        inline=False
                    )
                view = ui.MessageComponents()
                view.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("prev","commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next","commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back","commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
                embed.set_footer(text=f'Page {page+1} of {maxpage+1 if maxpage >= 1 else 1} | '+embed.footer.text)
                embed.set_footer(text=selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1})+' | '+embed.footer.text)
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
