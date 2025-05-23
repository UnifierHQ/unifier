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
from nextcord.ext import commands, tasks, application_checks
import inspect
import textwrap
from contextlib import redirect_stdout
from utils import log, ui, langmgr, restrictions as r, restrictions_legacy as r_legacy, slash as slash_helper
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
import tomllib
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
from enum import Enum
from typing import Union, Optional

# import ujson if installed
try:
    import ujson as json  # pylint: disable=import-error
except:
    pass

restrictions = r.Restrictions()
restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_helper.SlashHelper(language)
secrets_issuer = None

# Below are attributions to the works we used to build Unifier (including our own).
# If you've modified Unifier to use more works, please add it here.
attribution = {
    'unifier': {
        'author': 'UnifierHQ',
        'description': 'A cross-server and cross-platform bridge bot that works just as fast as you can type \U0001F680',
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
        'license': 'BSD-3-Clause',
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
    'tomllib': {
        'author': 'Taneli Hukkinen',
        'description': 'A lil\' TOML parser',
        'repo': 'https://github.com/hukkin/tomllib',
        'license': 'MIT',
        'license_url': 'https://github.com/hukkin/tomllib-w/blob/master/LICENSE'
    },
    'tomllib-w': {
        'author': 'Taneli Hukkinen',
        'description': 'A lil\' TOML writer (counterpart to https://github.com/hukkin/tomllib)',
        'repo': 'https://github.com/hukkin/tomllib-w',
        'license': 'MIT',
        'license_url': 'https://github.com/hukkin/tomllib-w/blob/master/LICENSE'
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
    },
    'jellyfish': {
        'author': 'James Turk',
        'description': '🪼 a python library for doing approximate and phonetic matching of strings. ',
        'repo': 'https://github.com/jamesturk/jellyfish',
        'license': 'MIT',
        'license_url': 'https://github.com/jamesturk/jellyfish/blob/main/LICENSE'
    },
    'tld': {
        'author': 'Artur Barseghyan',
        'description': 'Extracts the top level domain (TLD) from the URL given.',
        'repo': 'https://github.com/barseghyanartur/tld',
        'license': 'Multiple (GPL-2.0/LGPL-2.1/MPL-1.1)',
        'license_url': 'https://github.com/barseghyanartur/tld/blob/master/LICENSE.rst'
    }
}

# Command option types to human-readable format
option_types = {
    nextcord.ApplicationCommandOptionType.sub_command: 'subcommand',
    nextcord.ApplicationCommandOptionType.sub_command_group: 'subcommand group',
    nextcord.ApplicationCommandOptionType.string: 'string',
    nextcord.ApplicationCommandOptionType.integer: 'integer',
    nextcord.ApplicationCommandOptionType.boolean: 'boolean',
    nextcord.ApplicationCommandOptionType.user: 'user',
    nextcord.ApplicationCommandOptionType.channel: 'channel',
    nextcord.ApplicationCommandOptionType.role: 'role',
    nextcord.ApplicationCommandOptionType.mentionable: 'mentionable',
    nextcord.ApplicationCommandOptionType.number: 'number',
    nextcord.ApplicationCommandOptionType.attachment: 'attachment'
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
    def __init__(self, bot, get_commands_func, get_universal_func):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'exc_handler', self.bot.loglevel)
        self.get_all_commands = get_commands_func
        self.get_universal_commands = get_universal_func

    async def handle(self, ctx, error):
        if isinstance(ctx, commands.Context):
            author = ctx.author
        else:
            author = ctx.user

        selector = language.get_selector('sysmgr.error_handler', userid=author.id)

        async def respond(*args, **kwargs):
            if isinstance(ctx, commands.Context):
                return await ctx.send(*args, **kwargs)
            else:
                returned = await ctx.send(*args, **kwargs, ephemeral=True)
                if isinstance(returned, nextcord.WebhookMessage):
                    return returned
                return await returned.fetch()

        def check_instance(error, error_type):
            if error.__cause__:
                return check_instance(error.__cause__, error_type) or isinstance(error, error_type)
            else:
                return isinstance(error, error_type)

        try:
            if check_instance(error, commands.MissingRequiredArgument) or check_instance(error, restrictions.CustomMissingArgument):
                cmd = ctx.command
                cmdname = ctx.command.qualified_name
                embed = nextcord.Embed(color=self.bot.colors.unifier)

                cmds = self.get_all_commands()
                _universal, ignore = self.get_universal_commands(cmds, legacy=True)

                legacy_form = cmd
                slash_form = None

                for slash_cmd in ignore:
                    if slash_cmd.qualified_name == cmd.qualified_name:
                        slash_form = slash_cmd
                        break

                is_universal = legacy_form and slash_form

                helptext = selector.rawfget("title", "sysmgr.help", values={"botname": self.bot.user.global_name or self.bot.user.name})

                cmdtext = slash_form.get_mention() if is_universal else f'**`{self.bot.command_prefix}{cmdname}`**'
                cmddesc = selector.desc_from_all(cmd.qualified_name) or selector.rawget("no_desc", "sysmgr.help")

                embed.title = f'{self.bot.ui_emojis.command} {helptext} / {cmdname}'
                embed.description = f'# {cmdtext}\n{cmddesc}'

                if is_universal:
                    embed.description = embed.description + f'\n\n:sparkles: {selector.rawget("universal","sysmgr.help")}'

                slash_signature = ''
                if slash_form:
                    options = slash_form.options
                    options_text = []

                    for option, option_obj in options.items():
                        option_type = option_types.get(option_obj.payload['type'], 'string')

                        if option_obj.payload.get('required', False):
                            options_text.append(f'<{option_obj.name}: {option_type}>')
                        else:
                            options_text.append(f'[{option_obj.name}: {option_type}]')

                    options_text_final = ''
                    if len(options_text) > 0:
                        options_text_final = ' ' + ' '.join(options_text)

                    slash_signature = f'`/{slash_form.qualified_name}{options_text_final}`'

                if len(cmd.aliases) > 0:
                    aliases = []
                    for alias in cmd.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{alias}`')
                    embed.add_field(
                        name=selector.rawget("aliases","sysmgr.help"),
                        value='- ' + ('\n- '.join(aliases) if len(aliases) > 1 else aliases[0]),
                        inline=False
                    )

                legacy_signature = (
                    f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(cmd.signature) > 0 else
                    f'`{self.bot.command_prefix}{cmdname}`'
                )

                if is_universal:
                    embed.add_field(
                        name='Usage', value=(
                            '- ' + selector.rawfget(
                                "usage_slash_universal", "sysmgr.help", values={"command": slash_signature}
                            ) + '\n' +
                            '- ' + selector.rawfget(
                                "usage_legacy_universal", "sysmgr.help", values={"signature": legacy_signature}
                            )
                        ), inline=False
                    )
                else:
                    embed.add_field(
                        name='Usage', value=(
                            '- ' + selector.rawfget(
                                "usage_legacy_universal", "sysmgr.help", values={"signature": legacy_signature}
                            )
                        ), inline=False
                    )

                if check_instance(error, commands.MissingRequiredArgument):
                    missing = error.param.name
                    await ctx.send(f'{self.bot.ui_emojis.error} {selector.fget("argument",values={"arg": missing})}',embed=embed)
                else:
                    await ctx.send(f'{self.bot.ui_emojis.error} {error}', embed=embed)
            elif (
                    check_instance(error, commands.MissingPermissions)
                    or check_instance(error, commands.BotMissingPermissions)
                    or check_instance(error, application_checks.ApplicationMissingPermissions)
                    or check_instance(error, application_checks.ApplicationBotMissingPermissions)
            ):
                await respond(f'{self.bot.ui_emojis.error} {error}')
            elif check_instance(error, commands.NoPrivateMessage) or check_instance(error, application_checks.ApplicationNoPrivateMessage):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("servers_only")}')
            elif check_instance(error, commands.PrivateMessageOnly) or check_instance(error, application_checks.ApplicationPrivateMessageOnly):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("dms_only")}')
            elif check_instance(error, restrictions.NoRoomManagement):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("no_room_management")}')
            elif check_instance(error, restrictions.NoRoomJoin):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("no_room_join")}')
            elif check_instance(error, restrictions.UnknownRoom):
                await respond(f'{self.bot.ui_emojis.error} {selector.rawfget("invalid","commons.rooms",values={"prefix": self.bot.command_prefix})}')
            elif check_instance(error, restrictions.GlobalBanned):
                await respond(f'{self.bot.ui_emojis.error} {selector.fget("banned",values={"prefix": self.bot.command_prefix})}')
            elif check_instance(error, restrictions.UnderAttack):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("under_attack")}')
            elif check_instance(error, restrictions.TooManyPermissions):
                await respond(f'{self.bot.ui_emojis.error} {selector.fget("too_many_perms",values={"permission": error})}')
            elif check_instance(error, commands.CheckFailure) or check_instance(error, nextcord.errors.ApplicationCheckFailure):
                await respond(f'{self.bot.ui_emojis.error} {selector.get("permissions")}')
            elif check_instance(error, commands.CommandOnCooldown):
                t = int(error.retry_after)
                await respond(f'{self.bot.ui_emojis.error} {selector.fget("cooldown",values={"min":t//60,"sec":t % 60})}')
            elif check_instance(error, nextcord.errors.NotFound):
                return
            else:
                if isinstance(ctx, commands.Context):
                    error_tb = traceback.format_exc()
                    self.logger.exception('An error occurred!')
                else:
                    error_tb = ''.join(traceback.format_exception(
                        type(error), error, error.__traceback__
                    ))
                    self.logger.exception('An error occurred!', exc_info=error)
                view = ui.MessageComponents()
                if author.id==self.bot.config['owner']:
                    view.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label=selector.get("view")
                            )
                        )
                    )
                msg = await respond(f'{self.bot.ui_emojis.error} {selector.get("unexpected")}',
                                    view=view)

                def check(interaction):
                    if not interaction.message:
                        return False
                    return interaction.message.id==msg.id and interaction.user.id==author.id

                if not author.id == self.bot.config['owner']:
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
                    await interaction.response.send_message(f'```\n{error_tb}```', ephemeral=True)
                except:
                    await interaction.response.send_message(selector.get("tb_sendfail"), ephemeral=True)
        except:
            self.logger.exception('An error occurred!')
            await respond(f'{self.bot.ui_emojis.error} {selector.get("handler_error")}')

class CogAction(Enum):
    load = 0
    reload = 1
    unload = 2

class SysManager(commands.Cog, name=':wrench: System Manager'):
    """An extension that oversees a lot of the bot system."""

    class SysExtensionLoadFailed(Exception):
        pass

    def __init__(self, bot):
        global language
        self.bot = bot

        restrictions.attach_bot(self.bot)
        restrictions_legacy.attach_bot(self.bot)

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

        self.bot.exhandler = CommandExceptionHandler(self.bot, self.get_all_commands, self.get_universal_commands)
        self.logger = log.buildlogger(self.bot.package, 'sysmgr', self.bot.loglevel)

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
                extension_clean = extension
                if extension_clean.startswith('cogs.') or extension_clean.startswith('cogs/'):
                    extension_clean = extension[5:]

                try:
                    extras = {}

                    if extension_clean in sysext.get('uses_tokenstore', []):
                        # noinspection PyUnresolvedReferences
                        extras.update({'tokenstore': secrets_issuer.get_secret('system')})
                        self.logger.debug(f'Issued TokenStore to {extension}')
                    if extension_clean in sysext.get('uses_storage', []):
                        # noinspection PyUnresolvedReferences
                        extras.update({'storage': secrets_issuer.get_storage('system')})
                        self.logger.debug(f'Issued SecureStorage to {extension}')

                    try:
                        self.bot.load_extension('cogs.' + extension[:-3], extras=extras)
                    except nextcord.ext.commands.errors.InvalidSetupArguments:
                        # assume cog does not use extras kwargs
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
                            extras = {}

                            if extension in extinfo.get('uses_tokenstore', []):
                                # noinspection PyUnresolvedReferences
                                extras.update({'tokenstore': secrets_issuer.get_secret(plugin[:-5])})
                                self.logger.debug(f'Issued TokenStore to {extension}')
                            if extension in extinfo.get('uses_storage', []):
                                # noinspection PyUnresolvedReferences
                                extras.update({'storage': secrets_issuer.get_storage(plugin[:-5])})
                                self.logger.debug(f'Issued SecureStorage to {extension}')

                            try:
                                self.bot.load_extension('cogs.' + extension[:-3], extras=extras)
                            except nextcord.ext.commands.errors.InvalidSetupArguments:
                                # assume cog does not use extras kwargs
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

        try:
            with open('boot_config.json') as file:
                boot_config = json.load(file)
        except:
            pass
        else:
            self.pip_user_arg = ' --user' if not boot_config['bootloader'].get('global_dep_install', False) else ''

    def get_all_commands(self, cog=None):
        def extract_subcommands(__command):
            subcommands = []
            if (
                    type(__command) is nextcord.MessageApplicationCommand or
                    type(__command) is nextcord.UserApplicationCommand
            ):
                return []

            if type(__command) is commands.Group:
                for child in __command.commands:
                    subcommands += extract_subcommands(child)
                return subcommands
            elif type(__command) is commands.Command:
                return [__command]
            else:
                if __command.children:
                    for child in __command.children.keys():
                        subcommands += extract_subcommands(__command.children[child])
                    return subcommands
                else:
                    return [__command]

        if cog:
            legacy_commands = list(cog.get_commands())
            new_commands = [
                cmd for cmd in self.bot.get_application_commands()
                if cmd.parent_cog.qualified_name == cog.qualified_name
            ]
        else:
            legacy_commands = list(self.bot.commands)
            new_commands = list(self.bot.get_application_commands())

        legacy_commands_extracted = []
        application_commands = []
        for command in new_commands:
            application_commands += extract_subcommands(command)
        for command in legacy_commands:
            legacy_commands_extracted += extract_subcommands(command)

        return legacy_commands_extracted + application_commands

    def get_universal_commands(self, cmds, legacy=False):
        new_commands = []
        legacy_commands = []
        universal_commands = []
        should_ignore = []

        for cmd in cmds:
            if legacy:
                if type(cmd) is commands.Command:
                    new_commands.append(cmd)
                elif isinstance(cmd, nextcord.BaseApplicationCommand) or isinstance(cmd, nextcord.SlashApplicationSubcommand):
                    legacy_commands.append(cmd)
            else:
                if type(cmd) is commands.Command:
                    legacy_commands.append(cmd)
                elif isinstance(cmd, nextcord.BaseApplicationCommand) or isinstance(cmd, nextcord.SlashApplicationSubcommand):
                    new_commands.append(cmd)

        for cmd in new_commands:
            is_universal = False
            for legacy_cmd in legacy_commands:
                if cmd.qualified_name == legacy_cmd.qualified_name:
                    is_universal = True
                    should_ignore.append(legacy_cmd)
                    break

            if is_universal:
                universal_commands.append(cmd)

        return universal_commands, should_ignore

    def encrypt_string(self, hash_string):
        sha_signature = \
            hashlib.sha256(hash_string.encode()).hexdigest()
        return sha_signature

    async def cog_before_invoke(self, ctx):
        ctx.user = ctx.author

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
        __apikey = self.bot.tokenstore.retrieve('CLOUD_BACKUP_API_KEY')
        __headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {__apikey}"
        }
        try:
            __salt = self.bot.config['cloud_backup_salt']
            __pass = self.bot.tokenstore.retrieve('CLOUD_BACKUP_PASSWORD')
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
        __apikey = self.bot.tokenstore.retrieve('CLOUD_BACKUP_API_KEY')
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
            if not interaction.message:
                return False
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
                await self.bot.bridge.backup()
                self.logger.info("Backup complete")
            if restart:
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("rsuccess_title")}'
                embed.description = selector.get('rsuccess_body')
            else:
                embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
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

    async def manage_cog(self, cogs: list, action: CogAction):
        toload = []
        skip = []
        success = []
        failed = {}
        requires_tokens = {}
        requires_storage = {}

        async def run_check(plugin_name, plugin):
            if not plugin['shutdown']:
                return

            script = importlib.import_module('utils.' + plugin_name + '_check')
            await script.check(self.bot)

        def allow_tokenstore(plugin, cog):
            if not plugin in requires_tokens.keys():
                requires_tokens.update({plugin: []})

            requires_tokens[plugin].append(cog)

        def allow_storage(plugin, cog):
            if not plugin in requires_storage.keys():
                requires_storage.update({plugin: []})

            requires_storage[plugin].append(cog)

        for cog in cogs:
            if cog == 'system':
                toload.append('system')
                skip.append('system')
                failed.update({cog: 'Cannot manage the entire system plugin, manage the individual modules instead'})
                continue

            cog_exists = f'{cog}.py' in os.listdir('cogs')
            plugin_exists = f'{cog}.json' in os.listdir('plugins')

            plugin_data = {}

            if plugin_exists:
                with open('plugins/' + cog + '.json') as file:
                    plugin_data = json.load(file)

            if plugin_exists and cog_exists:
                if self.bot.config['plugin_priority']:
                    toload.extend(plugin_data['modules'])

                    for ext in plugin_data['modules']:
                        extension_clean = ext
                        if extension_clean.startswith('cogs.') or extension_clean.startswith('cogs/'):
                            extension_clean = ext[5:]

                        if not ext.startswith('cogs.'):
                            ext = 'cogs.' + ext
                        if ext.endswith('.py'):
                            ext = ext[:-3]

                        if extension_clean in plugin_data.get('uses_tokenstore', []):
                            allow_tokenstore(plugin_data['id'], ext)
                        if extension_clean in plugin_data.get('uses_storage', []):
                            allow_storage(plugin_data['id'], ext)

                    if not action == CogAction.load:
                        try:
                            await run_check(cog, plugin_data)
                        except:
                            skip.extend([f'cogs.{module}' for module in plugin_data['modules']])
                            for child_cog in [f'cogs.{module}' for module in plugin_data['modules']]:
                                failed.update({child_cog: 'Could not run pre-unload script.'})
                else:
                    toload.append(f'cogs.{cog}')
            elif plugin_exists:
                toload.extend([f'cogs.{module[:-3]}' for module in plugin_data['modules']])

                for ext in plugin_data['modules']:
                    extension_clean = ext
                    if extension_clean.startswith('cogs.') or extension_clean.startswith('cogs/'):
                        extension_clean = ext[5:]

                    if not ext.startswith('cogs.'):
                        ext = 'cogs.' + ext
                    if ext.endswith('.py'):
                        ext = ext[:-3]

                    if extension_clean in plugin_data.get('uses_tokenstore', []):
                        allow_tokenstore(plugin_data['id'], ext)
                    if extension_clean in plugin_data.get('uses_storage', []):
                        allow_storage(plugin_data['id'], ext)

                if not action == CogAction.load:
                    try:
                        await run_check(cog, plugin_data)
                    except:
                        skip.extend([f'cogs.{module}' for module in plugin_data['modules']])
                        for child_cog in [f'cogs.{module}' for module in plugin_data['modules']]:
                            failed.update({child_cog: 'Could not run pre-unload script.'})
            elif cog_exists:
                toload.append(f'cogs.{cog}')
                cog_clean = cog+'.py' if not cog.endswith('.py') else cog

                for plugin in os.listdir('plugins'):
                    if not plugin.endswith('.json'):
                        continue

                    with open('plugins/' + plugin) as file:
                        pluginfo = json.load(file)

                    if cog_clean in pluginfo['modules']:
                        if cog_clean in pluginfo.get('uses_tokenstore', []):
                            allow_tokenstore(plugin[:-5], f'cogs.{cog}')
                        if cog_clean in pluginfo.get('uses_storage', []):
                            allow_storage(plugin[:-5], f'cogs.{cog}')
            else:
                toload.append(f'cogs.{cog}')
                skip.append(f'cogs.{cog}')
                failed.update({cog: 'The cog or plugin does not exist.'})

        for toload_cog in toload:
            if toload_cog in skip:
                continue
            try:
                if action == CogAction.load:
                    extras = {}

                    # Generate TokenStoreWrapper if needed
                    for plugin in requires_tokens.keys():
                        if toload_cog in requires_tokens[plugin]:
                            # noinspection PyUnresolvedReferences
                            extras.update({'tokenstore': secrets_issuer.get_secret(plugin)})
                            self.logger.debug(f'Issued TokenStore to {toload_cog}')
                            break

                    # Generate SecureStorageWrapper if needed
                    for plugin in requires_storage.keys():
                        if toload_cog in requires_storage[plugin]:
                            # noinspection PyUnresolvedReferences
                            extras.update({'storage': secrets_issuer.get_storage(plugin)})
                            self.logger.debug(f'Issued SecureStorage to {toload_cog}')
                            break

                    try:
                        self.bot.load_extension(toload_cog, extras=extras)
                    except nextcord.ext.commands.errors.InvalidSetupArguments:
                        # assume cog does not use extras kwargs
                        self.bot.load_extension(toload_cog)
                elif action == CogAction.reload:
                    extras = {}

                    # Generate TokenStoreWrapper if needed
                    for plugin in requires_tokens.keys():
                        if toload_cog in requires_tokens[plugin]:
                            # noinspection PyUnresolvedReferences
                            extras.update({'tokenstore': secrets_issuer.get_secret(plugin)})
                            self.logger.debug(f'Issued TokenStore to {toload_cog}')
                            break

                    # Generate SecureStorageWrapper if needed
                    for plugin in requires_storage.keys():
                        if toload_cog in requires_storage[plugin]:
                            # noinspection PyUnresolvedReferences
                            extras.update({'storage': secrets_issuer.get_storage(plugin)})
                            self.logger.debug(f'Issued SecureStorage to {toload_cog}')
                            break

                    try:
                        self.bot.reload_extension(toload_cog, extras=extras)
                    except nextcord.ext.commands.errors.InvalidSetupArguments:
                        # assume cog does not use extras kwargs
                        self.bot.reload_extension(toload_cog)
                elif action == CogAction.unload:
                    self.bot.unload_extension(toload_cog)
                success.append(toload_cog)
            except:
                e = traceback.format_exc()
                failed.update({toload_cog: e})
        return len(toload), success, failed

    async def manage_cog_cmd(self, ctx: Union[commands.Context, nextcord.Interaction], action: CogAction, cogs: str):
        if type(ctx) is commands.Context:
            selector = language.get_selector('sysmgr.manage_cog', userid=ctx.author.id)
            author = ctx.author
        else:
            selector = language.get_selector('sysmgr.manage_cog', userid=ctx.user.id)
            author = ctx.user

        if self.bot.update:
            return await ctx.send(selector.get('disabled'))

        cogs = cogs.split(' ')

        if action == CogAction.load:
            action_str = 'load'
        elif action == CogAction.reload:
            action_str = 'reload'
        elif action == CogAction.unload:
            action_str = 'unload'
        else:
            # default to load
            action_str = 'load'

        msg = await ctx.send(f'{self.bot.ui_emojis.loading} {selector.get(action_str)}')
        if type(ctx) is nextcord.Interaction:
            msg = await msg.fetch()

        total, success, failed = await self.manage_cog(cogs, action)

        components = ui.MessageComponents()
        if failed:
            selection = nextcord.ui.StringSelect(
                placeholder=selector.get("viewerror"),
                max_values=1,
                min_values=1,
                custom_id='selection'
            )

            for fail in failed.keys():
                selection.add_option(
                    label=fail,
                    value=fail
                )

            components.add_row(
                ui.ActionRow(selection)
            )

        touse_emoji = self.bot.ui_emojis.success if len(success) == total else self.bot.ui_emojis.warning

        if len(success) > 0 and not action == CogAction.unload:
            await self.bot.discover_application_commands()
            await self.bot.register_new_application_commands()

        await msg.edit(
            content=f'{touse_emoji} {selector.fget("completed", values={"total":total, "success": len(success)})}',
            view=components
        )

        if not failed:
            return

        while True:
            def check(interaction):
                if not interaction.message:
                    return

                return interaction.message.id == msg.id and interaction.user.id == author.id

            try:
                interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
            except asyncio.TimeoutError:
                return await msg.edit(view=None)

            selected = interaction.data['values'][0]
            error = failed[selected]
            await interaction.response.send_message(
                f'{self.bot.ui_emojis.error} {selected}\n```\n{error}```', ephemeral=True
            )

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
            tasks = [self.bot.loop.create_task(self.bot.bridge.backup())]
            await asyncio.wait(tasks)
        except:
            self.logger.exception('Backup failed')

    @tasks.loop()
    async def periodic_backup_cloud(self):
        if not self.bot.ready:
            return
        endpoint = 'https://' + self.bot.config['cloud_backup_endpoint']
        __apikey = self.bot.tokenstore.retrieve('CLOUD_BACKUP_API_KEY')
        __headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {__apikey}"
        }
        try:
            __salt = self.bot.config['cloud_backup_salt']
            __pass = self.bot.tokenstore.retrieve('CLOUD_BACKUP_PASSWORD')
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

    @nextcord.slash_command(
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def system(self, ctx):
        pass

    @commands.group(name='system')
    async def system_legacy(self, ctx):
        pass

    @system_legacy.command(aliases=['reload-services'], description=language.desc('sysmgr.reload_services'))
    @restrictions_legacy.owner()
    async def reload_services(self,ctx,*,services=None):
        selector = language.get_selector(ctx)
        if not services:
            plugins = self.bot.loaded_plugins
        else:
            plugins = services.split(' ')
        success = []
        failed = []
        errors = []
        error_objs = []
        text = '```diff'
        msg = await ctx.send(selector.get('in_progress'))
        for plugin in plugins:
            try:
                importlib.reload(self.bot.loaded_plugins[plugin])
                success.append(plugin)
                text = text + f'\n+ [DONE] {plugin}'
            except Exception as error:
                e = traceback.format_exc()
                failed.append(plugin)
                errors.append(e)
                error_objs.append(error)
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
            if len(text) > 2000:
                for error in error_objs:
                    self.logger.exception('An error occurred!', exc_info=error)
                    return await ctx.author.send(selector.get("too_long"))
            await ctx.author.send(f'**{selector.get("fail_logs")}**\n{text}')

    # Eval command
    async def eval(self, ctx, body):
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
                await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"exec_time": exec_time})}\n```\n{value}\n```')

    # Shutdown command
    async def shutdown(self, ctx):
        await self.bot_shutdown(ctx)

    # Restart command
    async def restart(self, ctx):
        await self.bot_shutdown(ctx, restart=True)

    # Modifiers command
    async def modifiers(self, ctx: Union[nextcord.Interaction, commands.Context]):
        selector = language.get_selector(ctx)
        page = 0
        pluglist = [plugin for plugin in os.listdir('plugins') if plugin.endswith('.json')]
        offset = page * 20
        embed = nextcord.Embed(title=selector.get('title'), color=self.bot.colors.unifier)
        if offset > len(pluglist):
            page = len(pluglist) // 20 - 1
            offset = page * 20
        for x in range(offset, 20 + offset):
            if x == len(pluglist):
                break
            with open('plugins/'+pluglist[x]) as file:
                pluginfo = json.load(file)
            embed.add_field(
                name=f'{pluginfo["name"]} (`{pluginfo["id"]}`, {pluginfo["version"]})',
                value=pluginfo["description"],
                inline=False
            )
        embed.set_footer(text=selector.rawfget(
            'page', 'sysmgr.extensions', values={'page': page + 1}
        ))
        return await ctx.send(embed=embed)

    @system_legacy.command(aliases=['cogs'], description=language.desc('sysmgr.extensions'))
    @restrictions_legacy.owner()
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
                    text = f'- {selector.rawget("name", ext.replace("cogs.","",1)+".cogmeta",default="") or cog.qualified_name} (`{ext}`)'
                else:
                    text = f'{text}\n- {selector.rawget("name", ext.replace("cogs.","",1)+".cogmeta",default="") or cog.qualified_name} (`{ext}`)'
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

    # Reload command
    async def reload(self, ctx, extensions):
        await self.manage_cog_cmd(ctx, CogAction.reload, extensions)

    @system_legacy.command(description=language.desc('sysmgr.load'))
    @restrictions_legacy.owner()
    async def load(self, ctx, *, extensions):
        await self.manage_cog_cmd(ctx, CogAction.load, extensions)

    @system_legacy.command(description='Unloads an extension.')
    @restrictions_legacy.owner()
    async def unload(self, ctx, *, extensions):
        await self.manage_cog_cmd(ctx, CogAction.unload, extensions)

    @system_legacy.command(description='Installs a plugin.')
    @restrictions_legacy.owner()
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
            filters = new.get('filters', [])
            services = new.get('services', [])
            nups_platform = new.get('bridge_platform')
            if nups_platform == '':
                nups_platform = None

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
            for filt in filters:
                if filt in os.listdir('filters'):
                    conflicts.append('filters/'+filt)
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
            if not interaction.message:
                return False
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
                                os.system(f'{binary} -m pip install{self.pip_user_arg} --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                            ))
                        else:
                            binary = bootloader_config.get('binary', 'python3')
                            await self.bot.loop.run_in_executor(None, lambda: status(
                                os.system(f'{binary} -m pip install{self.pip_user_arg} --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                            ))
            except:
                self.logger.exception('Dependency installation failed')
                raise RuntimeError()
            self.logger.info('Installing Modifier')
            for module in modules:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+module)
                await self.copy('plugin_install/' + module, 'cogs/' + module)
            for util in utilities:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+util)
                await self.copy('plugin_install/' + util, 'utils/' + util)
            for filt in filters:
                self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/'+filt)
                await self.copy('plugin_install/' + filt, 'filters/' + filt)
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
            if not 'bridge_platform' in services:
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

            if 'bridge_platform' in services:
                embed.description = embed.description + '\n' + selector.get("restart_body")

            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Install failed')
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("postfail_title")}'
            embed.description = selector.get("postfail_body")
            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            return

    @system_legacy.command(description='Uninstalls a plugin.')
    @restrictions_legacy.owner()
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
            if not interaction.message:
                return False
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
            filters = plugin_info.get('filters', [])
            self.logger.info('Uninstalling Plugin')
            for module in modules:
                self.logger.debug('Uninstalling: ' + os.getcwd() + '/cogs/' + module)
                os.remove('cogs/'+module)
            for util in utilities:
                self.logger.debug('Uninstalling: ' + os.getcwd() + '/utils/' + util)
                os.remove('utils/'+util)
            for filt in filters:
                self.logger.debug('Uninstalling: ' + os.getcwd() + '/filters/' + filt)
                os.remove('filters/'+filt)
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

    # Upgrade command
    async def upgrade(self, ctx, plugin='system', args=''):
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

            with open('boot/internal.json') as file:
                bootdata = json.load(file)

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

                if not bootdata['stable_branch'] == self.bot.config['branch']:
                    embed.description += '\n\n' + self.bot.ui_emojis.warning + ' ' + selector.fget(
                        'unstable', values={'branch': self.bot.config['branch']}
                    )

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
                        style=nextcord.ButtonStyle.gray, label=selector.rawget('nevermind','commons.navigation'), custom_id=f'reject',
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
                    if not interaction.message:
                        return False
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
                            os.system(f'{binary} -m pip install{self.pip_user_arg} -U ' + '"' + '" "'.join(newdeps) + '"')
                        ))
                    else:
                        binary = bootloader_config.get('binary', 'python3')
                        await self.bot.loop.run_in_executor(None, lambda: status(
                            os.system(f'{binary} -m pip install{self.pip_user_arg} -U ' + '"' + '" "'.join(newdeps) + '"')
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
                for file in os.listdir(os.getcwd() + '/update/filters'):
                    self.logger.debug('Installing: ' + os.getcwd() + '/update/filters/' + file)
                    await self.copy('update/filters/' + file, 'filters/' + file)
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
                    oldcfg = tomllib.load(file)
                with open('update/config.toml', 'rb') as file:
                    newcfg = tomllib.load(file)

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
                            await self.manage_cog(cog, CogAction.reload)
                        except:
                            self.logger.warning(cog+' could not be reloaded.')
                            embed.set_footer(text=f':warning: {selector.get("reload_warning")}')
                    self.logger.info('Updating localization')
                    self.bot.langmgr.load()
                    await self.bot.discover_application_commands()
                    await self.bot.register_new_application_commands()
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
                services = new.get('services', [])
                filters = new.get('filters', [])
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
                if not interaction.message:
                    return False
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
                                    os.system(f'{binary} -m pip install{self.pip_user_arg} --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
                                ))
                            else:
                                binary = bootloader_config.get('binary', 'python3')
                                await self.bot.loop.run_in_executor(None, lambda: status(
                                    os.system(f'{binary} -m pip install{self.pip_user_arg} --no-dependencies -U ' + '"' + '" "'.join(newdeps) + '"')
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
                for filt in filters:
                    self.logger.debug('Installing: ' + os.getcwd() + '/plugin_install/' + filt)
                    await self.copy('plugin_install/' + filt, 'filters/' + filt)
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
                            oldcfg = tomllib.load(file)
                        with open('plugin_install/config.toml', 'rb') as file:
                            newcfg = tomllib.load(file)

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
                            await self.manage_cog(modname, CogAction.reload)
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

    @system_legacy.command(
        description='Activates an emoji pack. Activating the "base" emoji pack resets emojis back to vanilla.',
        aliases=['emojipack']
    )
    @restrictions_legacy.owner()
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

    # Help command
    async def help(self, ctx: Union[nextcord.Interaction, commands.Context], query: Optional[str] = None):
        selector = language.get_selector(ctx)
        is_legacy = type(ctx) is commands.Context
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
        if ctx.user.id in self.bot.moderators:
            permissions = 'mod'
        if ctx.user.id in self.bot.admins:
            permissions = 'admin'
        if ctx.user.id == self.bot.config['owner']:
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
                if cogname=='' or cogname=='search':
                    cmds = await self.bot.loop.run_in_executor(None, lambda: self.get_all_commands())
                else:
                    query_cog = None
                    cmds = []
                    for x in range(len(self.bot.extensions)):
                        if list(self.bot.extensions)[x]==cogname:
                            query_cog = self.bot.cogs[list(self.bot.cogs)[x]]
                            break

                    if not query_cog is None:
                        cmds = await self.bot.loop.run_in_executor(None, lambda: self.get_all_commands(cog=query_cog))

                universal_cmds, ignore_cmds = await self.bot.loop.run_in_executor(
                    None, lambda: self.get_universal_commands(cmds, legacy=is_legacy)
                )
                for cmd in ignore_cmds:
                    cmds.remove(cmd)

                legacy_mapped = {}
                for cmd in ignore_cmds:
                    legacy_mapped.update({cmd.qualified_name: cmd})

                universal_names = []
                for cmd in universal_cmds:
                    universal_names.append(cmd.qualified_name)

                offset = 0

                def in_aliases(query, query_cmd):
                    if (
                            isinstance(query_cmd, nextcord.BaseApplicationCommand) or
                            isinstance(query_cmd, nextcord.SlashApplicationSubcommand)
                    ):
                        # slash commands cannot have aliases
                        return False

                    for alias in query_cmd.aliases:
                        if query.lower() in alias.lower():
                            return True

                def search_filter(query, query_cmd):
                    has_alias = False
                    if not is_legacy:
                        alias_command = legacy_mapped.get(query_cmd.qualified_name)
                        command_aliases = []

                        if alias_command:
                            if alias_command.aliases:
                                for alias in alias_command.aliases:
                                    parent_name = ''
                                    if alias_command.parent:
                                        parent_name = alias_command.parent.qualified_name + ' '
                                    command_aliases.append(f'{parent_name}{alias}')

                        for found_alias in command_aliases:
                            if query.lower() in found_alias.lower():
                                has_alias = True
                                break

                    if match==0:
                        return (
                            (
                                query.lower() in query_cmd.qualified_name.lower() or
                                in_aliases(query,query_cmd) or
                                has_alias
                            ) and namematch or query.lower() in query_cmd.description.lower() and descmatch
                        )
                    elif match==1:
                        return (((
                            (
                                query.lower() in query_cmd.qualified_name.lower() or
                                in_aliases(query,query_cmd) or
                                has_alias
                            ) and namematch) or not namematch) and
                            ((query.lower() in query_cmd.description.lower() and descmatch) or not descmatch)
                        )

                for index in range(len(cmds)):
                    cmd = cmds[index-offset]
                    hidden = False
                    if permissions=='owner':
                        canrun = True
                    else:
                        try:
                            if (
                                    isinstance(cmd, nextcord.BaseApplicationCommand) or
                                    isinstance(cmd, nextcord.SlashApplicationSubcommand)
                            ) and not is_legacy or type(cmd) is commands.Command and is_legacy:
                                canrun = await cmd.can_run(ctx)
                            else:
                                canrun = (
                                        ctx.user.id == self.bot.owner or
                                        ctx.user.id in self.bot.other_owners or
                                        ctx.user.id in self.bot.admins
                                ) # legacy commands can only be used by owners and admins
                        except:
                            canrun = False or cmd.qualified_name in overrides[permissions]

                    if type(cmd) is commands.Command:
                        hidden = cmd.hidden

                    if not canrun or (cogname=='search' and not search_filter(query,cmd)) or hidden:
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
                                selector.rawget('description', f'{cogname.replace("cogs.", "", 1)}.{cmd.qualified_name}', default='')
                                or
                                selector.desc_from_all(cmd.qualified_name)
                                or
                                cmd.description or selector.get("no_desc")
                        )

                        if type(cmd) is commands.Command:
                            cmdtext = f'`{cmd.qualified_name}`'
                        else:
                            cmdtext = cmd.get_mention()

                        if cmd.qualified_name in universal_names:
                            if type(cmd) is commands.Command:
                                cmdtext = legacy_mapped[cmd.qualified_name].get_mention()

                            cmdtext = cmdtext + ' :sparkles:'
                        else:
                            cmdtext = f'{cmdtext}'

                        embed.add_field(
                            name=cmdtext,
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
                cmds = await self.bot.loop.run_in_executor(None, lambda: self.get_all_commands())
                possible_cmds = [cmd for cmd in cmds if cmd.qualified_name == cmdname]
                cmd = possible_cmds[0]
                localized_cogname = selector.get("search_nav") if cogname == 'search' else cogname
                embed.title = (
                    f'{self.bot.ui_emojis.command} {helptext} / {localized_cogname} / {cmdname}' if not cogname=='' else
                    f'{self.bot.ui_emojis.command} {helptext} / {selector.get("all")} / {cmdname}'
                )

                slash_form = None
                legacy_form = None
                for possibility in possible_cmds:
                    if isinstance(possibility, nextcord.BaseApplicationCommand) or isinstance(possibility, nextcord.SlashApplicationSubcommand):
                        slash_form = possibility
                        cmd = possibility
                    else:
                        legacy_form = possibility

                is_universal = slash_form and legacy_form

                try:
                    cmddesc = selector.desc_from_all(cmd.qualified_name) or cmd.description or selector.get("no_desc")
                except:
                    cmddesc = cmd.description or selector.get("no_desc")

                aliases = []
                if legacy_form:
                    parent_command = ''
                    if legacy_form.parent:
                        parent_command = legacy_form.parent.qualified_name + ' '

                    for alias in legacy_form.aliases:
                        aliases.append(f'`{self.bot.command_prefix}{parent_command}{alias}`')

                slash_signature = ''
                if slash_form:
                    options = slash_form.options
                    options_text = []

                    for option, option_obj in options.items():
                        option_type = option_types.get(option_obj.payload['type'], 'string')

                        if option_obj.payload.get('required', False):
                            options_text.append(f'<{option_obj.name}: {option_type}>')
                        else:
                            options_text.append(f'[{option_obj.name}: {option_type}]')

                    options_text_final = ''
                    if len(options_text) > 0:
                        options_text_final = ' ' + ' '.join(options_text)

                    slash_signature = f'`/{slash_form.qualified_name}{options_text_final}`'

                if is_universal:
                    cmddesc = cmddesc + '\n\n:sparkles: ' + selector.get("universal")
                    cmdtext = slash_form.get_mention()

                    if len(aliases) > 0:
                        embed.add_field(
                            name=selector.get("aliases_universal"),
                            value=('- ' + '\n- '.join(aliases)) if len(aliases) > 1 else ('- ' + aliases[0]),
                            inline=False
                        )

                    embed.add_field(
                        name=selector.get("usage"),
                        value=(
                            '- ' + selector.fget("usage_slash_universal", values={"command": slash_signature}) + '\n' +
                            '- ' + selector.fget("usage_legacy_universal", values={"signature": (
                                f'`{self.bot.command_prefix}{cmdname} {legacy_form.signature}`'
                                if len(legacy_form.signature) > 0 else
                                f'`{self.bot.command_prefix}{cmdname}`'
                            )})
                        ),
                        inline=False
                    )
                elif isinstance(cmd, nextcord.BaseApplicationCommand) or isinstance(cmd, nextcord.SlashApplicationSubcommand):
                    cmdtext = cmd.get_mention()
                    embed.add_field(
                        name=selector.get("usage"),
                        value='- '+selector.fget("usage_slash_universal", values={"command": slash_signature}),
                        inline=False
                    )
                elif isinstance(cmd, commands.Command):
                    cmdtext = f'**`{self.bot.command_prefix}{cmdname}`**'
                    if len(aliases) > 0:
                        embed.add_field(
                            name=selector.get("aliases"),
                            value=('- ' + '\n- '.join(aliases)) if len(aliases) > 1 else ('- ' + aliases[0]),
                            inline=False
                        )
                    embed.add_field(name=selector.get("usage"), value='- '+selector.fget(
                        "usage_legacy_universal", values={"signature": (
                            f'`{self.bot.command_prefix}{cmdname} {cmd.signature}`' if len(cmd.signature) > 0 else
                            f'`{self.bot.command_prefix}{cmdname}`'
                        )}
                    ), inline=False)
                else:
                    cmdtext = f'**`{self.bot.command_prefix}{cmdname}`**'

                embed.description = f'# {cmdtext}\n{cmddesc}'
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
                msg = await ctx.send(embed=embed,view=components)
                if type(ctx) is nextcord.Interaction:
                    msg = await msg.fetch()
            else:
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed,view=components)
            embed.clear_fields()

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id==ctx.user.id and interaction.message.id==msg.id

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

    # Custom prefix command
    async def custom_prefix(self, ctx: Union[nextcord.Interaction, commands.Context], prefix: Optional[str] = None):
        selector = language.get_selector(ctx)
        if not prefix:
            user_prefix = self.bot.db['bot_prefixes'].get(ctx.user.id)
            guild_prefix = self.bot.db['bot_prefixes'].get(ctx.guild.id)

            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.command} {selector.get("title")}',
                description=selector.get("body"),
                color=self.bot.colors.unifier
            )
            embed.add_field(name=selector.get("global"), value=f'`{self.bot.command_prefix}`', inline=False)
            if ctx.guild:
                embed.add_field(
                    name=selector.get("server"), value=f'`{guild_prefix}`' if guild_prefix else selector.get("none"),
                    inline=False
                )
            embed.add_field(
                name=selector.get("user"), value=f'`{user_prefix}`' if user_prefix else selector.get("none"),
                inline=False
            )

            return await ctx.send(embed=embed)
        else:
            if len(prefix) > 10:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("too_long")}')

            change_guild_prefix = False

            # Check if user is admin (has manage channels perms)
            can_change_guild = False
            if ctx.guild:
                can_change_guild = ctx.user.guild_permissions.manage_channels

            interaction: Optional[nextcord.Interaction] = None

            # Ask user which one to modify
            if can_change_guild:
                components = ui.MessageComponents()
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.get("choice_server"),
                            custom_id='server'
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.get("choice_user"),
                            custom_id='user'
                        )
                    )
                )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("cancel","commons.navigation"),
                            custom_id='cancel'
                        )
                    )
                )
                msg = await ctx.send(f'{self.bot.ui_emojis.warning} {selector.get("choose")}', view=components)
                if type(ctx) is nextcord.Interaction:
                    msg = await msg.fetch()

                def check(interaction):
                    if not interaction.message:
                        return False
                    return interaction.user.id == ctx.user.id and interaction.message.id == msg.id

                try:
                    interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
                except asyncio.TimeoutError:
                    return await msg.edit(view=None)

                if interaction.data['custom_id'] == 'cancel':
                    return await interaction.response.edit_message(view=None)

                change_guild_prefix = interaction.data['custom_id'] == 'server'

            target = ctx.guild.id if change_guild_prefix else ctx.user.id

            if prefix.lower() == self.bot.command_prefix:
                self.bot.db['bot_prefixes'].pop(str(target), None)
                response = selector.get('reset')
            else:
                self.bot.db['bot_prefixes'].update({str(target): prefix})
                response = selector.get('success')

            response = f'{self.bot.ui_emojis.success} {response}'

            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

            if interaction:
                await interaction.response.edit_message(content=response, view=None)
            else:
                await ctx.send(response)

    @system_legacy.command(name='register-commands', description='Registers commands.')
    @restrictions_legacy.owner()
    async def register_commands(self, ctx, *, args=''):
        selector = language.get_selector(ctx)
        if 'dereg' in args:
            await self.bot.delete_application_commands(*self.bot.get_all_application_commands())
            return await ctx.send(selector.get("atoms"))
        await self.bot.sync_application_commands()
        return await ctx.send(selector.get("registered"))

    @system_legacy.command(description='Views cloud backup status.')
    @restrictions_legacy.owner()
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
            if not interaction.message:
                return False
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

    async def uptime(self, ctx: Union[nextcord.Interaction, commands.Context]):
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

    # About command
    async def about(self, ctx: Union[nextcord.Interaction, commands.Context]):
        selector = language.get_selector(ctx)

        all_attribs = dict(attribution)

        for plugin in os.listdir('plugins'):
            if not plugin.endswith('.json') or plugin == 'system.json':
                continue
            with open(f'plugins/{plugin}') as file:
                plugin_info = json.load(file)
            all_attribs.update(plugin_info.get('attribution', {}))

        attr_limit = 10
        page = 0
        maxpage = math.ceil(len(all_attribs.keys())/attr_limit)-1
        show_attr = False
        interaction = None
        msg = None

        try:
            with open('plugins/system.json') as file:
                vinfo = json.load(file)
        except:
            vinfo = None

        try:
            with open('boot/internal.json') as file:
                pinfo = json.load(file)
        except:
            pinfo = {}

        if vinfo:
            footer_text = "Version " + vinfo['version'] + " | Made with \u2764\ufe0f by UnifierHQ"
        else:
            footer_text = "Unknown version | Made with \u2764\ufe0f by UnifierHQ"

        footer_text += f'\nUsing Nextcord {nextcord.__version__} on Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'

        while True:
            embed = nextcord.Embed(
                title=self.bot.user.global_name or self.bot.user.name,
                description=(
                    (self.bot.config["custom_slogan"] or "Powered by Unifier") + '\n\n' +
                    selector.fget("team", values={
                        "product": pinfo.get("product_name",'unknown'),
                        "maintainer": pinfo.get("maintainer",'unknown'),
                        "url": pinfo.get("maintainer_profile",'unknown')
                    })
                ),
                color=self.bot.colors.unifier
            )
            embed.set_footer(text=footer_text)

            terms_hyperlink = f'[{selector.get("terms")}]({self.bot.config["terms_url"]})'
            if not self.bot.config["terms_url"]:
                terms_hyperlink = selector.get("terms") + ' (' + selector.get("missing") + ')'

            privacy_hyperlink = f'[{selector.get("privacy")}]({self.bot.config["privacy_url"]})'
            if not self.bot.config["privacy_url"]:
                privacy_hyperlink = selector.get("privacy") + ' (' + selector.get("missing") + ')'

            guidelines_hyperlink = f'[{selector.get("guidelines")}]({self.bot.config["guidelines_url"]})'
            if not self.bot.config["guidelines_url"]:
                guidelines_hyperlink = selector.get("guidelines") + ' (' + selector.get("missing") + ')'

            if not show_attr:
                embed.add_field(name=selector.get("source_code"), value=self.bot.config['repo'], inline=False)
                embed.add_field(name=selector.get("legal"), value=f'{terms_hyperlink}\n{privacy_hyperlink}\n{guidelines_hyperlink}',inline=False)
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
                    if type(ctx) is nextcord.Interaction:
                        msg = await msg.fetch()
                else:
                    await interaction.response.edit_message(embed=embed, view=view)
            else:
                embed.clear_fields()

                for index in range(
                        page*attr_limit,
                        (page+1)*attr_limit if (page+1)*attr_limit < len(all_attribs.keys()) else len(all_attribs.keys())
                ):
                    attr_data = all_attribs[list(all_attribs.keys())[index]]
                    embed.add_field(
                        name=f'{list(all_attribs.keys())[index]} by {attr_data["author"]}',
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
                embed.set_footer(text=selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1})+' | '+footer_text)
                await interaction.response.edit_message(embed=embed, view=view)

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id == ctx.user.id and interaction.message.id == msg.id

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

    # Universal commands handlers and autocompletes

    # system modifiers
    @system.subcommand(
        name='modifiers',
        description=language.desc('sysmgr.modifiers'),
        description_localizations=language.slash_desc('sysmgr.modifiers')
    )
    async def modifiers_slash(self, ctx: nextcord.Interaction):
        await self.modifiers(ctx)

    @system_legacy.command(name='modifiers')
    async def modifiers_legacy(self, ctx: commands.Context):
        await self.modifiers(ctx)

    # help
    @nextcord.slash_command(
        name='help',
        description=language.desc('sysmgr.help'),
        description_localizations=language.slash_desc('sysmgr.help'),
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def help_slash(
            self, ctx: nextcord.Interaction,
            query: str = slash.option('sysmgr.help.query', required=False)
    ):
        await self.help(ctx, query=query)

    @help_slash.on_autocomplete("query")
    async def help_autocomplete(self, ctx: nextcord.Interaction, query: str):
        cmds = await self.bot.loop.run_in_executor(None, lambda: self.get_all_commands())
        universal_cmds, ignore_cmds = await self.bot.loop.run_in_executor(
            None, lambda: self.get_universal_commands(cmds)
        )

        for cmd in ignore_cmds:
            cmds.remove(cmd)

        legacy_mapped = {}
        for cmd in ignore_cmds:
            legacy_mapped.update({cmd.qualified_name: cmd})

        overrides = {
            'admin': [],
            'mod': [],
            'user': ['modping']
        }

        overrides['mod'] += overrides['user']
        overrides['admin'] += overrides['mod']

        permissions = 'user'
        if ctx.user.id in self.bot.moderators:
            permissions = 'mod'
        elif ctx.user.id in self.bot.admins:
            permissions = 'admin'
        elif ctx.user.id == self.bot.config['owner']:
            permissions = 'owner'

        possible = []
        for cmd in cmds:
            alias_command = legacy_mapped.get(cmd.qualified_name)
            command_aliases = []

            if alias_command:
                if alias_command.aliases:
                    for alias in alias_command.aliases:
                        parent_name = ''
                        if alias_command.parent:
                            parent_name = alias_command.parent.qualified_name + ' '
                        command_aliases.append(f'{parent_name}{alias}')

            has_alias = False
            for found_alias in command_aliases:
                if query.lower() in found_alias.lower():
                    has_alias = True
                    break

            if query.lower() in cmd.qualified_name or has_alias:
                try:
                    if isinstance(cmd, nextcord.BaseApplicationCommand) or isinstance(cmd, nextcord.SlashApplicationSubcommand):
                        canrun = await cmd.can_run(ctx)
                    else:
                        canrun = (
                                ctx.user.id == self.bot.owner or
                                ctx.user.id in self.bot.other_owners or
                                ctx.user.id in self.bot.admins
                        )  # legacy commands can only be used by owners and admins
                except:
                    canrun = False or cmd.qualified_name in overrides[permissions]

                if type(cmd) is commands.Command and cmd.hidden:
                    continue

                if canrun:
                    if not cmd.qualified_name in possible:
                        possible.append(cmd.qualified_name)

        return await ctx.response.send_autocomplete(possible[:25])

    @commands.command(name='help')
    async def help_legacy(self, ctx: commands.Context, *, query=None):
        await self.help(ctx, query)

    # custom-prefix
    @nextcord.slash_command(
        name='custom-prefix',
        description=language.desc('sysmgr.custom-prefix'),
        description_localizations=language.slash_desc('sysmgr.custom-prefix'),
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def custom_prefix_slash(
            self, ctx: nextcord.Interaction,
            prefix: str = slash.option('sysmgr.custom-prefix.prefix', required=False)
    ):
        await self.custom_prefix(ctx, prefix=prefix)

    @commands.command(name='custom-prefix')
    async def custom_prefix_legacy(self, ctx: commands.Context, prefix: Optional[str] = None):
        await self.custom_prefix(ctx, prefix=prefix)

    # about
    @nextcord.slash_command(
        name='about',
        description=language.desc('sysmgr.about'),
        description_localizations=language.slash_desc('sysmgr.about'),
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def about_slash(self, ctx: nextcord.Interaction):
        await self.about(ctx)

    @commands.command(name='about')
    async def about_legacy(self, ctx: commands.Context):
        await self.about(ctx)

    # system uptime
    @system.subcommand(
        name='uptime',
        description=language.desc('sysmgr.uptime'),
        description_localizations=language.slash_desc('sysmgr.uptime')
    )
    async def uptime_slash(self, ctx: nextcord.Interaction):
        await self.uptime(ctx)

    @system_legacy.command(name='uptime')
    async def uptime_legacy(self, ctx: commands.Context):
        await self.uptime(ctx)

    # system upgrade
    @system_legacy.command(name='upgrade', description='Upgrades Unifier or a plugin.')
    @restrictions_legacy.owner()
    async def upgrade_legacy(self, ctx, plugin='system', *, args=''):
        await self.upgrade(ctx, plugin=plugin, args=args)

    @commands.command(name='upgrade', description='Upgrades Unifier or a plugin.', hidden=True)
    @restrictions_legacy.owner()
    async def upgrade_legacy_alt(self, ctx, plugin='system', *, args=''):
        await self.upgrade(ctx, plugin=plugin, args=args)

    # system shutdown
    @system_legacy.command(name='shutdown', aliases=['poweroff'], description=language.desc('sysmgr.shutdown'))
    @restrictions_legacy.owner()
    async def shutdown_legacy(self, ctx):
        await self.shutdown(ctx)

    @commands.command(name='shutdown', aliases=['poweroff'], description=language.desc('sysmgr.shutdown'), hidden=True)
    async def shutdown_legacy_alt(self, ctx):
        await self.shutdown(ctx)

    # system restart
    @system_legacy.command(name='restart', aliases=['reboot'], description=language.desc('sysmgr.restart'))
    @restrictions_legacy.owner()
    async def restart_legacy(self, ctx):
        await self.restart(ctx)

    @commands.command(name='restart', aliases=['reboot'], description=language.desc('sysmgr.restart'), hidden=True)
    @restrictions_legacy.owner()
    async def restart_legacy_alt(self, ctx):
        await self.restart(ctx)

    # system reload
    @system_legacy.command(name='reload', description=language.desc('sysmgr.reload'))
    @restrictions_legacy.owner()
    async def reload_legacy(self, ctx, *, extensions):
        await self.reload(ctx, extensions)

    @commands.command(name='reload', description=language.desc('sysmgr.reload'), hidden=True)
    @restrictions_legacy.owner()
    async def reload_legacy_alt(self, ctx, *, extensions):
        await self.reload(ctx, extensions)

    # system eval
    @system_legacy.command(name='eval', description=language.desc('sysmgr.eval'))
    @restrictions_legacy.owner()
    async def eval_legacy(self, ctx, *, body):
        await self.eval(ctx, body)

    @commands.command(name='eval', description=language.desc('sysmgr.eval'), hidden=True)
    @restrictions_legacy.owner()
    async def eval_legacy_alt(self, ctx, *, body):
        await self.eval(ctx, body)

    # Error handling

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

    @commands.Cog.listener()
    async def on_application_command_error(
            self, interaction: nextcord.Interaction, exception: nextcord.ApplicationError
    ) -> None:
        await self.bot.exhandler.handle(interaction, exception)

def setup(bot, issuer):
    global secrets_issuer
    secrets_issuer = issuer
    bot.add_cog(SysManager(bot))
