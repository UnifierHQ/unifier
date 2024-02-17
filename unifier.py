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
import hashlib
import json
bot = commands.Bot(command_prefix='u!',intents=discord.Intents.all())

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

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
    print("loading cogs...")
    bot.load_extension("cogs.admin")
    bot.load_extension("cogs.bridge")
    bot.load_extension("cogs.moderation")
    bot.load_extension("cogs.config")
    try:
        bot.load_extension("cogs.upgrader")
    except:
        print('WARNING: Upgrader is missing, consider installing it for an easier life.')
    if not changestatus.is_running():
        changestatus.start()
    print('registering commands...')
    toreg = []
    for command in bot.commands:
        if isinstance(command, commands.core.ContextMenuCommand):
            toreg.append(command)
    await bot.register_application_commands(commands=toreg)
    print('ready hehe')

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return
        
    if message.content.startswith('U!'):
        message.content = message.content.replace('U','u',1)

    if message.content.startswith('u!') and not message.author.bot:
        return await bot.process_commands(message)

with open('config.json', 'r') as file:
    data = json.load(file)

bot.run(data['token'])
