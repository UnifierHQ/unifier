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
from nextcord.ext import commands
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
        if not hasattr(self.bot, "disconnects"):
            self.bot.disconnects = 0

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.bot.disconnects += 1

    @commands.command(description='Shows bot uptime.')
    async def uptime(self, ctx):
        embed = nextcord.Embed(
            title=f'{self.bot.user.global_name} uptime',
            description=f'The bot has been up since <t:{self.bot.ut_total}:f>.',
            color=self.bot.colors.unifier
        )
        t = round(time.time()) - self.bot.ut_total
        td = datetime.timedelta(seconds=t)
        d = td.days
        h, m, s = str(td).split(',')[len(str(td).split(','))-1].replace(' ','').split(':')
        embed.add_field(
            name='Total uptime',
            value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
            inline=False
        )
        embed.add_field(
            name='Disconnects/hr',
            value=f'{round(self.bot.disconnects/(t/3600),2)}',
            inline=False
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Uptime(bot))
