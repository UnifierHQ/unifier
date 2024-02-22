import discord
from discord.ext import commands
import time
import json

with open('config.json', 'r') as file:
    data = json.load(file)

owner = data['owner']

class Badge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def badge(self, ctx):
        user = "user"
        if ctx.author.id in self.bot.db['banned']:
            user = "banned"
        if ctx.author.id in self.bot.moderators:
            user = "moderator"
        if ctx.author.id in self.bot.admins:
            user = "admin"
        if ctx.author.id == owner:
            user = "owner"
        if user == "owner":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **owner**.",
                color=self.bot.colors.greens_hair  # You can change the color to your preference
            )
        elif user == "admin":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **admin**.",
                color=self.bot.colors.green  # You can change the color to your preference
            )
        elif user == "moderator":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **moderator**.",
                color=self.bot.colors.purple  # You can change the color to your preference
            )
        elif user == "banned":
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **banned user**.",
                color=self.bot.colors.red  # You can change the color to your preference
            )
            embed.set_footer(text="L bozo") # :nevheh:
        else:
            embed = discord.Embed(
                title="Unifier",
                description=f"<@{ctx.author.id}> is a Unifier **user**.",
                color=self.bot.colors.blurple  # You can change the color to your preference
            )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Badge(bot))
