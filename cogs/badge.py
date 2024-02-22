import discord
from discord.ext import commands
import aiofiles
import inspect
import textwrap
from contextlib import redirect_stdout
import cpuinfo
import time

class colors:
    default = 0
    teal = 0x1abc9c
    dark_teal = 0x11806a
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    blue = 0x3498db
    dark_blue = 0x206694
    purple = 0x9b59b6
    dark_purple = 0x71368a
    magenta = 0xe91e63
    dark_magenta = 0xad1457
    gold = 0xf1c40f
    dark_gold = 0xc27c0e
    orange = 0xe67e22
    dark_orange = 0xa84300
    red = 0xe74c3c
    dark_red = 0x992d22
    lighter_grey = 0x95a5a6
    dark_grey = 0x607d8b
    light_grey = 0x979c9f
    darker_grey = 0x546e7a
    blurple = 0x7289da
    greyple = 0x99aab5




class Badge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def badge(self, ctx):
        start = time.time()
        what = "user"
        if ctx.author.id in self.bot.db['banned']:
            user = "banned"
        if ctx.author.id in self.bot.moderators:
            user = "moderator"
        if ctx.author.id in self.bot.admins:
            user = "admin"
        if ctx.author.id == data['owner']:
            user = "owner"
        if what == "owner":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **owner**.",
                color=colors.dark_green  # You can change the color to your preference
            )
        elif what == "admin":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **admin**.",
                color=colors.green  # You can change the color to your preference
            )
        elif what == "moderator":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **moderator**.",
                color=colors.purple  # You can change the color to your preference
            )
        elif what == "user":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **user**.",
                color=colors.blurple  # You can change the color to your preference
            )
        elif what == "banned":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **banned user**.",
                color=colors.red  # You can change the color to your preference
            )
        end = time.time()
        duration_seconds = start - end
        embed.set_description(f"Operation took {duration_seconds} seconds.")
        await ctx.message.reply(embed=embed)

def setup(bot):
    bot.add_cog(Badge(bot))
