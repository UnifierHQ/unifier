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
from nextcord.ext import commands, application_checks
import traceback
import re
from utils import log, ui, langmgr, restrictions as r, restrictions_legacy as r_legacy, slash as slash_helper
from typing import Optional
import emoji as pymoji
import time

restrictions = r.Restrictions()
restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_helper.SlashHelper(language)

def timetoint(t):
    try:
        return int(t)
    except:
        pass
    if not type(t) is str:
        t = str(t)
    total = 0
    if t.count('d')>1 or t.count('w')>1 or t.count('h')>1 or t.count('m')>1 or t.count('s')>1:
        raise ValueError('each identifier should never recur')
    t = t.replace('n','n ').replace('d','d ').replace('w','w ').replace('h','h ').replace('m','m ').replace('s','s ')
    times = t.split()
    for part in times:
        if part.endswith('d'):
            multi = int(part[:-1])
            total += (86400 * multi)
        elif part.endswith('w'):
            multi = int(part[:-1])
            total += (604800 * multi)
        elif part.endswith('h'):
            multi = int(part[:-1])
            total += (3600 * multi)
        elif part.endswith('m'):
            multi = int(part[:-1])
            total += (60 * multi)
        elif part.endswith('s'):
            multi = int(part[:-1])
            total += multi
        else:
            raise ValueError('invalid identifier')
    return total

class Config(commands.Cog, name=':construction_worker: Config'):
    """Config is an extension that lets Unifier admins configure the bot and server moderators set up Unified Chat in their server.

    Developed by Green and ItsAsheer"""

    def __init__(self,bot):
        global language
        self.bot = bot
        if not hasattr(self.bot, 'bridged_emojis'):
            if not 'emojis' in list(self.bot.db.keys()):
                self.bot.db.update({'emojis':[]})
                self.bot.db.save_data()
            self.bot.bridged_emojis = self.bot.db['emojis']
        if not hasattr(self.bot, 'trusted_group'):
            self.bot.trusted_group = self.bot.db['trusted']
        restrictions.attach_bot(self.bot)
        restrictions_legacy.attach_bot(self.bot)
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)
        language = self.bot.langmgr

    def can_manage(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                room = self.bot.bridge.get_invite(room)['room']
            except:
                return False

        __roominfo = self.bot.bridge.get_room(room)
        if not __roominfo:
            return False

        is_server = str(user.guild.id) == __roominfo['meta']['private_meta']['server']
        is_moderator = user.id in self.bot.moderators
        is_admin = user.id in self.bot.admins
        is_owner = user.id == self.bot.owner or user.id in self.bot.other_owners

        if __roominfo['meta']['private']:
            return (
                    user.guild_permissions.manage_channels and is_server
            ) or ((is_moderator and self.bot.config['private_rooms_mod_access']) or is_admin or is_owner)
        else:
            return is_admin or is_owner

    def can_join(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                self.bot.bridge.get_invite(room)
                return True
            except:
                return False

        __roominfo = self.bot.bridge.get_room(room)
        if not __roominfo:
            return False

        is_server = str(user.guild.id) == __roominfo['meta']['private_meta']['server']
        is_allowed = user.guild.id in __roominfo['meta']['private_meta']['allowed']

        if __roominfo['meta']['private']:
            return is_server or is_allowed
        else:
            return True

    def is_user_admin(self,user_id):
        try:
            if user_id in self.bot.config['admin_ids']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def is_room_restricted(self, room, db):
        try:
            if db['rooms'][room]['meta']['restricted']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def is_room_locked(self, room, db):
        try:
            if db['rooms'][room]['meta']['locked']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    async def room_manage_private_autocomplete(self, room, user):
        # Usually I'd add this to a util or something to share it with other cogs,
        # but I'm not feeling like that right now...maybe next patch?
        possible = []
        for roomname in self.bot.bridge.rooms:
            roominfo = self.bot.bridge.get_room(roomname)
            if not roominfo['meta']['private']:
                continue
            if self.bot.bridge.can_manage_room(roomname, user) and roomname.startswith(room):
                possible.append(roomname)

        return possible

    @nextcord.slash_command(
        contexts=[nextcord.InteractionContextType.guild],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def config(self, ctx):
        pass

    @commands.command(hidden=True,description='Adds a moderator to the instance.')
    @restrictions_legacy.admin()
    async def addmod(self,ctx,*,userid):
        selector = language.get_selector(ctx)
        discord_hint = True
        userid = userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)
        try:
            userid = int(userid)
        except:
            discord_hint = False
        
        username = None
        discriminator = None
        is_bot = False
        if discord_hint:
            user = self.bot.get_user(userid)
            username = user.name
            discriminator = user.discriminator if not user.discriminator == '0' else None
            is_bot = user.bot
        else:
            for platform in self.bot.platforms.keys():
                support = self.bot.platforms[platform]
                try:
                    user = support.get_user(userid)
                except:
                    continue
                username = support.user_name(user)
                is_bot = support.is_bot(user)
                break
                    
        if not username:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        if userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_mod")}')
        if self.is_user_admin(userid) or is_bot:
            return await ctx.send(selector.get("self_target"))
        self.bot.db['moderators'].append(userid)
        self.bot.moderators.append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{username}#{discriminator}'
        if not discriminator:
            mod = f'@{username}'
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"mod":mod})}')

    @commands.command(hidden=True,aliases=['remmod','delmod'],description='Removes a moderator from the instance.')
    @restrictions_legacy.admin()
    async def removemod(self,ctx,*,userid):
        selector = language.get_selector(ctx)
        discord_hint = True
        userid = userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)
        try:
            userid = int(userid)
        except:
            discord_hint = False

        username = None
        discriminator = None
        if discord_hint:
            user = self.bot.get_user(userid)
            username = user.name
            discriminator = user.discriminator if not user.discriminator == '0' else None
        else:
            for platform in self.bot.platforms.keys():
                support = self.bot.platforms[platform]
                try:
                    user = support.get_user(userid)
                    username = support.user_name(user)
                except:
                    continue
                break

        if not username:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid","config.addmod")}')
        if not userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_mod")}')
        if self.is_user_admin(userid):
            return await ctx.send(selector.rawget("self_target","config.addmod"))
        self.bot.db['moderators'].remove(userid)
        self.bot.moderators.remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{username}#{discriminator}'
        if not discriminator:
            mod = f'@{username}'
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"mod":mod})}')

    @config.subcommand(
        name='create-invite',
        description=language.desc('config.create-invite'),
        description_localizations=language.slash_desc('config.create-invite')
    )
    @restrictions.not_banned()
    async def create_invite(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.create-invite.room'),
            expiry: Optional[str] = slash.option('config.create-invite.expiry',required=False),
            max_usage: Optional[int] = slash.option('config.create-invite.max-usage', required=False)
    ):
        if not expiry:
            expiry = '7d'
        if not max_usage:
            max_usage = 0
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if len(self.bot.db['rooms'][room]['meta']['private_meta']['invites']) >= 20:
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.get("invites_limit")}',
                ephemeral=True
            )

        infinite_enabled = ''
        if self.bot.config['permanent_invites']:
            infinite_enabled = ' ' + selector.get("permanent")

        if expiry == 'inf':
            if not self.bot.config['permanent_invites']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("permanent_disabled")}',ephemeral=True)
            expiry = 0
        else:
            try:
                expiry = timetoint(expiry)
            except:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.rawget("invalid_duration","commons.moderation")}',
                    ephemeral=True
                )
            if expiry > 604800:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("duration_toolong")}{infinite_enabled}',
                    ephemeral=True
                )
            expiry += time.time()
        invite = self.bot.bridge.create_invite(room, max_usage, expiry)
        try:
            await ctx.user.send(
                f'{selector.get("code")} `{invite}`\n{selector.fget("join",values={"prefix":self.bot.command_prefix,"invite":invite})}'
            )
        except:
            return await ctx.send(f'{self.bot.ui_emojis.warning} {selector.fget("dm_fail",values={"prefix":self.bot.command_prefix})}',ephemeral=True)
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}',ephemeral=True)

    @config.subcommand(
        name='delete-invite',
        description=language.desc('config.delete-invite'),
        description_localizations=language.slash_desc('config.delete-invite')
    )
    @restrictions.not_banned()
    async def delete_invite(
            self, ctx: nextcord.Interaction,
            invite: str = slash.option('config.delete-invite.invite')
    ):
        invite = invite.lower()
        if not self.bot.bridge.can_manage_room(invite, ctx.user):
            raise restrictions.NoRoomManagement()
        selector = language.get_selector(ctx)
        try:
            self.bot.bridge.delete_invite(invite)
        except self.bot.bridge.InviteNotFoundError:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}',ephemeral=True)
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}',ephemeral=True)

    @config.subcommand(
        description=language.desc('config.invites'),
        description_localizations=language.slash_desc('config.invites')
    )
    @restrictions.not_banned()
    async def invites(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.invites.room')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("is_public","config.create-invite")}',ephemeral=True)

        invites = self.bot.db['rooms'][room]['meta']['private_meta']['invites']

        embed = nextcord.Embed(
            title=f'Invites for `{room}`',
        )

        success = 0
        for invite in invites:
            invite_data = self.bot.bridge.get_invite(invite)
            if not invite_data:
                continue
            embed.add_field(
                name=f'`{invite}`',
                value=(
                    selector.get("unlimited") if invite_data['remaining'] == 0 else
                    f'{selector.get("remaining")} {invite_data["remaining"]}'
                )+f'\n{selector.get("expiry")} '+(
                    selector.get("never") if invite_data["expire"] == 0 else f'<t:{round(invite_data["expire"])}:R>'
                )
            )
            success += 1

        embed.description = selector.fget("created",values={"created":success,"limit":20})
        try:
            await ctx.user.send(embed=embed)
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("dm_fail")}',ephemeral=True)
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}',ephemeral=True)

    @invites.on_autocomplete("room")
    async def unbind_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_manage_private_autocomplete(room, ctx.guild))

    @commands.command(description=language.desc('config.rename'))
    @restrictions_legacy.admin()
    @restrictions_legacy.not_banned()
    async def rename(self, ctx, room, newroom):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.author):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        newroom = newroom.lower()
        if not bool(re.match("^[A-Za-z0-9_-]*$", newroom)):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("alphanumeric","config.make")}')
        if newroom in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exists")}')
        if self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_private")}')
        self.bot.db['rooms'].update({newroom: self.bot.db['rooms'][room]})
        self.bot.db['rooms'].pop(room)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}\n`{room}` => `{newroom}`')

    @config.subcommand(
        name='display-name',
        description=language.desc('config.display-name'),
        description_localizations=language.slash_desc('config.display-name')
    )
    @restrictions.not_banned()
    async def display_name(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.display-name.room'),
            name: Optional[str] = slash.option('config.display-name.display-name',required=False)
    ):
        if not name:
            name = ''
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        current_name = str(self.bot.db['rooms'][room]['meta']['display_name'])

        if len(name) == 0:
            if not self.bot.db['rooms'][room]['meta']['display_name']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_name")}')
            self.bot.db['rooms'][room]['meta']['display_name'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        elif len(name) > 32:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("toolong")}')
        self.bot.db['rooms'][room]['meta']['display_name'] = name
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}\n`{current_name}` => `{name}`')

    @config.subcommand(
        description=language.desc('config.roomdesc'),
        description_localizations=language.slash_desc('config.roomdesc')
    )
    @restrictions.not_banned()
    async def roomdesc(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.roomdesc.room'),
            desc: Optional[str] = slash.option('config.roomdesc.description', required=False)
    ):
        if not desc:
            desc = ''
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(desc)==0:
            if not self.bot.db['rooms'][room]['meta']['description']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_desc")}')
            self.bot.db['rooms'][room]['meta']['description'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        self.bot.db['rooms'][room]['meta']['description'] = desc
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @config.subcommand(
        description=language.desc('config.roomemoji'),
        description_localizations=language.slash_desc('config.roomemoji')
    )
    @restrictions.not_banned()
    async def roomemoji(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.roomemoji.room'),
            emoji: Optional[str] = slash.option('config.roomemoji.emoji', required=False)
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(emoji) == 0:
            if not self.bot.db['rooms'][room]['meta']['emoji']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_emoji")}')
            self.bot.db['rooms'][room]['meta']['emoji'] = None
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("removed")}')
        if not pymoji.is_emoji(emoji):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_emoji")}')
        self.bot.db['rooms'][room]['meta']['emoji'] = emoji
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(selector.get("success"))

    @commands.command(
        hidden=True,
        description='Restricts/unrestricts a room. Only admins will be able to collect to this room when restricted.'
    )
    @restrictions_legacy.admin()
    async def restrict(self,ctx,room=None):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_private")}')
        if self.bot.db['rooms'][room]['meta']['restricted']:
            self.bot.db['rooms'][room]['meta']['restricted'] = False
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['restricted'] = True
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')

    @config.subcommand(
        description=language.desc('config.lock'),
        description_localizations=language.slash_desc('config.lock')
    )
    @restrictions.moderator()
    async def lock(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('config.lock.room', required=False)
    ):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                raise restrictions.UnknownRoom()

        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private'] and not ctx.user.id in self.bot.admins:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if self.bot.db['rooms'][room]['meta']['locked']:
            self.bot.db['rooms'][room]['meta']['locked'] = False
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['locked'] = True
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(description='Maps channels to rooms in bulk.', aliases=['autobind'])
    @restrictions_legacy.admin()
    @restrictions_legacy.no_admin_perms()
    async def map(self, ctx):
        channels = []
        channels_enabled = []
        namelist = []

        selector = language.get_selector(ctx)

        # get using async because this property may take a while to get if there's lots of rooms
        public_rooms = await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.public_rooms)

        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.loading} {selector.get("map_title")}',
                               description=selector.get("check_body"),
                               color=self.bot.colors.warning)
        msg = await ctx.send(embed=embed)
        hooks = await ctx.guild.webhooks()
        for channel in ctx.guild.text_channels:
            duplicate = False
            for roomname in list(public_rooms):
                # Prevent duplicate binding
                try:
                    hook_id = self.bot.bridge.get_room(roomname)['discord'][f'{ctx.guild.id}'][0]
                except:
                    continue
                for hook in hooks:
                    if hook.id == hook_id and hook.channel_id==channel.id:
                        duplicate = True
                        break
            if duplicate:
                continue
            roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
            if len(roomname) < 3:
                roomname = str(channel.id)
            if roomname in namelist:
                continue
            namelist.append(roomname)
            try:
                if len(self.bot.db['rooms'][roomname]['discord'][f'{ctx.guild.id}']) >= 1:
                    continue
            except:
                pass
            perms = channel.permissions_for(ctx.guild.me)
            if perms.manage_webhooks and perms.send_messages and perms.read_messages and perms.read_message_history:
                channels.append(channel)
                if len(channels_enabled) < 10:
                    channels_enabled.append(channel)
            if len(channels) >= 25:
                break

        interaction = None
        restricted = False
        locked = False
        while True:
            text = ''
            for channel in channels_enabled:
                roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
                if len(roomname) < 3:
                    roomname = str(channel.id)
                if text=='':
                    text = f'#{channel.name} ==> **{roomname}**' + (
                        ' (__New__)' if not roomname in self.bot.db['rooms'].keys() else '')
                else:
                    text = f'{text}\n#{channel.name} ==> **{roomname}**' + (
                        ' (__New__)' if not roomname in self.bot.db['rooms'].keys() else '')
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.rooms} {selector.get("map_title")}',
                description=f'{selector.get("map_body")}\n\n{text}',
                color=self.bot.colors.unifier
            )

            view = ui.MessageComponents()
            selection = nextcord.ui.StringSelect(
                max_values=10 if len(channels) > 10 else len(channels),
                placeholder=selector.get("selection_ch"),
                custom_id='selection'
            )

            for channel in channels:
                selection.add_option(
                    label=f'#{channel.name}',
                    value=str(channel.id),
                    default=channel in channels_enabled
                )

            view.add_rows(
                ui.ActionRow(
                    selection
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.get("selectall_over10") if len(channels) > 10 else selector.get("selectall"),
                        custom_id='selectall'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.get("deselect"),
                        custom_id='deselect'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label=selector.get("bind"),
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=selector.get("bind_restricted"),
                        custom_id='bind_restricted'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=selector.get("bind_locked"),
                        custom_id='bind_locked'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.rawget("cancel","commons.navigation"),
                        custom_id='cancel'
                    )
                ) if ctx.author.id in self.bot.admins else ui.ActionRow(
                    # we don't support non-admins mapping yet, but in case we do
                    # then making rooms should not be allowed
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label=selector.get("bind"),
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=selector.rawget("cancel","commons.navigation"),
                        custom_id='cancel'
                    )
                )
            )

            if interaction:
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await msg.edit(embed=embed, view=view)

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
                if interaction.data['custom_id']=='cancel':
                    raise RuntimeError()
            except:
                return await msg.edit(view=ui.MessageComponents())

            if interaction.data['custom_id'].startswith('bind'):
                embed.title = embed.title.replace(self.bot.ui_emojis.rooms, self.bot.ui_emojis.loading, 1)
                await msg.edit(embed=embed, view=ui.MessageComponents())
                await interaction.response.defer(with_message=True)
                if 'restricted' in interaction.data['custom_id']:
                    restricted = True
                elif 'locked' in interaction.data['custom_id']:
                    locked = True
                break
            elif interaction.data['custom_id']=='selection':
                channels_enabled = []
                for value in interaction.data['values']:
                    channel = self.bot.get_channel(int(value))
                    channels_enabled.append(channel)
            elif interaction.data['custom_id']=='selectall':
                channels_enabled = []
                for channel in channels:
                    channels_enabled.append(channel)
                    if len(channels_enabled) >= 10:
                        break
            elif interaction.data['custom_id'] == 'deselect':
                channels_enabled = []

        for channel in channels_enabled:
            roomname = re.sub(r'[^a-zA-Z0-9_-]', '', channel.name).lower()
            if len(roomname) < 3:
                roomname = str(channel.id)
            if not roomname in self.bot.db['rooms'].keys():
                self.bot.bridge.create_room(roomname)
                if restricted:
                    self.bot.db['rooms'][roomname]['meta']['restricted'] = True
                elif locked:
                    self.bot.db['rooms'][roomname]['meta']['locked'] = True
            webhook = await channel.create_webhook(name='Unifier Bridge')
            await self.bot.bridge.join_room(ctx.author,roomname,ctx.channel.id,webhook_id=webhook.id)

        embed.title = f'{self.bot.ui_emojis.success} {selector.get("success")}'
        embed.colour = self.bot.colors.success
        await msg.edit(embed=embed)

        await interaction.edit_original_message(
            content=f'{self.bot.ui_emojis.success} {selector.get("say_hi")}')

    @config.subcommand(
        name='add-rule',
        description=language.desc('config.add-rule'),
        description_localizations=language.slash_desc('config.add-rule')
    )
    @restrictions.not_banned()
    async def addrule(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.add-rule.room'),
            rule: str = slash.option('config.add-rule.rule')
    ):
        __room = room.lower()
        if not __room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(__room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(self.bot.db['rooms'][__room]['meta']['rules']) >= 25:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exceed")}')
        self.bot.db['rooms'][__room]['meta']['rules'].append(rule)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @config.subcommand(
        name='delete-rule',
        description=language.desc('config.delete-rule'),
        description_localizations=language.slash_desc('config.delete-rule')
    )
    @restrictions.not_banned()
    async def delrule(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('config.delete-rule.room'),
            rule: int = slash.option('config.delete-rule.rule')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        try:
            rule = int(rule)
            if rule <= 0:
                raise ValueError()
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        self.bot.db['rooms'][room]['meta']['rules'].pop(rule-1)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @commands.command(hidden=True,description="Allows given user's webhooks to be bridged.")
    @restrictions_legacy.admin()
    async def addbridge(self,ctx,*,userid):
        selector = language.get_selector(ctx)

        try:
            userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            user = self.bot.get_user(userid)
            if not user or userid==self.bot.user.id:
                raise ValueError()
            if userid in self.bot.db['external_bridge']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_exists")}')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user","commons.moderation")}')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.fget("allow_title",values={"username":user.name})}',
            description=selector.get("allow_body"),
            color=self.bot.colors.warning
        )
        components = ui.MessageComponents()
        components.add_rows(
            ui.ActionRow(
                nextcord.ui.Button(label=selector.get("accept"),style=nextcord.ButtonStyle.green,custom_id='allow'),
                nextcord.ui.Button(label=selector.rawget("cancel","commons.navigation"),style=nextcord.ButtonStyle.gray)
            )
        )
        msg = await ctx.send(embed=embed,view=components)

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=30.0)
        except:
            return await msg.edit(view=None)
        await interaction.response.edit_message(view=None)
        if not interaction.data['custom_id']=='allow':
            return
        self.bot.db['external_bridge'].append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        return await ctx.send(f'# {self.bot.ui_emojis.success} {selector.get("success_title")}\n{selector.get("success_body")}')

    @commands.command(hidden=True,description='Prevents given user\'s webhooks from being bridged.')
    @restrictions_legacy.admin()
    async def delbridge(self, ctx, *, userid):
        selector = language.get_selector(ctx)
        try:
            userid = int(userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
            user = self.bot.get_user(userid)
            if not user:
                raise ValueError()
            if not userid in self.bot.db['external_bridge']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_whitelist")}')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user!')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.fget("remove_title",values={"username":user.name})}',
            description=selector.get("remove_body"),
            color=self.bot.colors.warning
        )
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(label=selector.get("accept"), style=nextcord.ButtonStyle.red, custom_id='allow'),
                nextcord.ui.Button(label=selector.rawget("cancel","commons.navigation"), style=nextcord.ButtonStyle.gray)
            )
        )
        msg = await ctx.send(embed=embed, view=components)

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=30.0)
        except:
            return await msg.edit(view=None)
        await interaction.response.edit_message(view=None)
        if not interaction.data['custom_id'] == 'allow':
            return
        self.bot.db['external_bridge'].remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        return await ctx.send(f'# {self.bot.ui_emojis.success} {selector.get("success_title")}\n{selector.get("success_body")}')

    @config.subcommand(
        name='toggle-emoji',
        description=language.desc('config.toggle-emoji'),
        description_localizations=language.slash_desc('config.toggle-emoji')
    )
    @application_checks.has_permissions(manage_guild=True)
    async def toggle_emoji(self,ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')
        self.bot.db['emojis'] = self.bot.bridged_emojis
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Config(bot))
