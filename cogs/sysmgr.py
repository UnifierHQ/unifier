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

import discord
from discord.ext import commands
import inspect
import textwrap
from contextlib import redirect_stdout
from utils import log
import logging
import json
import os
import sys
import traceback
import io
import base64
import re
import ast
import importlib

class Colors: # format: 0xHEXCODE
    greens_hair = 0xa19e78
    unifier = 0xed4545
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    purple = 0x9b59b6
    red = 0xe74c3c
    blurple = 0x7289da
    gold = 0xd4a62a

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

    @commands.command(aliases=['reload-services'], hidden=True)
    async def reload_services(self,ctx,*,services=None):
        """Reloads bot services."""
        if not ctx.author.id == self.bot.config['owner']:
            return
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

    @commands.command(hidden=True)
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

    @commands.command(aliases=['stop', 'poweroff', 'kill'], hidden=True)
    async def shutdown(self, ctx):
        """Gracefully shuts the bot down."""
        if not ctx.author.id == self.bot.config['owner']:
            return
        self.logger.info("Attempting graceful shutdown...")
        try:
            for extension in self.bot.extensions:
                await self.preunload(extension)
            self.logger.info("Backing up message cache...")
            self.bot.db.save_data()
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

    @commands.command(hidden=True)
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
            embed = discord.Embed(title='Unifier Plugins', color=self.bot.colors.unifier)
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
        embed = discord.Embed(
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

    @commands.command(hidden=True, aliases=['cogs'])
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
            embed = discord.Embed(title='Unifier Extensions', color=self.bot.colors.unifier)
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
        embed = discord.Embed(
            title=ext_info.qualified_name,
            description=ext_info.description,
            color=self.bot.colors.unifier
        )
        if (extension == 'cogs.sysmgr' or extension == 'cogs.lockdown' or
                extension == 'sysmgr' or extension == 'lockdown'):
            embed.description = embed.description + '\n# SYSTEM MODULE\nThis module cannot be unloaded.'
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def install(self, ctx, url):
        if not ctx.author.id==self.bot.config['owner']:
            return

        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

        if url.endswith('/'):
            url = url[:-1]
        if not url.endswith('.git'):
            url = url + '.git'
        embed = discord.Embed(title='Downloading extension...', description='Getting extension files from remote')
        embed.set_footer(text='Only install plugins from trusted sources!')
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/plugin_install')
            status(os.system(
                'git clone ' + url + ' ' + os.getcwd() + '/plugin_install'))
            with open('plugin_install/plugin.json', 'r') as file:
                new = json.load(file)
            if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
                embed.title = 'Invalid plugin.json file'
                embed.description = 'Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return
            if new['id']+'.json' in os.listdir('plugins'):
                with open('plugins/'+new['id']+'.json', 'r') as file:
                    current = json.load(file)
                embed.title = 'Plugin already installed'
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
                embed.title = 'Failed to install plugin'
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
            if len(conflicts) > 1:
                embed.title = 'Failed to install plugin'
                embed.description = 'Conflicting files were found:\n'
                for conflict in conflicts:
                    embed.description = embed.description + f'\n`{conflict}`'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return
        except:
            embed.title = 'Failed to install plugin'
            embed.description = 'The repository URL or the plugin.json file is invalid.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        embed.title = f'Install `{plugin_id}`?'
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
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Install', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
        ]
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        await msg.edit(embed=embed, components=components)
        embed.clear_fields()

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await msg.edit(components=components)
        if interaction.custom_id == 'reject':
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await interaction.response.edit_message(components=components)

        await interaction.response.edit_message(embed=embed, components=None)
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
            embed.title = 'Installation successful'
            embed.description = 'The installation was successful! :partying_face:'
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Install failed')
            embed.title = 'Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True)
    async def uninstall(self, ctx, plugin):
        if not ctx.author.id == self.bot.config['owner']:
            return

        if self.bot.update:
            return await ctx.send('Plugin management is disabled until restart.')

        plugin = plugin.lower()
        if plugin=='system':
            return await ctx.send('System plugin cannot be uninstalled!')
        embed = discord.Embed(title='placeholder', description='This will uninstall all of the plugin\'s files. This cannot be undone!')
        embed.colour = 0xffcc00
        try:
            with open('plugins/' + plugin + '.json') as file:
                plugin_info = json.load(file)
        except:
            embed.title = 'Plugin not found'
            embed.description = 'The plugin could not be found.'
            embed.colour = 0xff0000
            await ctx.send(embed=embed)
            return
        embed.title = 'Uninstall plugin `'+plugin_info['id']+'`?'
        row = [
            discord.ui.Button(style=discord.ButtonStyle.red, label='Uninstall', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
        ]
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        msg = await ctx.send(embed=embed, components=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await msg.edit(components=components)
        if interaction.custom_id == 'reject':
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await interaction.response.edit_message(components=components)

        await interaction.response.edit_message(embed=embed, components=None)
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
            embed.title = 'Uninstallation successful'
            embed.description = 'The plugin was successfully uninstalled.'
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            self.logger.exception('Uninstall failed')
            embed.title = 'Uninstallation failed'
            embed.description = 'The uninstallation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            return

    @commands.command(hidden=True)
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
            embed = discord.Embed(title=':inbox_tray: Checking for upgrades...',
                                  description='Getting latest version from remote')
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
                embed.title = ':x: Failed to check for updates'
                embed.description = 'Could not find a valid update.json file on remote'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                raise
            if not update_available:
                embed.title = ':white_check_mark: No updates available'
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
                embed.title = ':arrows_counterclockwise: Update available'
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
                options = []
                index = 0
                for update_option in available:
                    options.append(discord.ui.SelectOption(
                        label=update_option[0],
                        description=update_option[1],
                        value=f'{index}',
                        default=index == selected
                    ))
                    index += 1
                selection = discord.ui.ActionRow(discord.ui.SelectMenu(
                    placeholder='Select version...',
                    max_values=1,
                    min_values=1,
                    custom_id='selection',
                    disabled=len(available) == 1,
                    options=options
                ))
                btns = discord.ui.ActionRow(
                    discord.ui.Button(
                        style=discord.ButtonStyle.green, label='Upgrade', custom_id=f'accept',
                        disabled=False
                    ),
                    discord.ui.Button(
                        style=discord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject',
                        disabled=False
                    ),
                    discord.ui.Button(
                        style=discord.ButtonStyle.link, label='More info',
                        url=f'https://github.com/UnifierHQ/unifier/releases/tag/{version}'
                    )
                )
                components = discord.ui.MessageComponents(
                    selection,btns
                )
                if not interaction:
                    await msg.edit(embed=embed, components=components)
                else:
                    await interaction.response.edit_message(embed=embed, components=components)

                def check(interaction):
                    return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

                try:
                    interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)
                except:
                    return await msg.edit(components=None)
                if interaction.data['custom_id'] == 'reject':
                    return await interaction.response.edit_message(components=None)
                elif interaction.data['custom_id'] == 'accept':
                    break
                elif interaction.data['custom_id'] == 'selection':
                    selected = int(interaction.data['values'][0])
            self.logger.info('Upgrade confirmed, preparing...')
            if not no_backup:
                embed.title = 'Backing up...'
                embed.description = 'Your data is being backed up.'
                await interaction.response.edit_message(embed=embed, components=None)
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
                    embed.title = 'Backup failed'
                    embed.description = 'Unifier could not create a backup. The upgrade has been aborted.'
                    embed.colour = 0xff0000
                    await msg.edit(embed=embed)
                    raise
            else:
                self.logger.info('Backup complete, requesting final confirmation.')
                embed.description = '- :inbox_tray: Your files have been backed up to `[Unifier root directory]/old.`\n- :wrench: Any modifications you made to Unifier will be wiped, unless they are a part of the new upgrade.\n- :warning: Once started, you cannot abort the upgrade.'
            embed.title = ':arrow_up: Start the upgrade?'
            components = discord.ui.MessageComponents(btns)
            if no_backup:
                await interaction.response.edit_message(embed=embed, components=components)
            else:
                await msg.edit(embed=embed, components=components)
            try:
                interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            except:
                return await msg.edit(components=None)
            if interaction.custom_id == 'reject':
                return await msg.edit(components=None)
            self.logger.debug('Upgrade confirmed, beginning upgrade')
            embed.title = ':arrow_up: Upgrading Unifier'
            embed.description = ':hourglass_flowing_sand: Downloading updates\n:x: Installing updates\n:x: Reloading modules'
            await interaction.response.edit_message(embed=embed, components=None)
            self.logger.info('Starting upgrade')
            try:
                self.logger.debug('Purging old update files')
                os.system('rm -rf ' + os.getcwd() + '/update')
                self.logger.info('Downloading from remote repository...')
                os.system('git clone --branch ' + version + ' --single-branch --depth 1 ' + self.bot.config[
                    'files_endpoint'] + '/unifier.git ' + os.getcwd() + '/update')
                self.logger.debug('Confirming download...')
                x = open(os.getcwd() + '/update/plugins/system.json', 'r')
                x.close()
                self.logger.debug('Download confirmed, proceeding with upgrade')
            except:
                self.logger.exception('Download failed, no rollback required')
                embed.title = 'Upgrade failed'
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
                embed.title = ':x: Upgrade failed'
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
                    embed.title = ':white_check_mark: Restart to apply upgrade'
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
                    embed.title = ':white_check_mark: Upgrade successful'
                    embed.description = 'The upgrade was successful! :partying_face:'
                    embed.colour = 0x00ff00
                    await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed, attempting rollback')
                embed.title = ':x: Upgrade failed'
                try:
                    self.logger.debug('Reverting: ' + os.getcwd() + '/unifier.py')
                    status(os.system('cp ' + os.getcwd() + '/old/unifier.py ' + os.getcwd() + '/unifier.py'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/data.json')
                    status(os.system('cp ' + os.getcwd() + '/old/data.json ' + os.getcwd() + '/data.json'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/update.json')
                    status(os.system('cp ' + os.getcwd() + '/old/update.json ' + os.getcwd() + '/update.json'))
                    self.logger.debug('Reverting: ' + os.getcwd() + '/config.json')
                    status(os.system('cp ' + os.getcwd() + '/old/config.json ' + os.getcwd() + '/config.json'))
                    for file in os.listdir(os.getcwd() + '/old/cogs'):
                        self.logger.debug('Reverting: ' + os.getcwd() + '/cogs/' + file)
                        status(
                            os.system('cp ' + os.getcwd() + '/old/cogs/' + file + ' ' + os.getcwd() + '/cogs/' + file))
                    self.logger.info('Rollback success')
                    embed.description = 'The upgrade failed, and all files have been rolled back.'
                except:
                    embed.colour = 0xff0000
                    self.logger.exception('Rollback failed')
                    self.logger.critical(
                        'The rollback failed. Visit https://unichat-wiki.pixels.onl/setup-selfhosted/upgrading-unifier/manual-rollback for recovery steps.')
                    embed.description = 'The upgrade failed, and the bot may now be in a crippled state.\nPlease check console logs for more info.'
                await msg.edit(embed=embed)
                return
        else:
            embed = discord.Embed(title='Downloading extension...', description='Getting extension files from remote')

            try:
                with open('plugins/'+plugin+'.json') as file:
                    plugin_info = json.load(file)
            except:
                embed.title = 'Plugin not found'
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
                    embed.title = 'Invalid plugin.json file'
                    embed.description = 'Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.'
                    embed.colour = 0xff0000
                    await msg.edit(embed=embed)
                    return
                if new['release'] <= plugin_info['release'] and not force:
                    embed.title = 'Plugin up to date'
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
            except:
                embed.title = 'Failed to update plugin'
                embed.description = 'The repository URL or the plugin.json file is invalid.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                raise
            embed.title = f'Update `{plugin_id}`?'
            embed.description = f'Name: `{name}`\nVersion: `{version}`\n\n{desc}'
            embed.colour = 0xffcc00
            row = [
                discord.ui.Button(style=discord.ButtonStyle.green, label='Update', custom_id=f'accept', disabled=False),
                discord.ui.Button(style=discord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
            ]
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            await msg.edit(embed=embed, components=components)

            def check(interaction):
                return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

            try:
                interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            except:
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0], row[1])
                components = discord.ui.MessageComponents(btns)
                return await msg.edit(components=components)
            if interaction.custom_id == 'reject':
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0], row[1])
                components = discord.ui.MessageComponents(btns)
                return await interaction.response.edit_message(components=components)

            await interaction.response.edit_message(embed=embed, components=None)
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
                embed.title = 'Upgrade successful'
                embed.description = 'The upgrade was successful! :partying_face:'
                embed.colour = 0x00ff00
                await msg.edit(embed=embed)
            except:
                self.logger.exception('Upgrade failed')
                embed.title = 'Upgrade failed'
                embed.description = 'The upgrade failed.'
                embed.colour = 0xff0000
                await msg.edit(embed=embed)
                return

def setup(bot):
    bot.add_cog(SysManager(bot))
