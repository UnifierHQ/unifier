import discord
from discord.ext import commands
import aiohttp
import hashlib
bot = commands.Bot(command_prefix='u!',intents=discord.Intents.all())

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

moderators = [356456393491873795]

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
