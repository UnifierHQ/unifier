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

import discord
from discord.ext import commands, tasks
import random
import aiohttp
import asyncio
import hashlib
import json
import traceback
import os
import sys
import logging
from utils import log
from dotenv import load_dotenv

if os.name != "nt":
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except:
        pass

with open('config.json', 'r') as file:
    data = json.load(file)

env_loaded = load_dotenv()

level = logging.DEBUG if data['debug'] else logging.INFO
package = data['package']

logger = log.buildlogger(package,'core',level)

if not '.welcome.txt' in os.listdir():
    x = open('.welcome.txt','w+')
    x.close()
    logger.info('Thank you for installing Unifier!')
    logger.info('Unifier is licensed under the AGPLv3, so if you would like to add your own twist to Unifier, you must follow AGPLv3 conditions.')
    logger.info('You can learn more about modifying Unifier at https://unichat-wiki.pixels.onl/setup-selfhosted/modding-unifier')

if not 'repo' in list(data.keys()):
    logger.critical('WARNING: THIS INSTANCE IS NOT AGPLv3 COMPLAINT!')
    logger.critical('Unifier is licensed under the AGPLv3, meaning you need to make your source code available to users. Please add a repository to the config file under the repo key.')
    sys.exit(1)

if not env_loaded:
    logger.critical('Could not load .env file! More info: https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started/unifier#set-bot-token')
    sys.exit(1)

if 'token' in list(data.keys()):
    logger.warning('From v1.1.8, Unifier uses .env (dotenv) files to store tokens. We recommend you remove the old token keys from your config.json file.')

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

@tasks.loop(seconds=round(data['ping']))
async def periodicping():
    guild = bot.guilds[0]
    try:
        await bot.fetch_channel(guild.text_channels[0].id)
    except:
        pass

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession(loop=bot.loop)
    logger.info('Loading Unifier extensions...')
    if hasattr(bot, 'locked'):
        locked = bot.locked
    else:
        locked = False
    if not locked:
        try:
            bot.load_extension("cogs.admin")
            bot.pid = os.getpid()
            bot.load_extension("cogs.lockdown")
        except:
            logger.error('An error occurred!')
            logger.critical('Admin extension failed to load, aborting boot...')
            sys.exit(1)
        logger.debug('System extensions loaded')
        bot.load_extension("cogs.bridge")
        try:
            if hasattr(bot, 'bridge'):
                try:
                    if len(bot.bridge.bridged)==0:
                        await bot.bridge.restore()
                        logger.info(f'Restored {len(bot.bridge.bridged)} messages')
                except:
                    logger.exception('An error occurred!')
                    logger.warn('Message restore failed')
            try:
                if 'revolt' in data['external']:
                    bot.load_extension("cogs.bridge_revolt")
            except:
                try:
                    x = open('cogs/bridge_revolt.py','r')
                    x.close()
                    traceback.print_exc()
                except:
                    logger.warn(f'Revolt Support is enabled, but not installed. Run {bot.command_prefix}install-revolt to install Revolt Support.')
            try:
                if 'guilded' in data['external']:
                    bot.load_extension("cogs.bridge_guilded")
            except:
                try:
                    x = open('cogs/bridge_guilded.py','r')
                    x.close()
                    traceback.print_exc()
                except:
                    logger.warn(f'Guilded Support is enabled, but not installed. Run {bot.command_prefix}install-guilded to install Guilded Support.')
            bot.load_extension("cogs.moderation")
            bot.load_extension("cogs.config")
            bot.load_extension("cogs.badge")
            bot.load_extension("cogs.uptime")
        except:
            logger.error('An error occurred!')
            logger.critical('System extensions failed to load, but admin extension has been loaded.')
            logger.critical('Please repair the problematic extension, then load the extensions manually.')
        try:
            bot.load_extension("cogs.upgrader")
        except:
            logger.warning(f'Upgrader is  not installed. Run {bot.command_prefix}install-upgrader to easily manage bot upgrades.')
        if not changestatus.is_running() and data['enable_rotating_status']:
            changestatus.start()
        if not periodicping.is_running() and data['ping'] > 0:
            periodicping.start()
            logger.debug(f'Pinging servers every {round(data["ping"])} seconds')
        elif data['ping'] <= 0:
            logger.debug(f'Periodic pinging disabled')
        if data['enable_ctx_commands']:
            logger.debug("Registering context commands...")
            toreg = []
            for command in bot.commands:
                if isinstance(command, commands.core.ContextMenuCommand):
                    if command.name=='Reaction image':
                        toreg.insert(0,command)
                    else:
                        toreg.append(command)
            await bot.register_application_commands(commands=toreg)
            logger.debug(f'Registered {len(toreg)} commands')
    logger.info('Unifier is ready!')

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return
        
    if message.content.lower().startswith(bot.command_prefix) and not message.author.bot:
        message.content = bot.command_prefix + message.content[len(bot.command_prefix):]
        return await bot.process_commands(message)

bot.run(os.environ.get('TOKEN'))
