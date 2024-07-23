"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

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

from nextcord.ext import commands

class Restrictions:
    def __init__(self, bot=None):
        self.__bot = bot
        self.__attached = (not bot is None)

    @property
    def attached(self):
        return self.__attached

    def attach_bot(self, bot):
        if self.__bot:
            raise ValueError('Bot already attached')
        self.__bot = bot
        self.__attached = True

    def owner(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def admin(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id in self.__bot.admins or ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def moderator(self):
        async def predicate(ctx: commands.Context):
            return ctx.author.id in self.__bot.moderators or ctx.author.id in self.__bot.admins or ctx.author.id == self.__bot.config['owner']

        return commands.check(predicate)

    def demo_error(self):
        """A demo check which will always fail, intended for development use only."""

        async def predicate(_ctx: commands.Context):
            return False

        return commands.check(predicate)
