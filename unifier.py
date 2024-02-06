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
from discord.ext import commands
import aiohttp
import hashlib
bot = commands.Bot(command_prefix='u!',intents=discord.Intents.all())

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession(loop=bot.loop)
    print('ready hehe')
    bot.load_extension("cogs.admin")
    bot.load_extension("cogs.bridge")
    bot.load_extension("cogs.moderation")
    bot.load_extension("cogs.config")

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return

    if message.content.startswith('u!') and not message.author.bot:
        return await bot.process_commands(message)

bot.run('token')
