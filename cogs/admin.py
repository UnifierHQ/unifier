"""
Unifier - A "simple" bot to unite Discord servers with webhooks
Copyright (C) 2024  Green and ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import traceback

import discord
from discord.ext import commands
import aiofiles
import inspect
import textwrap
from contextlib import redirect_stdout
import cpuinfo
import time
import json
import os

class colors:
    greens_hair = 0xa19e78
    unifier = 0xed4545
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    purple = 0x9b59b6
    red = 0xe74c3c
    blurple = 0x7289da
    
def log(type='???',status='ok',content='None'):
    from time import gmtime, strftime
    time1 = strftime("%Y.%m.%d %H:%M:%S", gmtime())
    if status=='ok':
        status = ' OK  '
    elif status=='error':
        status = 'ERROR'
    elif status=='warn':
        status = 'WARN '
    elif status=='info':
        status = 'INFO '
    else:
        status = ' N/A '
    print(f'[{type} | {time1} | {status}] {content}')

with open('config.json', 'r') as file:
    data = json.load(file)

owner = data['owner']
branch = data['branch']
check_endpoint = data['check_endpoint']
files_endpoint = data['files_endpoint']

noeval = '''```-------------No eval?-------------
⠀⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀```'''

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

class Admin(commands.Cog, name=':wrench: Admin'):
    """A fork of Nevira's Admin module. Lets Unifier owners manage the bot and its extensions and install Upgrader.

    Developed by Green"""
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(self.bot, 'colors'):
            self.bot.colors = colors

    @commands.command(hidden=True)
    async def dashboard(self,ctx):
        if ctx.author.id==owner:
            async with aiofiles.open('uptime.txt','r',encoding='utf-8') as x:
                startup = await x.read()
                startup = int(startup)
                await x.close()
            embed = discord.Embed(title='Unifier dashboard',description='Just a moment...',color=0xb5eeff)
            before = time.monotonic()
            msg = await ctx.send(embed=embed)
            ping = (time.monotonic() - before) * 1000
            pingspeed = round(ping, 1)
            current = round(time.time())
            uptime = current - startup
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            seconds = (uptime % 3600) % 60
            import platform
            import psutil
            arch = platform.machine()
            osinfo = platform.platform()
            cpu = await self.bot.loop.run_in_executor(None, lambda: cpuinfo.get_cpu_info()['brand_raw'])
            ghz = await self.bot.loop.run_in_executor(None, lambda: round(cpuinfo.get_cpu_info()['hz_actual'][0]/1000000000,2))
            ram = round(psutil.virtual_memory().total / (1024.0 **3))
            cpuusage = psutil.cpu_percent()
            ramusage = psutil.virtual_memory()[2]
            membercount = 0
            for guild in self.bot.guilds:
                try:
                    membercount = membercount + guild.member_count
                except:
                    pass
            embed = discord.Embed(title='Unifier Dashboard',color=0xb5eeff)
            embed.add_field(name='Latency',value='%s ms' % round(ping, 1),inline=True)
            embed.add_field(name='CPU',value='{0} ({1} GHz, currently using {2}%)'.format(cpu,ghz,cpuusage),inline=True)
            embed.add_field(name='RAM',value='{0} GB (currently using {1}%)'.format(ram,ramusage),inline=True)
            embed.add_field(name='Architecture',value=arch,inline=True)
            embed.add_field(name='OS',value=osinfo,inline=True)
            guildcount = len(self.bot.guilds)
            if guildcount == 69:
                guildcount = '69 :smirk:'
            embed.add_field(name='Server count',value='%s' % guildcount,inline=True)
            embed.add_field(name='User count',value='{0} ({1} cached)'.format(membercount,len(set(self.bot.get_all_members())),inline=True))
            embed.add_field(name='Up since',value=f'<t:{startup}:f>',inline=False)
            embed.add_field(name='Uptime',value=f'`{hours}` hours, `{minutes}` minutes, `{seconds}` seconds',inline=False)
            await msg.edit(embed=embed)

    @commands.command(hidden=True)
    async def eval(self,ctx,*,body):
        if ctx.author.id==owner:
            import io
            import traceback
            env = {
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                'source': inspect.getsource,
                'session':self.bot.session,
                'bot':self.bot
            }

            env.update(globals())

            body = cleanup_code(body)
            stdout = io.StringIO()
            err = out = None

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                if 'bot.token' in body:
                    raise ValueError('Blocked phrase')
                exec(to_compile, env)
            except Exception as e:
                pass

            try:
                func = env['func']
            except Exception as e:
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` the code didn\'t work\n`2.` no meme?')
                await ctx.author.send(f'```py\n{e.__class__.__name__}: {e}\n```')
                return
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` the code didn\'t work\n`2.` no meme?')
                await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                if value=='':
                    pass
                else:
                    await ctx.send('```%s```' % value)
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @eval.error
    async def eval_error(self,ctx,error):
        if ctx.author.id==owner:
            if isinstance(error, commands.MissingRequiredArgument):
                try:
                    await ctx.send('where code :thinking:',file=discord.File(fp='nocode.png'))
                except:
                    try:
                        await ctx.send('where code :thinking:')
                    except:
                        await ctx.author.send('where code and permission to send messages :thinking:')
            else:
                try:
                    await ctx.send('Something went horribly wrong, sadge')
                except:
                    await ctx.author.send('i cant send stuff in that channel :/')
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @commands.command(hidden=True,aliases=['cogs'])
    async def extensions(self,ctx,*,extension=None):
        if extension:
            extension = extension.lower()
        page = 0
        try:
            page = int(extension)-1
            if page < 0:
                page = 0
            extension = None
        except:
            pass
        if not extension:
            offset = page*20
            embed = discord.Embed(title='Unifier Extensions',color=0xed4545)
            text = ''
            extlist = list(self.bot.extensions)
            if offset > len(extlist):
                page = len(extlist) // 20 - 1
                offset = page * 20
            for x in range(offset,20+offset):
                if x == len(list(self.bot.cogs)):
                    break
                cog = self.bot.cogs[list(self.bot.cogs)[x]]
                ext = list(self.bot.extensions)[x]
                if text=='':
                    text = f'- {cog.qualified_name} (`{ext}`)'
                else:
                    text = f'{text}\n- {cog.qualified_name} (`{ext}`)'
            embed.description = text
            embed.set_footer(text="Page "+str(page+1))
            return await ctx.send(embed=embed)
        found = False
        index = 0
        for ext in list(self.bot.extensions):
            if ext.replace('cogs.','',1) == extension or ext == extension:
                found = True
                break
            index += 1
        if found:
            ext_info = self.bot.cogs[list(self.bot.cogs)[index]]
        else:
            return await ctx.send('Could not find extension!')
        embed = discord.Embed(title=ext_info.qualified_name,description=ext_info.description,color=0xed4545)
        if extension=='admin' or extension=='cogs.admin' or extension == 'lockdown' or extension == 'cogs.lockdown':
            embed.description = embed.description + '\n# SYSTEM MODULE\nThis module cannot be unloaded.'
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def reload(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Reloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    if extension=='lockdown':
                        raise ValueError('Cannot unload lockdown extension for security purposes.')
                    self.bot.reload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Reload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run reload! :x:')

    @commands.command(hidden=True)
    async def load(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Loading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    self.bot.load_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Load completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run load! :x:')

    @commands.command(hidden=True)
    async def unload(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Unloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    if extension=='admin':
                        raise ValueError('Cannot unload the admin extension, let\'s not break the bot here!')
                    if extension=='lockdown':
                        raise ValueError('Cannot unload lockdown extension for security purposes.')
                    if extension=='bridge_revolt':
                        raise ValueError('Revolt Bridge cannot be unloaded. Use u!stop-revolt instead.')
                    self.bot.unload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Unload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run unload! :x:')

    @commands.command(name='start-revolt', hidden=True)
    async def start_revolt(self, ctx):
        """Starts the Revolt client. This is automatically done on boot"""
        if not ctx.author.id == owner:
            return
        try:
            self.bot.load_extension('cogs.bridge_revolt')
            await ctx.send('Revolt client started.')
        except Exception as e:
            if isinstance(e, discord.ext.commands.errors.ExtensionAlreadyLoaded):
                return await ctx.send('Revolt client is already online.')
            traceback.print_exc()
            await ctx.send('Something went wrong while starting the instance.')

    @commands.command(name='stop-revolt',hidden=True)
    async def stop_revolt(self,ctx):
        """Kills the Revolt client. This is automatically done when upgrading Unifier."""
        if not ctx.author.id==owner:
            return
        try:
            await self.bot.revolt_session.close()
            del self.bot.revolt_client
            del self.bot.revolt_session
            self.bot.unload_extension('cogs.bridge_revolt')
            await ctx.send('Revolt client stopped.')
        except Exception as e:
            if isinstance(e, AttributeError):
                return await ctx.send('Revolt client is already offline.')
            traceback.print_exc()
            await ctx.send('Something went wrong while killing the instance.')

    @commands.command(name='restart-revolt', hidden=True)
    async def restart_revolt(self, ctx):
        """Restarts the Revolt client."""
        if not ctx.author.id == owner:
            return
        try:
            await self.bot.revolt_session.close()
            del self.bot.revolt_client
            del self.bot.revolt_session
            self.bot.reload_extension('cogs.bridge_revolt')
            await ctx.send('Revolt client restarted.')
        except Exception as e:
            if isinstance(e, AttributeError):
                return await ctx.send('Revolt client is not offline.')
            traceback.print_exc()
            await ctx.send('Something went wrong while restarting the instance.')

    @commands.command(name='start-guilded', hidden=True)
    async def start_guilded(self, ctx):
        """Starts the Guilded client. This is automatically done on boot"""
        if not ctx.author.id == owner:
            return
        try:
            self.bot.load_extension('cogs.bridge_guilded')
            await ctx.send('Guilded client started.')
        except Exception as e:
            if isinstance(e, discord.ext.commands.errors.ExtensionAlreadyLoaded):
                return await ctx.send('Guilded client is already online.')
            traceback.print_exc()
            await ctx.send('Something went wrong while starting the instance.')

    @commands.command(name='stop-guilded', hidden=True)
    async def stop_guilded(self, ctx):
        """Kills the Guilded client. This is automatically done when upgrading Unifier."""
        if not ctx.author.id == owner:
            return
        try:
            await self.bot.guilded_client.close()
            self.bot.guilded_client_task.cancel()
            del self.bot.guilded_client
            self.bot.unload_extension('cogs.bridge_guilded')
            await ctx.send('Guilded client stopped.')
        except Exception as e:
            if isinstance(e, AttributeError):
                return await ctx.send('Guilded client is already offline.')
            traceback.print_exc()
            await ctx.send('Something went wrong while killing the instance.')

    @commands.command(name='restart-guilded', hidden=True)
    async def restart_guilded(self, ctx):
        """Restarts the Guilded client."""
        if not ctx.author.id == owner:
            return
        try:
            await self.bot.guilded_client.close()
            del self.bot.guilded_client
            self.bot.reload_extension('cogs.bridge_guilded')
            await ctx.send('Guilded client restarted.')
        except Exception as e:
            if isinstance(e, AttributeError):
                return await ctx.send('Guilded client is not offline.')
            traceback.print_exc()
            await ctx.send('Something went wrong while restarting the instance.')

    @commands.command(name='install-upgrader', hidden=True)
    async def install_upgrader(self, ctx):
        if not ctx.author.id==owner:
            return
        embed = discord.Embed(title='Finding Upgrader version...', description='Getting latest version from remote')
        try:
            x = open('cogs/upgrader.py','r',encoding='utf-8')
            x.close()
        except:
            pass
        else:
            embed.title = 'Upgrader already installed'
            embed.description = f'Unifier Upgrader is already installed! Run `{self.bot.command_prefix}upgrade-upgrader` to upgrade the Upgrader.'
            embed.colour = 0x00ff00
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/update_check')
            status(os.system(
                'git clone --branch ' + branch + ' ' + files_endpoint + '/unifier-version.git ' + os.getcwd() + '/update_check'))
            with open('update_check/upgrader.json', 'r') as file:
                new = json.load(file)
            release = new['release']
            version = new['version']
        except:
            embed.title = 'Failed to check for updates'
            embed.description = 'Could not find a valid upgrader.json file on remote'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        print('Upgrader install available: ' + new['version'])
        print('Confirm install through Discord.')
        embed.title = 'Upgrader available'
        embed.description = f'Unifier Upgrader is available!\n\nVersion: {version} (`{release}`)\n\nUnifier Upgrader is an extension that allows Unifier admins to easily upgrade Unifier to the newest version. This extension will be loaded on boot.'
        embed.colour = 0xffcc00
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Install', custom_id=f'accept', disabled=False),
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
        print('Installation confirmed, preparing...')
        embed.title = 'Start the installation?'
        embed.description = '- :x: Your files have **not** been backed up, as this is not a Unifier upgrade.\n- :tools: A new file called `upgrader.py` will be made in `[Unifier root directory]/cogs`.\n- :warning: Once started, you cannot abort the installation.'
        await interaction.response.edit_message(embed=embed, components=components)
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
        print('Installation confirmed, installing Unifier Upgrader...')
        print()
        embed.title = 'Installing Unifier Upgrader'
        embed.description = ':hourglass_flowing_sand: Downloading Upgrader\n:x: Installing Upgrader\n:x: Activating Upgrader'
        await interaction.response.edit_message(embed=embed, components=None)
        log(type='UPG', status='info', content='Starting install')
        try:
            log(type='GIT', status='info', content='Purging old update files')
            os.system('rm -rf ' + os.getcwd() + '/update_upgrader')
            log(type='GIT', status='info', content='Downloading from remote repository...')
            status(os.system(
                'git clone --branch main ' + files_endpoint + '/unifier-upgrader.git ' + os.getcwd() + '/update_upgrader'))
            log(type='GIT', status='info', content='Confirming download...')
            x = open(os.getcwd() + '/update_upgrader/upgrader.py', 'r')
            x.close()
            log(type='GIT', status='ok', content='Download confirmed, proceeding with install')
        except:
            log(type='UPG', status='error', content='Download failed, no rollback required')
            embed.title = 'Upgrade failed'
            embed.description = 'Could not download updates. Nothing new was installed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        try:
            log(type='INS', status='info', content='Installing Upgrader')
            embed.description = ':white_check_mark: Downloading Upgrader\n:hourglass_flowing_sand: Installing Upgrader\n:x: Activating Upgrader'
            await msg.edit(embed=embed)
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_upgrader/upgrader.py')
            status(os.system(
                'cp ' + os.getcwd() + '/update_upgrader/upgrader.py' + ' ' + os.getcwd() + '/cogs/upgrader.py'))
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_check/upgrader.json')
            status(
                os.system('cp ' + os.getcwd() + '/update_check/upgrader.json' + ' ' + os.getcwd() + '/upgrader.json'))
            embed.description = ':white_check_mark: Downloading Upgrader\n:white_check_mark: Installing Upgrader\n:hourglass_flowing_sand: Activating Upgrader'
            await msg.edit(embed=embed)
            log(type='UPG', status='ok', content='Activating extension: cogs.upgrader')
            self.bot.load_extension('cogs.upgrader')
            log(type='UPG', status='ok', content='Installation complete')
            embed.title = 'Installation successful'
            embed.description = 'The installation was successful! :partying_face:\nUpgrader has been loaded and will be loaded on boot.'
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            log(type='UPG', status='error', content='Install failed')
            embed.title = 'Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise

    @commands.command(name='install-revolt', hidden=True, aliases=['install-revolt-support'])
    async def install_revolt(self, ctx):
        if not ctx.author.id == owner:
            return
        embed = discord.Embed(title='Finding Revolt Support version...', description='Getting latest version from remote')
        try:
            x = open('cogs/bridge_revolt.py', 'r', encoding='utf-8')
            x.close()
        except:
            pass
        else:
            embed.title = 'Revolt Support already installed'
            embed.description = f'Revolt Support is already installed! Run `{self.bot.command_prefix}upgrade-revolt` to upgrade Revolt Support (Upgrader required).'
            embed.colour = 0x00ff00
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/update_check')
            status(os.system(
                'git clone --branch ' + branch + ' ' + files_endpoint + '/unifier-version.git ' + os.getcwd() + '/update_check'))
            with open('update_check/revolt.json', 'r') as file:
                new = json.load(file)
            release = new['release']
            version = new['version']
        except:
            embed.title = 'Failed to check for updates'
            embed.description = 'Could not find a valid upgrader.json file on remote'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        print('Revolt Support install available: ' + new['version'])
        print('Confirm install through Discord.')
        embed.title = 'Revolt Support available'
        embed.description = f'Unifier Revolt Support is available!\n\nVersion: {version} (`{release}`)\n\nUnifier Revolt Support is an extension that allows Unifier to bridge messages between Discord and Revolt. This extension will be loaded on boot.'
        embed.colour = 0xffcc00
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Install', custom_id=f'accept', disabled=False),
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
        print('Installation confirmed, preparing...')
        embed.title = 'Start the installation?'
        embed.description = '- :x: Your files have **not** been backed up, as this is not a Unifier upgrade.\n- :tools: A new file called `bridge_revolt.py` will be made in `[Unifier root directory]/cogs`.\n- :warning: Once started, you cannot abort the installation.'
        await interaction.response.edit_message(embed=embed, components=components)
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
        print('Installation confirmed, installing Revolt Support...')
        print()
        embed.title = 'Installing Revolt Support'
        embed.description = ':hourglass_flowing_sand: Downloading Revolt Support\n:x: Installing Revolt Support dependencies\n:x: Installing Revolt Support\n:x: Activating Revolt Support'
        await interaction.response.edit_message(embed=embed, components=None)
        log(type='UPG', status='info', content='Starting install')
        try:
            log(type='GIT', status='info', content='Purging old update files')
            os.system('rm -rf ' + os.getcwd() + '/update_revolt')
            log(type='GIT', status='info', content='Downloading from remote repository...')
            status(os.system(
                'git clone --branch main ' + files_endpoint + '/unifier-revolt.git ' + os.getcwd() + '/update_revolt'))
            log(type='GIT', status='info', content='Confirming download...')
            x = open(os.getcwd() + '/update_revolt/bridge_revolt.py', 'r')
            x.close()
            log(type='GIT', status='ok', content='Download confirmed, proceeding with install')
        except:
            log(type='UPG', status='error', content='Download failed, no rollback required')
            embed.title = 'Upgrade failed'
            embed.description = 'Could not download updates. Nothing new was installed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        try:
            log(type='INS', status='info', content='Installing Upgrader')
            embed.description = ':white_check_mark: Downloading Revolt Support\n:hourglass_flowing_sand: Installing Revolt Support dependencies\n:x: Installing Revolt Support\n:x: Activating Revolt Support'
            await msg.edit(embed=embed)
            log(type='PIP', status='info', content='Installing: revolt.py')
            status(os.system('python3 -m pip install -U revolt.py'))
            embed.description = ':white_check_mark: Downloading Revolt Support\n:white_check_mark: Installing Revolt Support dependencies\n:hourglass_flowing_sand: Installing Revolt Support\n:x: Activating Revolt Support'
            await msg.edit(embed=embed)
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_revolt/bridge_revolt.py')
            status(os.system(
                'cp ' + os.getcwd() + '/update_revolt/bridge_revolt.py' + ' ' + os.getcwd() + '/cogs/bridge_revolt.py'))
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_check/revolt.json')
            status(
                os.system('cp ' + os.getcwd() + '/update_check/revolt.json' + ' ' + os.getcwd() + '/revolt.json'))
            embed.description = ':white_check_mark: Downloading Revolt Support\n:white_check_mark: Installing Revolt Support dependencies\n:white_check_mark: Installing Revolt Support\n:hourglass_flowing_sand: Activating Revolt Support'
            await msg.edit(embed=embed)
            log(type='UPG', status='ok', content='Activating extension: cogs.bridge_revolt')
            self.bot.load_extension('cogs.bridge_revolt')
            log(type='UPG', status='ok', content='Installation complete')
            embed.title = 'Installation successful'
            embed.description = 'The installation was successful! :partying_face:\nRevolt Support has been loaded and will be loaded on boot.'
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            log(type='UPG', status='error', content='Install failed')
            embed.title = 'Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise

    @commands.command(name='install-guilded', hidden=True, aliases=['install-guilded-support'])
    async def install_guilded(self, ctx):
        if not ctx.author.id == owner:
            return
        embed = discord.Embed(title='Finding Guilded Support version...',
                              description='Getting latest version from remote')
        try:
            x = open('cogs/bridge_guilded.py', 'r', encoding='utf-8')
            x.close()
        except:
            pass
        else:
            embed.title = 'Guilded Support already installed'
            embed.description = f'Guilded Support is already installed! Run `{self.bot.command_prefix}upgrade-guilded` to upgrade Guilded Support (Upgrader required).'
            embed.colour = 0x00ff00
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=embed)
        try:
            os.system('rm -rf ' + os.getcwd() + '/update_check')
            status(os.system(
                'git clone --branch ' + branch + ' ' + files_endpoint + '/unifier-version.git ' + os.getcwd() + '/update_check'))
            with open('update_check/guilded.json', 'r') as file:
                new = json.load(file)
            release = new['release']
            version = new['version']
        except:
            embed.title = 'Failed to check for updates'
            embed.description = 'Could not find a valid upgrader.json file on remote'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        print('Guilded Support install available: ' + new['version'])
        print('Confirm install through Discord.')
        embed.title = 'Guilded Support available'
        embed.description = f'Unifier Guilded Support is available!\n\nVersion: {version} (`{release}`)\n\nUnifier Guilded Support is an extension that allows Unifier to bridge messages between Discord and Guilded. This extension will be loaded on boot.'
        embed.colour = 0xffcc00
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Install', custom_id=f'accept', disabled=False),
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
        print('Installation confirmed, preparing...')
        embed.title = 'Start the installation?'
        embed.description = '- :x: Your files have **not** been backed up, as this is not a Unifier upgrade.\n- :tools: A new file called `bridge_guilded.py` will be made in `[Unifier root directory]/cogs`.\n- :warning: Once started, you cannot abort the installation.'
        await interaction.response.edit_message(embed=embed, components=components)
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
        print('Installation confirmed, installing Guilded Support...')
        print()
        embed.title = 'Installing Guilded Support'
        embed.description = ':hourglass_flowing_sand: Downloading Guilded Support\n:x: Installing Guilded Support dependencies\n:x: Installing Guilded Support\n:x: Activating Guilded Support'
        await interaction.response.edit_message(embed=embed, components=None)
        log(type='UPG', status='info', content='Starting install')
        try:
            log(type='GIT', status='info', content='Purging old update files')
            os.system('rm -rf ' + os.getcwd() + '/update_guilded')
            log(type='GIT', status='info', content='Downloading from remote repository...')
            status(os.system(
                'git clone --branch main ' + files_endpoint + '/unifier-guilded.git ' + os.getcwd() + '/update_guilded'))
            log(type='GIT', status='info', content='Confirming download...')
            x = open(os.getcwd() + '/update_guilded/bridge_guilded.py', 'r')
            x.close()
            log(type='GIT', status='ok', content='Download confirmed, proceeding with install')
        except:
            log(type='UPG', status='error', content='Download failed, no rollback required')
            embed.title = 'Upgrade failed'
            embed.description = 'Could not download updates. Nothing new was installed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        try:
            log(type='INS', status='info', content='Installing Upgrader')
            embed.description = ':white_check_mark: Downloading Guilded Support\n:hourglass_flowing_sand: Installing Guilded Support dependencies\n:x: Installing Guilded Support\n:x: Activating Guilded Support'
            await msg.edit(embed=embed)
            log(type='PIP', status='info', content='Installing: guilded.py')
            status(os.system('python3 -m pip install -U guilded.py'))
            embed.description = ':white_check_mark: Downloading Guilded Support\n:white_check_mark: Installing Guilded Support dependencies\n:hourglass_flowing_sand: Installing Guilded Support\n:x: Activating Guilded Support'
            await msg.edit(embed=embed)
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_guilded/bridge_guilded.py')
            status(os.system(
                'cp ' + os.getcwd() + '/update_guilded/bridge_guilded.py' + ' ' + os.getcwd() + '/cogs/bridge_guilded.py'))
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update_check/guilded.json')
            status(
                os.system('cp ' + os.getcwd() + '/update_check/guilded.json' + ' ' + os.getcwd() + '/guilded.json'))
            embed.description = ':white_check_mark: Downloading Guilded Support\n:white_check_mark: Installing Guilded Support dependencies\n:white_check_mark: Installing Guilded Support\n:hourglass_flowing_sand: Activating Guilded Support'
            await msg.edit(embed=embed)
            log(type='UPG', status='ok', content='Activating extension: cogs.bridge_guilded')
            self.bot.load_extension('cogs.bridge_guilded')
            log(type='UPG', status='ok', content='Installation complete')
            embed.title = 'Installation successful'
            embed.description = 'The installation was successful! :partying_face:\nGuilded Support has been loaded and will be loaded on boot.'
            embed.colour = 0x00ff00
            await msg.edit(embed=embed)
        except:
            log(type='UPG', status='error', content='Install failed')
            embed.title = 'Installation failed'
            embed.description = 'The installation failed.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise

def setup(bot):
    bot.add_cog(Admin(bot))
