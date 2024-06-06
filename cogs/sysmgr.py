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

# WARNING: EDITING THIS FILE MAY BE DANGEROUS!!!
#
# System Manager (sysmgr.py) contains certain admin commands, which if
# used maliciously, may damage your Unifier instance, or even your
# system! These commands are only to be used by the instance owner, and
# NOT anyone else.
#
# We can't stop you from modifying this file (it's licensed under the
# AGPLv3 license anyway), but we still STRONGLY recommend you DO NOT
# modify this, unless you're ABSOLUTELY SURE of what you're doing.

import nextcord
from nextcord.ext import commands
import inspect
import textwrap
from contextlib import redirect_stdout
from utils import log, ui
import logging
import ujson as json
import os
import sys
import traceback
import io
import base64
import re
import ast
import importlib
import math
import asyncio
import discord_emoji

class Colors: # format: 0xHEXCODE
    greens_hair = 0xa19e78
    unifier = 0xed4545
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    purple = 0x9b59b6
    red = 0xe74c3c
    blurple = 0x7289da
    gold = 0xd4a62a

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

class SysManager(commands.Cog, name=':wrench: System Manager'):
    """An extension that oversees a lot of the bot system.

    Developed by Green"""

    class SysExtensionLoadFailed(Exception):
        pass

    def __init__(self, bot):
        self.bot = bot

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

        self.logger = log.buildlogger(self.bot.package, 'sysmgr', self.bot.loglevel)
        if not hasattr(self.bot,'loaded_plugins'):
            self.bot.loaded_plugins = {}
            if not self.bot.safemode:
                for plugin in os.listdir('plugins'):
                    with open('plugins/' + plugin) as file:
                        extinfo = json.load(file)
                        try:
                            if not 'content_protection' in extinfo['services']:
                                continue
                        except:
                            continue
                    script = importlib.import_module('utils.' + plugin[:-5] + '_content_protection')
                    self.bot.loaded_plugins.update({plugin[:-5]: script})

        if not self.bot.ready:
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
            self.bot.ready = True

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

    @commands.command(aliases=['reload-services'], hidden=True, description="Reloads bot services.")
    async def reload_services(self,ctx,*,services=None):
        if not services:
            plugins = self.bot.loaded_plugins
        else:
            plugins = services.split(' ')
        success = []
        failed = []
        errors = []
        text = '```diff'
        msg = await ctx.send('Reloading services...')
        for plugin in plugins:
            try:
                importlib.reload(self.bot.loaded_plugins[plugin])
                success.append(plugin)
                text = text + f'\n+ [DONE] {plugin}'
            except Exception as e:
                failed.append(plugin)
                errors.append(e)
                text = text + f'\n- [FAIL] {plugin}'
        await msg.edit(
            content=f'Reload completed (`{len(plugins) - len(failed)}'f'/{len(plugins)}` successful)\n\n{text}```'
        )
        text = ''
        index = 0
        for fail in failed:
            if len(text) == 0:
                text = f'Extension `{fail}`\n```{errors[index]}```'
            else:
                text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
            index += 1
        if not len(failed) == 0:
            await ctx.author.send(f'**Fail logs**\n{text}')

    @commands.command(hidden=True,description='Evaluates code.')
    async def eval(self, ctx, *, body):
        if ctx.author.id == self.bot.config['owner']:
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
                await ctx.send('An error occurred while executing the code.', reference=ctx.message)
                await ctx.author.send(
                    f'```py\n{e.__class__.__name__}: {e}\n```\nIf this is a KeyError, it is most likely a SyntaxError.')
                return
            token_start = base64.b64encode(bytes(str(self.bot.user.id), 'utf-8')).decode('utf-8')
            try:
                with redirect_stdout(stdout):
                    # ret = await func() to return output
                    await func()
            except:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                await ctx.send('An error occurred while executing the code.', reference=ctx.message)
                if token_start in value:
                    return await ctx.author.send('The error contained your bot\'s token, so it was not sent.')
                await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                if token_start in value:
                    return await ctx.send('The output contained your bot\'s token, so it was not sent.')
                if value == '':
                    pass
                else:
                    #  here, cause is if haves value
                    await ctx.send('```%s```' % value)
        else:
            await ctx.send('Only the owner can execute code.')

    @eval.error
    async def eval_error(self, ctx, error):
        if ctx.author.id == self.bot.config['owner']:
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send('where code :thinking:')
            else:
                await ctx.send('Something went horribly wrong.')
                raise
        else:
            await ctx.send('Only the owner can execute code.')

    @commands.command(aliases=['stop', 'poweroff', 'kill'], hidden=True, description='Gracefully shuts the bot down.')
    async def shutdown(self, ctx):
        if not ctx.author.id == self.bot.config['owner']:
            return
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
            await ctx.send('Shutting down...')
        except:
            self.logger.exception("Graceful shutdown failed")
            await ctx.send('Shutdown failed')
            return
        self.logger.info("Closing bot session")
        await self.bot.session.close()
        self.logger.info("Shutdown complete")
        await self.bot.close()
        sys.exit(0)

    @commands.command(hidden=True,description='Lists all installed plugins.')
    async def plugins(self, ctx, *, plugin=None):
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
            embed = nextcord.Embed(title='Unifier Plugins', color=self.bot.colors.unifier)
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
            embed.set_footer(text="Page " + str(page + 1))
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
            return await ctx.send('Could not find extension!')
        embed = nextcord.Embed(
            title=pluginfo["name"],
            description=("Version " + pluginfo['version'] + ' (`' + str(pluginfo['release']) + '`)\n\n' +
                         pluginfo["description"]),
            color=self.bot.colors.unifier
        )
        if plugin == 'system':
            embed.description = embed.description + '\n# SYSTEM PLUGIN\nThis plugin cannot be uninstalled.'
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
        embed.add_field(name='Modules',value=modtext,inline=False)
        modtext = 'None'
        for module in pluginfo['utils']:
            if modtext == 'None':
                modtext = '- ' + module
            else:
                modtext = modtext + '\n- ' + module
        embed.add_field(name='Utilities', value=modtext, inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True, aliases=['cogs'], description='Lists all loaded extensions.')
    async def extensions(self, ctx, *, extension=None):
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
            embed = nextcord.Embed(title='Unifier Extensions', color=self.bot.colors.unifier)
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
            embed.set_footer(text="Page " + str(page + 1))
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
            return await ctx.send('Could not find extension!')
        embed = nextcord.Embed(
            title=ext_info.qualified_name,
            description=ext_info.description,
            color=self.bot.colors.unifier
        )
        if (extension == 'cogs.sysmgr' or extension == 'cogs.lockdown' or
                extension == 'sysmgr' or extension == 'lockdown'):
            embed.description = embed.description + '\n# SYSTEM MODULE\nThis module cannot be unloaded.'
        await ctx.send(embed=embed)

    @commands.command(hidden=True,description='Reloads an extension.')
    async def reload(self, ctx, *, extensions):
        if ctx.author.id == self.bot.config['owner']:
            if self.bot.update:
                return await ctx.send('Plugin management is disabled until restart.')

            extensions = extensions.split(' ')
            msg = await ctx.send('Reloading extensions...')
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
            await msg.edit(
                content=f'Reload completed (`{len(extensions) - len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text) == 0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed) == 0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('Only the owner can reload extensions.')

    @commands.command(hidden=True,description='Loads an extension.')
    async def load(self, ctx, *, extensions):
        if ctx.author.id == self.bot.config['owner']:
            if self.bot.update:
                return await ctx.send('Plugin management is disabled until restart.')

            extensions = extensions.split(' ')
            msg = await ctx.send('Loading extensions...')
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
            await msg.edit(
                content=f'Load completed (`{len(extensions) - len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text) == 0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed) == 0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('Only the owner can load extensions.')

    @commands.command(hidden=True,description='Unloads an extension.')
    async def unload(self, ctx, *, extensions):
        if ctx.author.id == self.bot.config['owner']:
            if self.bot.update:
                return await ctx.send('Plugin management is disabled until restart.')

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
            await msg.edit(
                content=f'Unload completed (`{len(extensions) - len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text) == 0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed) == 0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('Only the owner can unload extensions.')

    @commands.command(hidden=True,description='Installs a plugin.')
    async def install(self, ctx, url):
        if not ctx.author.id==self.bot.config['owner']:
            return

        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

        if url.endswith('/'):
            url = url[:-1]
        if not url.endswith('.git'):
            url = url + '.git'
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.install} Downloading extension...', description='Getting extension files from remote')
        embed.set_footer(text='Only install plugins from trusted sources!')
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/plugin_install')
            status(os.system(
                'git clone ' + url + ' ' + os.getcwd() + '/plugin_install'))
            with open('plugin_install/plugin.json', 'r') as file:
                new = json.load(file)
            if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                embed.title = f'{self.bot.ui_emojis.error} Invalid plugin.json file'
                embed.description = 'Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return
            if new['id']+'.json' in os.listdir('plugins'):
                with open('plugins/'+new['id']+'.json', 'r') as file:
                    current = json.load(file)
                embed.title = f'{self.bot.ui_emojis.error} Plugin already installed'
                embed.description = f'This plugin is already installed!\n\nName: `{current["name"]}`\nVersion: `{current["version"]}`'
                embed.colour = 0xff0000
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
                services = new['services']
            except:
                services = []

            with open('plugins/system.json', 'r') as file:
                vinfo = json.load(file)

            if vinfo['release'] < minimum:
                embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
                embed.description = f'Your Unifier does not support this plugin. Release `{minimum}` or later is required.'
                embed.colour = 0xff0000
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
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return
        except:
            embed.title = f'{self.bot.ui_emojis.error} Failed to install plugin'
            embed.description = 'The repository URL or the plugin.json file is invalid.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
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
                    embed.colour = 0xff0000
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
                        status(os.system('python3 -m pip install --no-dependencies ' + ' '.join(newdeps)))
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
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Install failed')
            embed.title = f'{self.bot.ui_emojis.error} Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Uninstalls a plugin.')
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
            embed.colour = 0xff0000
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
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Uninstall failed')
            embed.title = f'{self.bot.ui_emojis.error} Uninstallation failed'
            embed.description = 'The uninstallation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True,description='Upgrades Unifier or a plugin.')
    async def upgrade(self, ctx, plugin='system', *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return

        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

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
                title=f'{self.bot.ui_emojis.install} Checking for upgrades...',
                description='Getting latest version from remote'
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
                                )
                            ) or force
                    ):
                        available.append([legacy['version'], 'Legacy version', legacy['release'], index, legacy['reboot']])
                    index += 1
                update_available = len(available) >= 1
            except:
                embed.title = f'{self.bot.ui_emojis.error} Failed to check for updates'
                embed.description = 'Could not find a valid update.json file on remote'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                raise
            if not update_available:
                embed.title = f'{self.bot.ui_emojis.success} No updates available'
                embed.description = 'Unifier is up-to-date.'
                embed.colour = 0x00ff00
                return await msg.edit(embed=embed)
            selected = 0
            interaction = None
            while True:
                release = available[selected][2]
                version = available[selected][0]
                legacy = available[selected][3] > -1
                reboot = available[selected][4]
                embed.title = f'{self.bot.ui_emojis.install} Update available'
                embed.description = f'An update is available for Unifier!\n\nCurrent version: {current["version"]} (`{current["release"]}`)\nNew version: {version} (`{release}`)'
                embed.remove_footer()
                embed.colour = 0xffcc00
                if legacy:
                    should_reboot = reboot >= (current['legacy'] if 'legacy' in current.keys() and
                                               type(current['legacy']) is int else -1)
                else:
                    should_reboot = reboot >= current['release']
                if should_reboot:
                    embed.set_footer(text='The bot will need to reboot to apply the new update.')
                selection = nextcord.ui.StringSelect(
                    placeholder='Select version...',
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
                        style=nextcord.ButtonStyle.green, label='Upgrade', custom_id=f'accept',
                        disabled=False
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject',
                        disabled=False
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.link, label='More info',
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
                embed.title = f'{self.bot.ui_emojis.install} Backing up...'
                embed.description = 'Your data is being backed up.'
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
                    embed.description = '- :x: Your files have **NOT BEEN BACKED UP**! Data loss or system failures may occur if the upgrade fails!\n- :wrench: Any modifications you made to Unifier will be wiped, unless they are a part of the new upgrade.\n- :warning: Once started, you cannot abort the upgrade.'
                elif ignore_backup:
                    self.logger.warning('Backup failed, continuing anyways')
                    embed.description = '- :x: Your files **COULD NOT BE BACKED UP**! Data loss or system failures may occur if the upgrade fails!\n- :wrench: Any modifications you made to Unifier will be wiped, unless they are a part of the new upgrade.\n- :warning: Once started, you cannot abort the upgrade.'
                else:
                    self.logger.error('Backup failed, abort upgrade.')
                    embed.title = f'{self.bot.ui_emojis.error} Backup failed'
                    embed.description = 'Unifier could not create a backup. The upgrade has been aborted.'
                    embed.colour = 0xff0000
                    await msg.edit(embed=embed)
                    raise
            else:
                self.logger.info('Backup complete, requesting final confirmation.')
                embed.description = '- :inbox_tray: Your files have been backed up to `[Unifier root directory]/old.`\n- :wrench: Any modifications you made to Unifier will be wiped, unless they are a part of the new upgrade.\n- :warning: Once started, you cannot abort the upgrade.'
            embed.title = f'{self.bot.ui_emojis.install} Start the upgrade?'
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
            embed.title = f'{self.bot.ui_emojis.install} Upgrading Unifier'
            embed.description = ':hourglass_flowing_sand: Downloading updates\n:x: Installing updates\n:x: Reloading modules'
            await interaction.response.edit_message(embed=embed, view=None)
            self.logger.info('Starting upgrade')
            try:
                self.logger.debug('Purging old update files')
                os.system('rm -rf ' + os.getcwd() + '/update')
                self.logger.info('Downloading from remote repository...')
                os.system('git clone --branch ' + new['version'] + ' --single-branch --depth 1 ' + self.bot.config[
                    'files_endpoint'] + '/unifier.git ' + os.getcwd() + '/update')
                self.logger.debug('Confirming download...')
                x = open(os.getcwd() + '/update/plugins/system.json', 'r')
                x.close()
                self.logger.debug('Download confirmed, proceeding with upgrade')
            except:
                self.logger.exception('Download failed, no rollback required')
                embed.title = f'{self.bot.ui_emojis.error} Upgrade failed'
                embed.description = 'Could not download updates. No rollback is required.'
                embed.colour = 0xff0000
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
                    status(os.system('python3 -m pip install ' + ' '.join(newdeps)))
            except:
                self.logger.exception('Dependency installation failed, no rollback required')
                embed.title = f'{self.bot.ui_emojis.error} Upgrade failed'
                embed.description = 'Could not install dependencies. No rollback is required.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return
            try:
                self.logger.info('Installing upgrades')
                embed.description = ':white_check_mark: Downloading updates\n:hourglass_flowing_sand: Installing updates\n:x: Reloading modules'
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
                    embed.title = f'{self.bot.ui_emojis.success} Restart to apply upgrade'
                    embed.description = f'The upgrade was successful. Please reboot the bot.'
                    embed.colour = 0x00ff00
                    await msg.edit(embed=embed)
                else:
                    self.logger.info('Restarting extensions')
                    embed.description = ':white_check_mark: Downloading updates\n:white_check_mark: Installing updates\n:hourglass_flowing_sand: Reloading modules'
                    await msg.edit(embed=embed)
                    for cog in list(self.bot.extensions):
                        self.logger.debug('Restarting extension: ' + cog)
                        await self.preunload(cog)
                        self.bot.reload_extension(cog)
                    self.logger.info('Upgrade complete')
                    embed.title = f'{self.bot.ui_emojis.success} Upgrade successful'
                    embed.description = 'The upgrade was successful! :partying_face:'
                    embed.colour = 0x00ff00
                    await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed, attempting rollback')
                embed.title = f'{self.bot.ui_emojis.error} Upgrade failed'
                embed.colour = 0xff0000
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
                    embed.description = 'The upgrade failed, and all files have been rolled back.'
                except:
                    self.logger.exception('Rollback failed')
                    self.logger.critical(
                        'The rollback failed. Visit https://unichat-wiki.pixels.onl/setup-selfhosted/upgrading-unifier/manual-rollback for recovery steps.')
                    embed.description = 'The upgrade failed, and the bot may now be in a crippled state.\nPlease check console logs for more info.'
                await msg.edit(embed=embed)
                return
        else:
            embed = nextcord.Embed(title=f'{self.bot.ui_emojis.install} Downloading extension...', description='Getting extension files from remote')

            try:
                with open('plugins/'+plugin+'.json') as file:
                    plugin_info = json.load(file)
            except:
                embed.title = f'{self.bot.ui_emojis.error} Plugin not found'
                embed.description = 'The plugin could not be found.'
                if plugin=='force':
                    embed.description = embed.description + f'\n\n**Hint**: If you\'re trying to force upgrade, run `{self.bot.command_prefix}upgrade system force`'
                embed.colour = 0xff0000
                await ctx.send(embed=embed)
                return
            embed.set_footer(text='Only install plugins from trusted sources!')
            msg = await ctx.send(embed=embed)
            url = plugin_info['repository']
            try:
                os.system('rm -rf ' + os.getcwd() + '/plugin_install')
                status(os.system(
                    'git clone ' + url + ' ' + os.getcwd() + '/plugin_install'))
                with open('plugin_install/plugin.json', 'r') as file:
                    new = json.load(file)
                if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                    embed.title = f'{self.bot.ui_emojis.error} Invalid plugin.json file'
                    embed.description = 'Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.'
                    embed.colour = 0xff0000
                    await msg.edit(embed=embed)
                    return
                if new['release'] <= plugin_info['release'] and not force:
                    embed.title = f'{self.bot.ui_emojis.success} Plugin up to date'
                    embed.description = f'This plugin is already up to date!'
                    embed.colour = 0x00ff00
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
                embed.title = f'{self.bot.ui_emojis.error} Failed to update plugin'
                embed.description = 'The repository URL or the plugin.json file is invalid.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                raise
            embed.title = f'{self.bot.ui_emojis.install} Update `{plugin_id}`?'
            embed.description = f'Name: `{name}`\nVersion: `{version}`\n\n{desc}'
            embed.colour = 0xffcc00
            btns = ui.ActionRow(
                nextcord.ui.Button(style=nextcord.ButtonStyle.green, label='Update', custom_id=f'accept', disabled=False),
                nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
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
                            status(os.system('python3 -m pip install --no-dependencies ' + ' '.join(newdeps)))
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
                embed.title = f'{self.bot.ui_emojis.success} Upgrade successful'
                embed.description = 'The upgrade was successful! :partying_face:'
                embed.colour = 0x00ff00
                await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed')
                embed.title = f'{self.bot.ui_emojis.error} Upgrade failed'
                embed.description = 'The upgrade failed.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return

    @commands.command(description='Activates an emoji pack. Activating the "base" emoji pack resets emojis back to vanilla.')
    async def uiemojis(self, ctx, *, emojipack):
        if not ctx.author.id == self.bot.config['owner']:
            return

        emojipack = emojipack.lower()
        if emojipack=='base':
            self.bot.ui_emojis = Emojis()
            await ctx.send(f'{self.bot.ui_emojis.success} Emoji pack reset to default.')
        else:
            try:
                with open(f'emojis/{emojipack}.json', 'r') as file:
                    data = json.load(file)
                data.update({'id':emojipack})
                with open(f'emojis/current.json', 'w+') as file:
                    json.dump(data, file, indent=2)
                self.bot.ui_emojis = Emojis(data=data)
                await ctx.send(f'{self.bot.ui_emojis.success} Emoji pack {emojipack} activated.')
            except:
                self.logger.exception('An error occurred!')
                await ctx.send(f'{self.bot.ui_emojis.error} Could not activate emoji pack.')

    @commands.command(description='Shows this command.')
    async def help(self,ctx):
        show_sysmgr = False
        show_admin = False
        show_moderation = False

        system_restricted = [
            'initbridge', 'uiemojis'
        ]

        admin_restricted = [
            'addmod','removemod','make','roomdesc','roomlock','roomrestrict','addrule','delrule','fullban','appealban',
            'addexperiment','experimentdesc','removeexperiment','system','trust'
        ]

        mod_restricted = [
            'globalban','globalunban','warn','delwarn','delban'
        ]

        if ctx.author.id == self.bot.config['owner']:
            show_sysmgr = True
            show_admin = True
            show_moderation = True
        elif ctx.author.id in self.bot.admins:
            show_admin = True
            show_moderation = True
        elif ctx.author.id in self.bot.moderators:
            show_moderation = True

        if show_sysmgr:
            if 'asadmin' in ctx.message.content:
                show_sysmgr = False
            elif 'asmod' in ctx.message.content:
                show_sysmgr = False
                show_admin = False
            elif 'asuser' in ctx.message.content:
                show_sysmgr = False
                show_admin = False
                show_moderation = False

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

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel==0:
                extlist = list(self.bot.extensions)
                if not show_sysmgr:
                    extlist.remove('cogs.sysmgr')
                if not show_admin:
                    extlist.remove('cogs.lockdown')
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
                    for x in range(len(parts)):
                        index = x - offset
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
                    if (
                            cmd.qualified_name in admin_restricted and not show_admin or
                            cmd.qualified_name in mod_restricted and not show_moderation or
                            cmd.qualified_name in system_restricted and not show_sysmgr
                    ) and not show_sysmgr or (
                            cogname=='search' and not search_filter(query,cmd)
                    ):
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
                cogname = 'search'
                query = interaction.data['components'][0]['components'][0]['value']
                namematch = True
                descmatch = True
                match = 0

    @commands.command(hidden=True, description='Registers commands.')
    async def forcereg(self, ctx, *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return
        if 'dereg' in args:
            await self.bot.delete_application_commands(*self.bot.get_all_application_commands())
            return await ctx.send('gone, reduced to atoms (hopefully)')
        await self.bot.sync_application_commands()
        return await ctx.send(f'Registered commands to bot')

def setup(bot):
    bot.add_cog(SysManager(bot))
