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

import discord
from discord.ext import commands, tasks
import random
import aiohttp
import asyncio
import hashlib
import json
import traceback
from time import gmtime, strftime
import os

if os.name != "nt":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

with open('config.json', 'r') as file:
    data = json.load(file)

with open('update.json', 'r') as file:
    vinfo = json.load(file)

bot = commands.Bot(command_prefix=data['prefix'],intents=discord.Intents.all())

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

asciiart = """  _    _       _  __ _           
 | |  | |     (_)/ _(_)          
 | |  | |_ __  _| |_ _  ___ _ __ 
 | |  | | '_ \\| |  _| |/ _ \\ '__|
 | |__| | | | | | | | |  __/ |   
  \\____/|_| |_|_|_| |_|\\___|_| """

print(asciiart)
print('Version: '+vinfo['version'])
print('Release '+str(vinfo['release']))
print()

try:
    with open('upgrader.json', 'r') as file:
        uvinfo = json.load(file)
    print('Upgrader is installed')
    print('Version: ' + uvinfo['version'])
    print('Release ' + str(uvinfo['release']))
    print()
except:
    pass

try:
    with open('revolt.json', 'r') as file:
        rvinfo = json.load(file)
    print('Revolt Support is installed')
    print('Version: ' + rvinfo['version'])
    print('Release ' + str(rvinfo['release']))
    print()
except:
    pass

try:
    with open('guilded.json', 'r') as file:
        gvinfo = json.load(file)
    print('Guilded Support is installed')
    print('Version: ' + gvinfo['version'])
    print('Release ' + str(gvinfo['release']))
    print()
except:
    pass

def log(type='???',status='ok',content='None'):
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
        raise ValueError('Invalid status type provided')
    print(f'[{type} | {time1} | {status}] {content}')

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

@tasks.loop(seconds=300)
async def changestatus():
    status_messages = [
        "with the ban hammer",
        "with fire",
        "with the API",
        "hide and seek",
        "with code",
        "in debug mode",
        "in a parallel universe",
        "with commands",
        "a game of chess",
        "with electrons",
        "with the matrix",
        "with cookies",
        "with the metaverse",
        "with emojis",
        "with Nevira",
        "with green.",
        "with ItsAsheer",
        "webhooks",
    ]
    new_stat = random.choice(status_messages)
    if new_stat == "webhooks":
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=new_stat))
    else:
        await bot.change_presence(activity=discord.Game(name=new_stat))

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession(loop=bot.loop)
    log("BOT","info","Loading Unifier extensions...")
    bot.load_extension("cogs.lockdown")
    if hasattr(bot, 'locked'):
        locked = bot.locked
    else:
        locked = False
    if not locked:
        bot.load_extension("cogs.admin")
        bot.pid = os.getpid()
        bot.load_extension("cogs.bridge")
        if hasattr(bot, 'bridge'):
            try:
                if len(bot.bridge.bridged)==0:
                    await bot.bridge.restore()
                    log('SYS','ok','Restored '+str(len(bot.bridge.bridged))+' messages')
            except:
                traceback.print_exc()
                log('SYS','warn','Message restore failed')
        try:
            if 'revolt' in data['external']:
                bot.load_extension("cogs.bridge_revolt")
        except:
            try:
                x = open('cogs/bridge_revolt.py','r')
                x.close()
                traceback.print_exc()
            except:
                log("BOT","warn",f'Revolt Support is enabled, but not installed. Run {bot.command_prefix}install-revolt to install Revolt Support.')
        try:
            if 'guilded' in data['external']:
                bot.load_extension("cogs.bridge_guilded")
        except:
            try:
                x = open('cogs/bridge_guilded.py','r')
                x.close()
                traceback.print_exc()
            except:
                log("BOT","warn",f'Guilded Support is enabled, but not installed. Run {bot.command_prefix}install-guilded to install Guilded Support.')
        bot.load_extension("cogs.moderation")
        bot.load_extension("cogs.config")
        bot.load_extension("cogs.badge")
        try:
            bot.load_extension("cogs.upgrader")
        except:
            log("BOT","warn",f'Upgrader is  not installed. Run {bot.command_prefix}install-upgrader to easily manage bot upgrades.')
        if not changestatus.is_running() and data['enable_rotating_status']:
            changestatus.start()
        if data['enable_ctx_commands']:
            log("BOT","info","Registering context commands...")
            toreg = []
            for command in bot.commands:
                if isinstance(command, commands.core.ContextMenuCommand):
                    if command.name=='Reaction image':
                        toreg.insert(0,command)
                    else:
                        toreg.append(command)
            await bot.register_application_commands(commands=toreg)
    log("BOT","ok","Unifier is ready!")

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return
        
    if message.content.lower().startswith(bot.command_prefix) and not message.author.bot:
        message.content = bot.command_prefix + message.content[len(bot.command_prefix):]
        return await bot.process_commands(message)

bot.run(data['token'])
