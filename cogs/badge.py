import discord
from discord.ext import commands
import aiofiles
import inspect
import textwrap
from contextlib import redirect_stdout
import cpuinfo
import time

if hasattr(self.bot, 'colors'):
    colors = self.bot.colors
else:
    time.sleep(3) # wait for admin to set colors
    colors = self.bot.colors

class Badge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def badge(self, ctx):
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
