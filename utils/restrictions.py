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

    class NoRoomManagement(commands.CheckFailure):
        pass

    class NoRoomJoin(commands.CheckFailure):
        pass

    class UnknownRoom(commands.CheckFailure):
        pass

    class AlreadyConnected(commands.CheckFailure):
        pass

    class NotConnected(commands.CheckFailure):
        pass

    class GlobalBanned(commands.CheckFailure):
        pass

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

    def can_create(self):
        async def predicate(ctx: commands.Context):
            return (
                ctx.author.id in self.__bot.admins or ctx.author.id == self.__bot.config['owner']
            ) or ctx.author.guild_permissions.manage_channels

        return commands.check(predicate)

    def join_room(self):
        async def predicate(ctx: commands.Context):
            index = 0

            # the below is to be used if we ever make a command
            # that has the room arg not in position 0
            # if ctx.command.qualified_name == "name":
            #     index = 1

            room = ctx.args[index].lower()

            if ctx.command.qualified_name == 'bind' and self.__bot.bridge.get_invite(room):
                return True

            if not room in self.__bot.bridge.rooms:
                raise self.UnknownRoom('The room does not exist.')

            if self.__bot.bridge.can_join_room(room, ctx.author):
                return True

            raise self.NoRoomJoin('You do not have permissions to join this room.')

        return commands.check(predicate)

    def manage_room(self):
        async def predicate(ctx: commands.Context):
            index = 0

            # the below is to be used if we ever make a command
            # that has the room arg not in position 0
            # if ctx.command.qualified_name == "name":
            #     index = 1

            room = ctx.args[index].lower()

            if not room in self.__bot.bridge.rooms:
                raise self.UnknownRoom('The room does not exist.')

            # this should not fail, but if it does check will fail
            if self.__bot.bridge.can_manage_room(room, ctx.author):
                return ctx.author.guild_permissions.manage_channels

            raise self.NoRoomManagement('You do not have permissions to manage this room.')

        return commands.check(predicate)

    def not_connected(self):
        async def predicate(ctx: commands.Context):
            index = 0

            # the below is to be used if we ever make a command
            # that has the room arg not in position 0
            # if ctx.command.qualified_name == "name":
            #     index = 1

            room = ctx.args[index].lower()

            if ctx.command.qualified_name == 'bind' and self.__bot.bridge.get_invite(room):
                return True

            if not room in self.__bot.bridge.rooms:
                raise self.UnknownRoom('The room does not exist.')

            roominfo = self.__bot.bridge.get_room(room)

            # assume no servers are connected if discord isn't a key
            if 'discord' in roominfo.keys():
                if str(ctx.guild.id) in roominfo['discord'].keys():
                    raise self.AlreadyConnected('You are already connected to this room.')

            return True

        return commands.check(predicate)

    def is_connected(self):
        # basically not_connected but inverted

        async def predicate(ctx: commands.Context):
            index = 0

            # the below is to be used if we ever make a command
            # that has the room arg not in position 0
            # if ctx.command.qualified_name == "name":
            #     index = 1

            room = ctx.args[index].lower()

            if not room in self.__bot.bridge.rooms:
                raise self.UnknownRoom('The room does not exist.')

            roominfo = self.__bot.bridge.get_room(room)

            # assume no servers are connected if discord isn't a key
            if 'discord' in roominfo.keys():
                if str(ctx.guild.id) in roominfo['discord'].keys():
                    return True

            raise self.NotConnected('You are not connected to this room.')

        return commands.check(predicate)

    def not_banned(self):
        async def predicate(ctx: commands.Context):
            if (
                    f'{ctx.author.id}' in self.__bot.db['banned'].keys() or
                    f'{ctx.guild.id}' in self.__bot.db['banned'].keys()
            ):
                raise self.GlobalBanned('You are global banned.')

        return commands.check(predicate)

    def not_banned_user(self):
        async def predicate(ctx: commands.Context):
            if f'{ctx.author.id}' in self.__bot.db['banned'].keys():
                raise self.GlobalBanned('You are global banned.')

        return commands.check(predicate)

    def not_banned_guild(self):
        async def predicate(ctx: commands.Context):
            if f'{ctx.guild.id}' in self.__bot.db['banned'].keys():
                raise self.GlobalBanned('You are global banned.')

        return commands.check(predicate)

    def demo_error(self):
        """A demo check which will always fail, intended for development use only."""

        async def predicate(_ctx: commands.Context):
            return False

        return commands.check(predicate)
