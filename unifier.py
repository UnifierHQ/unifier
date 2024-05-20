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

import nextcord
from nextcord.ext import commands, tasks
import random
import aiohttp
import asyncio
import hashlib
import json
import os
import sys
import logging
from utils import log
from dotenv import load_dotenv
import requests
from pathlib import Path

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
    logger.info('You can learn more about modifying Unifier at https://unifier-wiki.pixels.onl/setup-selfhosted/modding-unifier')

if not 'repo' in list(data.keys()):
    logger.critical('WARNING: THIS INSTANCE IS NOT AGPLv3 COMPLAINT!')
    logger.critical('Unifier is licensed under the AGPLv3, meaning you need to make your source code available to users. Please add a repository to the config file under the repo key.')
    sys.exit(1)

if 'allow_prs' in list(data.keys()) and not 'allow_posts' in list(data.keys()):
    logger.warning('From v1.2.4, allow_prs is deprecated. Use allow_posts instead.')

if not env_loaded:
    logger.critical('Could not load .env file! More info: https://unifier-wiki.pixels.onl/setup-selfhosted/getting-started/unifier#set-bot-token')
    sys.exit(1)

if 'token' in list(data.keys()):
    logger.warning('From v1.1.8, Unifier uses .env (dotenv) files to store tokens. We recommend you remove the old token keys from your config.json file.')

cgroup = Path('/proc/self/cgroup')
if Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text():
    logger.warning('Unifier is running in a Docker container. Some features may need plugins to work properly.')

try:
    with open('plugins/system.json', 'r') as file:
        vinfo = json.load(file)
except:
    with open('update.json', 'r') as file:
        vinfo = json.load(file)

try:
    incidents = requests.get('https://discordstatus.com/api/v2/summary.json',timeout=10).json()['incidents']
    for incident in incidents:
        logger.warning('Discord incident: ' + incident['name'])
        logger.warning(incident['status']+': '+incident['incident_updates'][0]['body'])
except:
    logger.debug('Failed to get Discord status')

class DiscordBot(commands.Bot):
    """Extension of discord.ext.commands.Bot for bot configuration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ready = False
        self.ready = None
        self.__update = False
        self.update = None
        self.__config = None
        self.config = None
        self.__safemode = None
        self.safemode = None
        self.bridge = None

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, config):
        if self.__config:
            raise RuntimeError('Config already set')
        self.__config = config

    @property
    def ready(self):
        return self.__ready

    @ready.setter
    def ready(self, ready):
        if self.__ready:
            raise RuntimeError('Bot is already ready')
        self.__ready = ready

    @property
    def update(self):
        return self.__update

    @update.setter
    def update(self, update):
        if self.__update:
            raise RuntimeError('Update lock is set')
        self.__update = update

    @property
    def safemode(self):
        return self.__safemode

    @safemode.setter
    def safemode(self, status):
        if not self.__safemode is None:
            raise RuntimeError('Safemode is set')
        self.__safemode = status


bot = DiscordBot(command_prefix=data['prefix'],intents=nextcord.Intents.all())
bot.config = data
bot.safemode = 'safemode' in sys.argv
mentions = nextcord.AllowedMentions(everyone=False,roles=False,users=False)

if bot.safemode:
    logger.warning('Safemode is enabled. Only system extensions will be loaded.')

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
        await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=new_stat))
    else:
        await bot.change_presence(activity=nextcord.Game(name=new_stat))

@tasks.loop(seconds=round(data['periodic_backup']))
async def periodic_backup():
    try:
        tasks = [bot.loop.create_task(bot.bridge.backup(limit=10000))]
        await asyncio.wait(tasks)
    except:
        logger.exception('Backup failed')

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
            bot.load_extension("cogs.sysmgr")
            bot.pid = os.getpid()
            bot.load_extension("cogs.lockdown")
        except:
            logger.error('An error occurred!')
            logger.critical('System modules failed to load, aborting boot...')
            sys.exit(1)
        logger.debug('System extensions loaded')
        if hasattr(bot, 'bridge'):
            try:
                if len(bot.bridge.bridged)==0:
                    await bot.bridge.restore()
                    logger.info(f'Restored {len(bot.bridge.bridged)} messages')
            except:
                logger.exception('An error occurred!')
                logger.warning('Message restore failed')
        if not changestatus.is_running() and data['enable_rotating_status']:
            changestatus.start()
        if not periodicping.is_running() and data['ping'] > 0:
            periodicping.start()
            logger.debug(f'Pinging servers every {round(data["ping"])} seconds')
        elif data['ping'] <= 0:
            logger.debug(f'Periodic pinging disabled')
        if not periodic_backup.is_running() and data['periodic_backup'] > 0:
            periodic_backup.start()
            logger.debug(f'Backing up messages every {round(data["periodic_backup"])} seconds')
        elif data['periodic_backup'] <= 0:
            logger.debug(f'Periodic backups disabled')
        if data['enable_ctx_commands']:
            logger.debug("Registering context commands...")
            await bot.sync_application_commands()
    logger.info('Unifier is ready!')

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return

    if message.author.id in bot.db['fullbanned']:
        if message.author.id==bot.owner:
            bot.db['fullbanned'].remove(message.author.id)
            bot.db.save_data()
        else:
            return
        
    if message.content.lower().startswith(bot.command_prefix) and not message.author.bot:
        message.content = bot.command_prefix + message.content[len(bot.command_prefix):]
        return await bot.process_commands(message)

bot.run(os.environ.get('TOKEN'))
