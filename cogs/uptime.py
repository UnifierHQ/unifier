"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

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
from utils import log
import time
import datetime

class Uptime(commands.Cog, name=':stopwatch: Uptime'):
    """Uptime tracks the uptime of the bot.

    Developed by Green"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = log.buildlogger(
            self.bot.package, "uptime", self.bot.loglevel
        )
        if not hasattr(self.bot, "ut_total"):
            self.bot.ut_total = round(time.time())
        if not hasattr(self.bot, "ut_connected"):
            self.bot.ut_connected = 0
        if not hasattr(self.bot, "ut_conntime"):
            self.bot.ut_conntime = round(time.time())
        if not hasattr(self.bot, "ut_measuring"):
            self.bot.ut_measuring = True

    @commands.Cog.listener()
    async def on_connect(self):
        if not self.bot.ut_measuring:
            self.bot.ut_measuring = True
            self.bot.ut_conntime = round(time.time())

    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.bot.ut_measuring:
            self.bot.ut_connected += round(time.time()) - self.bot.ut_conntime
            self.bot.ut_measuring = False

    @commands.command()
    async def uptime(self, ctx):
        embed = discord.Embed(
            title=f'{self.bot.user.global_name} uptime',
            description=f'The bot has been up since <t:{self.bot.ut_total}:f>.',
            color=self.bot.colors.unifier
        )
        t = self.bot.ut_connected + round(time.time()) - self.bot.ut_conntime
        td = datetime.timedelta(seconds=t)
        d = td.days
        h, m, s = str(td).split(',')[len(str(td).split(','))-1].replace(' ','').split(':')
        tup = t
        embed.add_field(
            name='Total uptime',
            value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
            inline=False
        )
        t = self.bot.ut_connected + round(time.time()) - self.bot.ut_conntime
        td = datetime.timedelta(seconds=t)
        d = td.days
        h, m, s = str(td).split(',')[len(str(td).split(','))-1].replace(' ','').split(':')
        embed.add_field(
            name='Connected uptime',
            value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
            inline=False
        )
        embed.add_field(
            name='Connected uptime %',
            value=f'{round((t/tup)*100,2)}%',
            inline=False
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Uptime(bot))
