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

import nextcord
from nextcord.ext import application_checks

class Restrictions:
    def __init__(self, bot=None):
        self.__bot = bot
        self.__attached = (not bot is None)

    class NoRoomManagement(nextcord.ApplicationCheckFailure):
        pass

    class NoRoomModeration(nextcord.ApplicationCheckFailure):
        pass

    class NoRoomJoin(nextcord.ApplicationCheckFailure):
        pass

    class UnknownRoom(nextcord.ApplicationCheckFailure):
        pass

    class AlreadyConnected(nextcord.ApplicationCheckFailure):
        pass

    class NotConnected(nextcord.ApplicationCheckFailure):
        pass

    class GlobalBanned(nextcord.ApplicationCheckFailure):
        pass

    class UnderAttack(nextcord.ApplicationCheckFailure):
        pass

    class CustomMissingArgument(nextcord.ApplicationCheckFailure):
        pass

    class TooManyPermissions(nextcord.ApplicationCheckFailure):
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
        async def predicate(interaction: nextcord.Interaction):
            return interaction.user.id == self.__bot.config['owner'] or interaction.user.id in self.__bot.config['other_owners']

        return application_checks.check(predicate)

    def admin(self):
        async def predicate(interaction: nextcord.Interaction):
            return interaction.user.id in self.__bot.admins or interaction.user.id == self.__bot.config['owner']

        return application_checks.check(predicate)

    def moderator(self):
        async def predicate(interaction: nextcord.Interaction):
            return interaction.user.id in self.__bot.moderators or interaction.user.id in self.__bot.admins or interaction.user.id == self.__bot.config['owner']

        return application_checks.check(predicate)

    def can_create(self):
        async def predicate(interaction: nextcord.Interaction):
            return (
                interaction.user.id in self.__bot.admins or interaction.user.id == self.__bot.config['owner']
            ) or interaction.user.guild_permissions.manage_channels

        return application_checks.check(predicate)

    def not_banned(self):
        async def predicate(interaction: nextcord.Interaction):
            if (
                    f'{interaction.user.id}' in self.__bot.db['banned'].keys() or
                    f'{interaction.guild.id}' in self.__bot.db['banned'].keys()
            ):
                raise self.GlobalBanned('You are global banned.')
            elif f'{interaction.guild.id}' in self.__bot.db['underattack']:
                raise self.UnderAttack('The server is under attack.')
            return True

        return application_checks.check(predicate)

    def not_banned_user(self):
        async def predicate(interaction: nextcord.Interaction):
            if f'{interaction.user.id}' in self.__bot.db['banned'].keys():
                raise self.GlobalBanned('You are global banned.')
            return True

        return application_checks.check(predicate)

    def not_banned_guild(self):
        async def predicate(interaction: nextcord.Interaction):
            if f'{interaction.guild.id}' in self.__bot.db['banned'].keys():
                raise self.GlobalBanned('You are global banned.')
            elif f'{interaction.guild.id}' in self.__bot.db['underattack']:
                raise self.UnderAttack('This server is under attack.')
            return True

        return application_checks.check(predicate)

    def under_attack(self):
        async def predicate(interaction: nextcord.Interaction):
            if f'{interaction.guild.id}' in self.__bot.db['underattack']:
                return interaction.user.guild_permissions.manage_channels
            else:
                return interaction.user.guild_permissions.ban_members or interaction.user.guild_permissions.manage_channels

        return application_checks.check(predicate)

    def no_admin_perms(self):
        async def predicate(interaction: nextcord.Interaction):
            if interaction.guild.me.guild_permissions.administrator:
                raise self.TooManyPermissions('Administrator')
            return True

        return application_checks.check(predicate)

    def demo_error(self):
        """A demo check which will always fail, intended for development use only."""

        async def predicate(_interaction: nextcord.Interaction):
            return False

        return application_checks.check(predicate)
