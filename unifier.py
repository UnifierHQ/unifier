import discord
from discord.ext import commands
import ast
import aiofiles
import aiohttp
import hashlib

import threading #Used for the random by time status
import random
import time

bot = commands.Bot(command_prefix='u!',intents=discord.Intents.all())

def random_status_thread():
    while True:
        status_messages = [ # Used chatgpt 💀
        "with GPT-3.5",
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
        "SimAirport",
        "with Nevira",
        "with green."
        "with ItsAsheer"
        "webhooks",
        ]
        new_stat = random.choice(status_messages)
        if new_stat == "webhooks":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=new_stat))
        else:
            await bot.change_presence(activity=discord.Game(name=new_stat))
        time.sleep(5 * 60) # 5 mins to evit api abuse

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

moderators = [356456393491873795, 549647456837828650]

rules = {
    '_main': ['Be civil and follow Discord ToS and guidelines.',
              'Absolutely no NSFW in here - this is a SFW channel.',
              'Don\'t be a dick and harass others, be a nice fellow to everyone.',
              'Don\'t cause drama, we like to keep things clean.',
              'Don\'t ask for punishments, unless you want to be restricted.',
              'Server and global moderators have the final say, don\'t argue unless there\'s a good reason to.',
              'These rules are not comprehensive - don\'t use loopholes or use "it wasn\'t in the rules" as an argument.'
              ],
    '_pr': ['Follow all main room rules.',
            'Only PRs in here - no comments allowed.'],
    '_prcomments': ['Follow all main room rules.',
                    'Don\'t make PRs in here - this is for comments only.'],
    '_liveries': ['Follow all main room rules.',
                  'Please keep things on topic and post liveries or comments on liveries only.']
    }

"""
def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature
"""

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession(loop=bot.loop)
    print("loading cogs...")
    bot.load_extension("cogs.admin")
    bot.load_extension("cogs.bridge")
    bot.load_extension("cogs.moderation")
    bot.load_extension("cogs.config")
    print("starting status thread...")
    status_thread = threading.Thread(target=random_status_thread)
    status_thread.start()
    print('ready hehe')
    

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return

    if message.content.startswith('u!') and not message.author.bot:
        return await bot.process_commands(message)

bot.run('token')
