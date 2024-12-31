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
from nextcord.ext import commands
from typing import Optional
from utils import log, langmgr, restrictions_legacy as r_legacy, slash as slash_handler
from enum import Enum

restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_handler.SlashHelper(language)

class UserRole(Enum):
    # let values be None until set by langmgr
    OWNER = language.get('owner','badge.roles')
    ADMIN = language.get('admin','badge.roles')
    MODERATOR = language.get('moderator','badge.roles')
    TRUSTED = language.get('trusted','badge.roles')
    BANNED = language.get('banned','badge.roles')
    USER = language.get('user','badge.roles')

class Badge(commands.Cog, name=':medal: Badge'):
    """Badge contains commands that show you your role in Unifier."""

    def __init__(self, bot):
        global language
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'badge', self.bot.loglevel)
        language = self.bot.langmgr
        self.embed_colors = {
            UserRole.OWNER: (
                self.bot.colors.greens_hair if self.bot.user.id==1187093090415149056 else self.bot.colors.unifier
            ),
            UserRole.ADMIN: nextcord.Color.green(),
            UserRole.MODERATOR: nextcord.Color.purple(),
            UserRole.TRUSTED: self.bot.colors.gold,
            UserRole.BANNED: nextcord.Color.red(),
            UserRole.USER: nextcord.Color.blurple()
        }
        restrictions_legacy.attach_bot(self.bot)

    @nextcord.slash_command(
        description=language.desc('badge.badge'),
        description_localizations=language.slash_desc('badge.badge'),
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def badge(
            self, ctx: nextcord.Interaction,
            user: Optional[nextcord.User] = slash.option('badge.badge.user', required=False)
    ):
        selector = language.get_selector(ctx)
        if not user:
            user = ctx.user
        user_role = self.get_user_role(user.id)
        embed = nextcord.Embed(
            description=selector.fget("body", values={
                'mention':f"<@{user.id}>",'role': user_role.value
            }),
            color=self.embed_colors[user_role]
        )
        embed.set_author(
            name=f'@{user.name}',
            icon_url=user.avatar.url if user.avatar else None
        )
        if user_role==UserRole.BANNED:
            embed.set_footer(text=selector.get("easter_egg"))

        await ctx.send(embed=embed)

    @commands.command(hidden=True,aliases=['trust'],description=language.desc('badge.verify'))
    @restrictions_legacy.admin()
    async def verify(self, ctx, user: nextcord.User):
        selector = language.get_selector(ctx)

        if user.id in self.bot.trusted_group:
            return await ctx.send(f'{self.bot.ui_emojis.error} '+selector.fget("failed", values={'user': user.name}))

        self.bot.trusted_group.append(user.id)

        self.bot.db['trusted'] = self.bot.trusted_group
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

        await ctx.send(f'{self.bot.ui_emojis.success} '+selector.fget("success", values={'user': user.name}))

    @commands.command(hidden=True, aliases=['untrust'], description=language.desc('badge.unverify'))
    @restrictions_legacy.admin()
    async def unverify(self, ctx, user: nextcord.User):
        selector = language.get_selector(ctx)

        if not user.id in self.bot.trusted_group:
            return await ctx.send(f'{self.bot.ui_emojis.error} '+selector.fget("failed", values={'user': user.name}))

        self.bot.trusted_group.remove(user.id)

        self.bot.db['trusted'] = self.bot.trusted_group
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

        await ctx.send(f'{self.bot.ui_emojis.success} '+selector.fget("success", values={'user': user.name}))

    def get_user_role(self, user_id):
        if user_id == self.bot.owner or user_id in self.bot.other_owners:
            return UserRole.OWNER
        elif user_id in self.bot.admins:
            return UserRole.ADMIN
        elif user_id in self.bot.moderators:
            return UserRole.MODERATOR
        elif user_id in self.bot.trusted_group:
            return UserRole.TRUSTED
        elif str(user_id) in self.bot.db['banned']:
            return UserRole.BANNED
        else:
            return UserRole.USER

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

# Happy new 2025, leaving this as an easteregg, with love, ItsAsheer, green., summer., Lezetho, Arhan, Saphire, and arandomguy

# note from green to itsasheer:
# out of ALL FILES you couldve added the comment to, you chose badge.py...
# this is downright unacceptable. expect to see me in my totally real office next week
#
# (jokes aside happy new year)

# ItsAsheer -> green. : Its bc new update to badge.py soon :eyes:, and bc its not a critical feature (imagine i broke bridge.py. We could create an easter egg file where we leave comments :)

def setup(bot):
    bot.add_cog(Badge(bot))
