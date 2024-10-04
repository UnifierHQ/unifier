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
import traceback
import re
from utils import log, ui, langmgr, restrictions as r
import math
import random
import string
import emoji as pymoji
import time

restrictions = r.Restrictions()
language = langmgr.partial()
language.load()

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
        self.bot = bot
        if not hasattr(self.bot, 'bridged_emojis'):
            if not 'emojis' in list(self.bot.db.keys()):
                self.bot.db.update({'emojis':[]})
                self.bot.db.save_data()
            self.bot.bridged_emojis = self.bot.db['emojis']
        self.bot.admins = self.bot.config['admin_ids']
        self.bot.moderators = self.bot.admins + self.bot.db['moderators']
        if not hasattr(self.bot, 'trusted_group'):
            self.bot.trusted_group = self.bot.db['trusted']
        restrictions.attach_bot(self.bot)
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)
        language = self.bot.langmgr

    def can_manage(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                room = self.bot.bridge.get_invite(room)['room']
            except:
                return False

        roominfo = self.bot.bridge.get_room(room)
        if not roominfo:
            return False

        if roominfo['meta']['private']:
            return (
                    user.guild_permissions.manage_channels and user.guild.id == roominfo['meta']['private_meta']['server']
            ) or (
                    user.id in self.bot.moderators or
                    user.id in self.bot.admins or
                    user.id == self.bot.owner
            )
        else:
            return (
                    user.id in self.bot.admins or
                    user.id == self.bot.owner
            )

    def can_moderate(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                room = self.bot.bridge.get_invite(room)['room']
            except:
                return False

        roominfo = self.bot.bridge.get_room(room)
        if not roominfo:
            return False

        if roominfo['meta']['private']:
            return (
                    user.guild_permissions.ban_members and user.guild.id == roominfo['meta']['private_meta']['server']
            ) or (
                    user.id in self.bot.moderators or
                    user.id in self.bot.admins or
                    user.id == self.bot.owner
            )
        else:
            return (
                    user.id in self.bot.admins or
                    user.id == self.bot.owner
            )

    def can_join(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                self.bot.bridge.get_invite(room)
                return True
            except:
                return False

        roominfo = self.bot.bridge.get_room(room)
        if not roominfo:
            return False

        if roominfo['meta']['private']:
            return (
                    user.guild.id in roominfo['meta']['private_meta']['allowed'] or
                    user.guild.id == roominfo['meta']['private_meta']['server']
            )
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

    async def roomslist(self, ctx, private):
        selector = language.get_selector('config.rooms', userid=ctx.author.id)
        
        show_restricted = False
        show_locked = False

        if ctx.author.id in self.bot.admins:
            show_restricted = True
            show_locked = True
        elif ctx.author.id in self.bot.moderators:
            show_locked = True

        panel = 0
        limit = 8
        page = 0
        match = 0
        namematch = False
        descmatch = False
        was_searching = False
        roomname = ''
        query = ''
        msg = None
        interaction = None
        ignore_mod = True

        helptext = selector.fget("title", values={"botname": self.bot.user.global_name or self.bot.user.name})
        
        if private:
            helptext = selector.fget("title_private", values={"botname": self.bot.user.global_name or self.bot.user.name})

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel == 0:
                was_searching = False
                search_roomlist = self.bot.bridge.rooms
                roomlist = []
                for search_room in search_roomlist:
                    # yes, this logic is messy.
                    # but it doesn't overwrite the origin server thing so i'm keeping it for now
                    if private:
                        if not self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not self.bot.bridge.can_access_room(search_room, ctx.author, ignore_mod=ignore_mod):
                            continue
                    else:
                        if self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not show_restricted and self.is_room_restricted(search_room, self.bot.db):
                            continue
                        elif not show_locked and self.is_room_locked(search_room, self.bot.db):
                            continue
                    roomlist.append(search_room)

                maxpage = math.ceil(len(roomlist) / limit) - 1
                if interaction:
                    if page > maxpage:
                        page = maxpage
                embed.title = f'{self.bot.ui_emojis.rooms} {helptext}'
                embed.description = selector.get("choose_room")
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room")
                )

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(roomlist):
                        break
                    try:
                        # redundant try-except block
                        name = roomlist[index]
                    except:
                        break
                    display_name = (
                            self.bot.db['rooms'][name]['meta']['display_name'] or name
                    )
                    description = (
                            self.bot.db['rooms'][name]['meta']['description'] or selector.get("no_desc")
                    )
                    emoji = (
                        '\U0001F527' if self.is_room_restricted(roomlist[index], self.bot.db) else
                        '\U0001F512' if self.is_room_locked(roomlist[index], self.bot.db) else
                        '\U0001F310'
                    ) if not self.bot.db['rooms'][name]['meta']['emoji'] else self.bot.db['rooms'][name]['meta'][
                        'emoji']

                    embed.add_field(
                        name=f'{emoji} '+(
                            f'{display_name} (`{name}`)' if self.bot.db['rooms'][name]['meta']['display_name'] else
                            f'`{display_name}`'
                        ),
                        value=description,
                        inline=False
                    )
                    selection.add_option(
                        label=display_name,
                        emoji=emoji,
                        description=description,
                        value=name
                    )

                if len(embed.fields) == 0:
                    embed.add_field(
                        name=selector.get("noresults_title"),
                        value=selector.get("noresults_body_room"),
                        inline=False
                    )
                    selection.add_option(
                        label='placeholder',
                        value='placeholder'
                    )
                    selection.disabled = True

                components.add_rows(
                    ui.ActionRow(
                        selection
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("prev","commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0 or selection.disabled,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next","commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage or selection.disabled,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget("search","commons.seacrh"),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search,
                            disabled=selection.disabled
                        )
                    )
                )

                if ctx.author.id in self.bot.moderators and private:
                    components.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label=selector.get("show_all") if ignore_mod else selector.get("hide_inaccessible"),
                                custom_id='viewall'
                            )
                        )
                    )
            elif panel == 1:
                was_searching = True
                search_roomlist = list(self.bot.db['rooms'].keys())

                def search_filter(query, query_cmd):
                    if match == 0:
                        return (
                                (
                                        query.lower() in (
                                            self.bot.db['rooms'][query_cmd]['meta']['display_name'] or query_cmd
                                        )
                                ) and namematch or
                                (
                                    query.lower() in self.bot.db['rooms'][query_cmd]['meta']['description'].lower()
                                    if self.bot.db['rooms'][query_cmd]['meta']['description'] else False
                                ) and descmatch
                        )
                    elif match == 1:
                        return (
                                (((
                                          query.lower() in (
                                              self.bot.db['rooms'][query_cmd]['meta']['display_name'] or query_cmd
                                          )
                                  ) and namematch) or not namematch) and
                                ((
                                     query.lower() in self.bot.db['rooms'][query_cmd]['meta']['description'].lower()
                                     if self.bot.db['rooms'][query_cmd]['meta']['description'] else False
                                 ) and descmatch or not descmatch)
                        )

                roomlist = []
                for search_room in search_roomlist:
                    # yes, this logic is messy.
                    # but it doesn't overwrite the origin server thing so i'm keeping it for now
                    if not search_filter(query,search_room):
                        continue
                    if private:
                        if not self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not self.bot.bridge.can_access_room(search_room, ctx.author, ignore_mod=ignore_mod):
                            continue
                    else:
                        if self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not show_restricted and self.is_room_restricted(search_room, self.bot.db):
                            continue
                        elif not show_locked and self.is_room_locked(search_room, self.bot.db):
                            continue
                    roomlist.append(search_room)

                embed.title = f'{self.bot.ui_emojis.rooms} {helptext} / search'
                embed.description = selector.get("choose_room")

                if len(roomlist) == 0:
                    maxpage = 0
                    embed.add_field(
                        name=selector.get("noresults_title"),
                        value=selector.get("noresults_body_search"),
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room"), disabled=True
                    )
                    selection.add_option(
                        label='No rooms'
                    )
                else:
                    maxpage = math.ceil(len(roomlist) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room")
                    )

                    roomlist = await self.bot.loop.run_in_executor(None, lambda: sorted(
                        roomlist,
                        key=lambda x: x.lower()
                    ))

                    for x in range(limit):
                        index = (page * limit) + x
                        if index >= len(roomlist):
                            break
                        room = roomlist[index]
                        display_name = (
                                self.bot.db['rooms'][room]['meta']['display_name'] or room
                        )
                        emoji = (
                            '\U0001F527' if self.is_room_restricted(roomlist[index], self.bot.db) else
                            '\U0001F512' if self.is_room_locked(roomlist[index], self.bot.db) else
                            '\U0001F310'
                        ) if not self.bot.db['rooms'][room]['meta']['emoji'] else self.bot.db['rooms'][room]['meta'][
                            'emoji']
                        roomdesc = (
                            self.bot.db['rooms'][room]['meta']['description']
                            if self.bot.db['rooms'][room]['meta']['description'] else selector.get("no_desc")
                        )
                        embed.add_field(
                            name=f'{emoji} ' + (
                                f'{display_name} (`{room}`)' if self.bot.db['rooms'][room]['meta']['display_name'] else
                                f'`{display_name}`'
                            ),
                            value=roomdesc,
                            inline=False
                        )
                        selection.add_option(
                            label=display_name,
                            description=roomdesc if len(roomdesc) <= 100 else roomdesc[:-(len(roomdesc) - 97)] + '...',
                            value=room,
                            emoji=emoji
                        )

                embed.description = selector.rawfget("search_results","commons.search",values={"query":query,"results":len(roomlist)})
                maxcount = (page + 1) * limit
                if maxcount > len(roomlist):
                    maxcount = len(roomlist)
                embed.set_footer(
                    text=(
                        selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1}) + ' | '+
                        selector.rawfget("result_count","commons.search",values={"lower": page * limit + 1, "upper": maxcount, "total": len(roomlist)})
                    )
                )

                components.add_row(
                    ui.ActionRow(
                        selection
                    )
                )

                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("prev","commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next","commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget("search","commons.search"),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search
                        )
                    )
                )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='match',
                            label=(
                                selector.rawget("match_any","commons.search") if match == 0 else
                                selector.rawget("match_both","commons.search")
                            ),
                            style=(
                                nextcord.ButtonStyle.green if match == 0 else
                                nextcord.ButtonStyle.blurple
                            ),
                            emoji=(
                                '\U00002194' if match == 0 else
                                '\U000023FA'
                            )
                        ),
                        nextcord.ui.Button(
                            custom_id='name',
                            label=selector.get("room_name"),
                            style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label=selector.get("room_desc"),
                            style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                        )
                    )
                )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back","commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 2:
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {helptext} / search / {roomname}'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {helptext} / {roomname}'
                )
                display_name = (
                        self.bot.db['rooms'][roomname]['meta']['display_name'] or roomname
                )
                description = (
                        self.bot.db['rooms'][roomname]['meta']['description'] or selector.get("no_desc")
                )
                emoji = (
                    '\U0001F527' if self.is_room_restricted(roomname, self.bot.db) else
                    '\U0001F512' if self.is_room_locked(roomname, self.bot.db) else
                    '\U0001F310'
                ) if not self.bot.db['rooms'][roomname]['meta']['emoji'] else self.bot.db['rooms'][roomname]['meta'][
                    'emoji']
                if self.bot.db['rooms'][roomname]['meta']['display_name']:
                    embed.description = f'# **{emoji} {display_name}**\n`{roomname}`\n\n{description}'
                else:
                    embed.description = f'# **{emoji} `{display_name}`**\n{description}'
                stats = await self.bot.bridge.roomstats(roomname)
                embed.add_field(name=selector.get("statistics"), value=(
                        f':homes: {selector.fget("servers",values={"count": stats["guilds"]})}\n' +
                        f':green_circle: {selector.fget("online", values={"count": stats["online"]})}, '+
                        f':busts_in_silhouette: {selector.fget("members", values={"count": stats["members"]})}\n' +
                        f':speech_balloon: {selector.fget("messages", values={"count": stats["messages"]})}'
                ))
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.get("view_rules"),
                            custom_id='rules',
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back","commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 3:
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {helptext} / {selector.rawget("search_nav","sysmgr.help")} / {roomname} / {selector.get("rules_nav")}'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {helptext} / {roomname} / {selector.get("rules_nav")}'
                )
                index = 0
                text = ''
                rules = self.bot.db['rooms'][roomname]['meta']['rules']
                for rule in rules:
                    if text == '':
                        text = f'1. {rule}'
                    else:
                        text = f'{text}\n{index}. {rule}'
                    index += 1
                if len(rules) == 0:
                    text = selector.get("no_rules")
                embed.description = text
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back","commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if panel == 0:
                embed.set_footer(text=selector.rawfget("page","commons.search",values={"page":page+1,"maxpage":maxpage+1}))
            if not msg:
                msg = await ctx.send(embed=embed, view=components, reference=ctx.message, mention_author=False)
            else:
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=components)
            embed.clear_fields()

            def check(interaction):
                return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
            except:
                try:
                    await msg.edit(view=None)
                except:
                    pass
                break
            if interaction.type == nextcord.InteractionType.component:
                if interaction.data['custom_id'] == 'selection':
                    roomname = interaction.data['values'][0]
                    panel = 2
                    page = 0
                elif interaction.data['custom_id'] == 'back':
                    panel -= 1
                    if panel < 0 or panel == 1 and not was_searching:
                        panel = 0
                    page = 0
                elif interaction.data['custom_id'] == 'rules':
                    panel += 1
                elif interaction.data['custom_id'] == 'prev':
                    page -= 1
                elif interaction.data['custom_id'] == 'next':
                    page += 1
                elif interaction.data['custom_id'] == 'search':
                    modal = nextcord.ui.Modal(title=selector.rawget("search_title","commons.search"), auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label=selector.rawget("query","commons.search"),
                            style=nextcord.TextInputStyle.short,
                            placeholder=selector.rawget("query_prompt","commons.search")
                        )
                    )
                    await interaction.response.send_modal(modal)
                elif interaction.data['custom_id'] == 'match':
                    match += 1
                    if match > 1:
                        match = 0
                elif interaction.data['custom_id'] == 'name':
                    namematch = not namematch
                    if not namematch and not descmatch:
                        namematch = True
                elif interaction.data['custom_id'] == 'desc':
                    descmatch = not descmatch
                    if not namematch and not descmatch:
                        descmatch = True
                elif interaction.data['custom_id'] == 'viewall':
                    ignore_mod = not ignore_mod
            elif interaction.type == nextcord.InteractionType.modal_submit:
                panel = 1
                query = interaction.data['components'][0]['components'][0]['value']
                namematch = True
                descmatch = True
                match = 0
                page = 0

    @commands.command(hidden=True,description='Adds a moderator to the instance.')
    @restrictions.admin()
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
    @restrictions.admin()
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

    @commands.command(hidden=True, aliases=['newroom'],description='Creates a new room.')
    @restrictions.can_create()
    @restrictions.not_banned()
    async def make(self,ctx,*,room=None):
        roomtype = 'private'
        dry_run = False
        
        selector = language.get_selector(ctx)

        if room:
            if room.startswith('-dry-run'):
                if room == '-dry-run':
                    room = None
                dry_run = ctx.author.id == self.bot.owner

        if room:
            room = room.lower().replace(' ','-')
            if not bool(re.match("^[A-Za-z0-9_-]*$", room)):
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("alphanumeric")}'
                )

        interaction = None
        if ctx.author.id in self.bot.admins or ctx.author.id == self.bot.config['owner']:
            if not self.bot.config['enable_private_rooms']:
                roomtype = 'public'
            else:
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.StringSelect(
                            options=[
                                nextcord.SelectOption(
                                    value='private',
                                    label=selector.get("private_name"),
                                    description=selector.get("private_desc"),
                                    emoji='\U0001F512'
                                ),
                                nextcord.SelectOption(
                                    value='public',
                                    label=selector.get("public_name"),
                                    description=selector.get("public_desc"),
                                    emoji='\U0001F310'
                                )
                            ],
                            custom_id='selection'
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("cancel","commons.navigation"),
                            custom_id='cancel'
                        )
                    )
                )
                msg = await ctx.send(f'{self.bot.ui_emojis.warning} {selector.get("select")}',view=components)

                def check(interaction):
                    return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

                try:
                    interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
                    if interaction.data['custom_id'] == 'cancel':
                        return await interaction.response.edit_message(
                            content=f'{self.bot.ui_emojis.error} {selector.rawget("aborted","commons.navigation")}', view=None
                        )
                    else:
                        roomtype = interaction.data['values'][0]
                except:
                    return await msg.edit(content=f'{self.bot.ui_emojis.error} {selector.rawget("timeout","commons.navigation")}', view=None)

        if not self.bot.config['enable_private_rooms'] and roomtype == 'private':
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("private_disabled")}')

        if not room or roomtype=='private':
            for _ in range(10):
                room = roomtype + '-' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                if not room in self.bot.bridge.rooms:
                    break
            if room in self.bot.bridge.rooms:
                if interaction:
                    return await interaction.response.edit_message(
                        content=f'{self.bot.ui_emojis.error} {selector.get("unique_fail")}'
                    )
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("unique_fail")}')

        if room in list(self.bot.db['rooms'].keys()):
            if interaction:
                return await interaction.response.edit_message(
                    content=f'{self.bot.ui_emojis.error} {selector.get("exists")}'
                )
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exists")}')
        try:
            roomdata = self.bot.bridge.create_room(
                room, private=roomtype=='private', dry_run=dry_run, origin=ctx.guild.id
            )
        except self.bot.bridge.TooManyRooms:
            if interaction:
                return await interaction.response.edit_message(
                    content=f'{self.bot.ui_emojis.error} {selector.fget("private_limit",values={"limit": self.bot.config["private_rooms_limit"]})}',
                    view=None
                )
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.fget("private_limit",values={"limit": self.bot.config["private_rooms_limit"]})}'
            )

        dry_run_text = ''
        if dry_run:
            dry_run_text = f'\n```js\n{roomdata}```\n-# {self.bot.ui_emojis.warning} {selector.get("dryrun_warning")}'

        roomtype_text = selector.get(roomtype+'_name')

        if interaction:
            return await interaction.response.edit_message(
                content=f'{self.bot.ui_emojis.success} {selector.fget("success",values={"roomtype":roomtype_text,"room":room})}{dry_run_text}',
                view=None
            )
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"roomtype":roomtype_text,"room":room})}{dry_run_text}')

    @commands.command(name='create-invite', hidden=True, description='Creates an invite.')
    @restrictions.not_banned()
    async def create_invite(self, ctx, room, expiry='7d', max_usage=0):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if len(self.bot.db['rooms'][room]['meta']['private_meta']['invites']) >= 20:
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.get("invites_limit")}'
            )

        infinite_enabled = ''
        if self.bot.config['permanent_invites']:
            infinite_enabled = ' ' + selector.get("permanent")

        if expiry == 'inf':
            if not self.bot.config['permanent_invites']:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("permanent_disabled")}')
            expiry = 0
        else:
            try:
                expiry = timetoint(expiry)
            except:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("invalid_duration","commons.moderation")}'
                )
            if expiry > 604800:
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("duration_toolong")}{infinite_enabled}'
                )
            expiry += time.time()
        invite = self.bot.bridge.create_invite(room, max_usage, expiry)
        try:
            await ctx.author.send(
                f'{selector.get("code")} `{invite}`\n{selector.fget("join",values={"prefix":self.bot.command_prefix,"invite":invite})}'
            )
        except:
            return await ctx.send(f'{self.bot.ui_emojis.warning} {selector.fget("dm_fail",values={"prefix":self.bot.command_prefix})}')
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @commands.command(name='delete-invite', hidden=True, description='Deletes an invite.')
    @restrictions.not_banned()
    async def delete_invite(self, ctx, invite):
        invite = invite.lower()
        if not self.can_manage(ctx.author, invite):
            raise restrictions.NoRoomManagement()
        selector = language.get_selector(ctx)
        try:
            self.bot.bridge.delete_invite(invite)
        except self.bot.bridge.InviteNotFoundError:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @commands.command(hidden=True, description='Views your room\'s invites.')
    @restrictions.not_banned()
    async def invites(self, ctx, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("is_public","config.create-invite")}')

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
            await ctx.author.send(embed=embed)
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("dm_fail")}')
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @commands.command(hidden=True, description='Renames a room.')
    @restrictions.not_banned()
    async def rename(self, ctx, room, newroom):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
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

    @commands.command(name='display-name', hidden=True, description='Sets a room\'s display name.')
    @restrictions.not_banned()
    async def display_name(self, ctx, room, *, name=''):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
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

    @commands.command(hidden=True,description='Sets a room\'s description.')
    @restrictions.not_banned()
    async def roomdesc(self,ctx,room,*,desc=''):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
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

    @commands.command(hidden=True, description='Sets a room\'s emoji.')
    @restrictions.not_banned()
    async def roomemoji(self, ctx, room, *, emoji=''):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
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
    @restrictions.admin()
    async def restrict(self,ctx,room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if self.bot.db['rooms'][room]['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_private")}')
        if self.bot.db['rooms'][room]['meta']['restricted']:
            self.bot.db['rooms'][room]['meta']['restricted'] = False
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['restricted'] = True
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')

    @commands.command(
        hidden=True,
        description='Locks/unlocks a room. Only moderators and admins will be able to chat in this room when locked.'
    )
    @restrictions.moderator()
    async def lock(self,ctx,room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        if not self.bot.db['rooms'][room]['meta']['private'] and not ctx.author.id in self.bot.admins:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("is_public")}')
        if self.bot.db['rooms'][room]['meta']['locked']:
            self.bot.db['rooms'][room]['meta']['locked'] = False
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_set",values={"room":room})}')
        else:
            self.bot.db['rooms'][room]['meta']['locked'] = True
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success_unset",values={"room":room})}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(description='Disbands a room.')
    async def disband(self, ctx, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.fget("confirm_title",values={"room":room})}',
            description=selector.get("confirm_body"),
            color=self.bot.colors.warning
        )
        view = ui.MessageComponents()
        view.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("disband"),
                    custom_id='disband'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel'
                )
            )
        )
        msg = await ctx.send(embed=embed, view=view)
        view.clear_items()
        view.row_count = 0
        view.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("disband"),
                    custom_id='disband',
                    disabled=True
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel',
                    disabled=True
                )
            )
        )

        def check(interaction):
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
        except:
            return await msg.edit(view=view)

        if interaction.data['custom_id'] == 'cancel':
            return await interaction.response.edit_message(view=view)

        self.bot.db['rooms'].pop(room)
        embed.title = f'{self.bot.ui_emojis.success} {selector.fget("success_body",values={"room":room})}'
        embed.description = selector.get("success_body")
        embed.colour = self.bot.colors.success
        await interaction.response.edit_message(embed=embed,view=None)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(aliases=['link','connect','federate','bridge'],description='Connects the channel to a given room.')
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    @restrictions.not_banned()
    @restrictions.no_admin_perms()
    async def bind(self,ctx,*,room):
        invite = False
        roominfo = self.bot.bridge.get_room(room.lower())

        if not roominfo:
            invite = True
            try:
                roominfo = self.bot.bridge.get_room(
                    self.bot.bridge.get_invite(room.lower())['room']
                )
            except:
                raise restrictions.UnknownRoom()

        if not invite:
            room = room.lower()
            if not room in self.bot.bridge.rooms:
                raise restrictions.UnknownRoom()

            if not self.can_join(ctx.author, room):
                raise restrictions.NoRoomJoin()
            roomname = room
        else:
            roomname = self.bot.bridge.get_invite(room.lower())['room']

        selector = language.get_selector(ctx)

        text = []
        if len(roominfo['meta']['rules']) > 0:
            for i in range(len(roominfo['meta']['rules'])):
                text.append(f'{i+1}. '+roominfo['meta']['rules'][i])
            text = '\n'.join(text)
        else:
            text = selector.fget("no_rules",values={"prefix":self.bot.command_prefix,"room":roominfo['meta']['display_name'] or roomname})

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.loading} {selector.get("check_title")}',
            description=selector.get("check_body"),
            color=self.bot.colors.warning
        )
        msg = await ctx.send(embed=embed)

        duplicate = self.bot.bridge.check_duplicate(ctx.channel)
        if duplicate:
            embed.colour = self.bot.colors.error
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("already_linked_title")}'
            embed.description = selector.fget("already_linked_body",values={"room":duplicate,"prefix":self.bot.command_prefix})
            return await msg.edit(embed=embed)

        'Join {}?'
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} {selector.fget("join_title",values={"roomname":roominfo["meta"]["display_name"] or roomname})}',
            description=f'{text}\n\n{selector.get("display")}',
            color=self.bot.colors.warning
        )
        embed.set_footer(text=selector.get("disclaimer"))

        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green,
                    label=selector.get("accept"),
                    custom_id='accept',
                    emoji=f'{self.bot.ui_emojis.success}'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel',
                    emoji=f'{self.bot.ui_emojis.error}'
                )
            )
        )

        await msg.edit(embed=embed,view=components)

        def check(interaction):
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=60)

            if interaction.data['custom_id'] == 'cancel':
                await interaction.response.edit_message(view=None)
                raise Exception()
        except:
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("no_agree")}'
            embed.colour = self.bot.colors.error
            return await msg.edit(embed=embed,view=None)

        embed.title = embed.title.replace(self.bot.ui_emojis.rooms, self.bot.ui_emojis.loading, 1)
        await msg.edit(embed=embed, view=None)
        await interaction.response.defer(ephemeral=False, with_message=True)

        webhook = None

        try:
            roomname = room
            if invite:
                roomname = self.bot.bridge.get_invite(room.lower())['room']
                await self.bot.bridge.accept_invite(ctx.author, room.lower())

            webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
            await self.bot.bridge.join_room(ctx.author,roomname,ctx.channel,webhook_id=webhook.id)
        except Exception as e:
            if webhook:
                try:
                    await webhook.delete()
                except:
                    pass

            embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'

            if type(e) is self.bot.bridge.InviteNotFoundError:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("invalid_invite")}'
            elif type(e) is self.bot.bridge.RoomBannedError:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("room_banned")}'

            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            await interaction.delete_original_message()

            if not type(e) is self.bot.bridge.InviteNotFoundError:
                raise
        else:
            embed.title = f'{self.bot.ui_emojis.success} {selector.get("success")}'
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
            try:
                await msg.pin()
            except:
                pass
            await interaction.edit_original_message(content=f'{self.bot.ui_emojis.success} {selector.get("say_hi")}')

    @commands.command(aliases=['unlink','disconnect'],description='Disconnects the server from a given room.')
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    @restrictions.no_admin_perms()
    async def unbind(self,ctx,room=None):
        selector = language.get_selector(ctx)
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_connected")}')
        data = self.bot.bridge.get_room(room.lower())
        if not data:
            raise restrictions.UnknownRoom()

        hook_deleted = True
        try:
            hooks = await ctx.guild.webhooks()
            if f'{ctx.guild.id}' in list(data.keys()):
                hook_ids = data[f'{ctx.guild.id}']
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
        except:
            hook_deleted = False

        await self.bot.bridge.leave_room(ctx.guild, room)

        if hook_deleted:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')
        else:
            await ctx.send(f'{self.bot.ui_emojis.warning} {selector.get("success_semi")}')

    @commands.command(description='Kicks a server from the room.')
    @restrictions.not_banned()
    async def roomkick(self, ctx, room, guild):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_moderate(ctx.author, room):
            raise restrictions.NoRoomModeration()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room.lower())

        platform = None
        for check_platform in data.keys():
            if check_platform == 'meta':
                continue
            if f'{guild}' in data[check_platform].keys():
                platform = check_platform
                break

        if not platform:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_connected")}')

        server_name = None
        try:
            if platform == 'discord':
                guild_obj = self.bot.get_guild(int(guild))
                server_name = guild_obj.name
            else:
                support = self.bot.platforms[platform]
                guild_obj = support.get_server(guild)
                server_name = support.name(guild_obj)

            hooks = await guild_obj.webhooks()
            if guild in list(data.keys()):
                hook_ids = data[guild]
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
        except:
            pass
        data[platform].pop(guild)
        self.bot.bridge.update_room(room, data)

        if not server_name:
            server_name = '[unknown server]'

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"server":server_name})}')

    @commands.command(description='Bans a server from the room.')
    @restrictions.not_banned()
    async def roomban(self, ctx, room, guild):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_moderate(ctx.author, room):
            raise restrictions.NoRoomModeration()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room.lower())

        platform = None
        for check_platform in data.keys():
            if check_platform == 'meta':
                continue
            if f'{guild}' in data[check_platform].keys():
                platform = check_platform
                break

        server_name = None
        try:
            if platform == 'discord':
                guild_obj = self.bot.get_guild(int(guild))
                server_name = guild_obj.name
            else:
                # if platform is None, this will error, this is normal
                support = self.bot.platforms[platform]
                guild_obj = support.get_server(guild)
                server_name = support.name(guild_obj)

            if platform == 'discord':
                hooks = await guild_obj.webhooks()
                if guild in list(data.keys()):
                    hook_ids = data[guild]
                else:
                    hook_ids = []
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        await webhook.delete()
                        break
        except:
            pass

        if platform:
            data[platform].pop(guild)

        if not guild in data['meta']['banned']:
            data['meta']['banned'].append(guild)

        self.bot.bridge.update_room(room, data)

        if not server_name:
            server_name = '[unknown server]'

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success",values={"server":server_name})}')

    @commands.command(description='Maps channels to rooms in bulk.', aliases=['autobind'])
    @restrictions.admin()
    @restrictions.no_admin_perms()
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

    @commands.command(description='Displays room rules for the specified room.')
    async def rules(self,ctx,*,room=''):
        if self.is_room_restricted(room,self.bot.db) and not self.is_user_admin(ctx.author.id):
            return await ctx.send(':eyes:')
        if room=='' or not room:
            room = self.bot.config['main_room']
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        selector = language.get_selector(ctx)

        index = 0
        text = ''
        if room in list(self.bot.db['rooms'].keys()):
            rules = self.bot.db['rooms'][room]['meta']['rules']
            if len(rules)==0:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_rules")}')
        else:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_rules")}')
        for rule in rules:
            if text=='':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.rooms} {selector.get("rules_title")}',description=text,color=self.bot.colors.unifier)
        embed.set_footer(text=selector.rawget("disclaimer","config.bind"))
        await ctx.send(embed=embed)

    @commands.command(hidden=True,description="Adds a rule to a given room.")
    @restrictions.not_banned()
    async def addrule(self,ctx,room,*,rule):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        if len(self.bot.db['rooms'][room]['meta']['rules']) >= 25:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exceed")}')
        self.bot.db['rooms'][room]['meta']['rules'].append(rule)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @commands.command(hidden=True,description="Removes a given rule from a given room.")
    @restrictions.not_banned()
    async def delrule(self,ctx,room,*,rule):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_manage(ctx.author, room):
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
    @restrictions.admin()
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
    @restrictions.admin()
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

    @commands.command(aliases=['public-rooms'], description='Shows a list of public rooms.')
    @commands.guild_only()
    async def rooms(self,ctx):
        await self.roomslist(ctx, False)

    @commands.command(name='private-rooms', description='Shows a list of public rooms.')
    @commands.guild_only()
    async def private_rooms(self, ctx):
        await self.roomslist(ctx, True)

    @commands.command(aliases=['guilds'], description='Lists all servers connected to a given room.')
    @commands.guild_only()
    async def servers(self, ctx, *, room='main'):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_join(ctx.author, room):
            raise restrictions.NoRoomJoin()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room)

        text = ''
        for platform in data.keys():
            if platform == 'meta':
                continue
            for guild_id in data[platform]:
                try:
                    if platform == 'discord':
                        name = self.bot.get_guild(int(guild_id)).name
                    else:
                        support = self.bot.platforms[platform]
                        name = support.name(support.get_server(guild_id))
                except:
                    continue
                if len(text) == 0:
                    text = f'- {name} (`{guild_id}`, {platform})'
                else:
                    text = f'{text}\n- {name} (`{guild_id}`, {platform})'
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} {selector.fget("title",values={"room":room})}', description=text,
            color=self.bot.colors.unifier
        )
        await ctx.send(embed=embed)

    @commands.command(description='Enables or disables usage of server emojis as Global Emojis.')
    @commands.has_permissions(manage_guild=True)
    async def toggle_emoji(self,ctx):
        selector = language.get_selector(ctx)
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')
        self.bot.db['emojis'] = self.bot.bridged_emojis
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(description='Displays or sets custom avatar.')
    @restrictions.not_banned()
    async def avatar(self,ctx,*,url=''):
        selector = language.get_selector(ctx)

        desc = selector.fget("no_avatar",values={"prefix":self.bot.command_prefix})
        try:
            if f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                avurl = self.bot.db['avatars'][f'{ctx.author.id}']
                desc = selector.fget("custom_avatar",values={"prefix":self.bot.command_prefix})
            else:
                desc = selector.fget("default_avatar",values={"prefix":self.bot.command_prefix})
                avurl = ctx.author.avatar.url
        except:
            avurl = None
        if not url=='':
            avurl = url
        embed = nextcord.Embed(
            title=selector.get("title"),
            description=desc,
            color=self.bot.colors.unifier
        )
        author = f'{ctx.author.name}#{ctx.author.discriminator}'
        if ctx.author.discriminator == '0':
            author = f'@{ctx.author.name}'
        try:
            embed.set_author(name=author,icon_url=avurl)
            embed.set_thumbnail(url=avurl)
        except:
            return await ctx.send(f"{self.bot.ui_emojis.error} Invalid URL!")
        if url=='remove':
            if not f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("error_missing")}')
            self.bot.db['avatars'].pop(f'{ctx.author.id}')
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        if not url=='':
            embed.title = selector.get("confirmation_title")
            embed.description = selector.get("confirmation_body")
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label=selector.get("apply"), custom_id='apply',
                disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray, label=selector.rawget("cancel","commons.navigation"), custom_id='cancel',
                disabled=False
            )
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        if url=='':
            embed.set_footer(text=selector.fget("change",values={"prefix":self.bot.command_prefix}))
            components = None
        msg = await ctx.send(embed=embed,view=components)
        if not url == '':
            def check(interaction):
                return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

            try:
                interaction = await self.bot.wait_for("interaction", check=check, timeout=30.0)
            except:
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                await msg.edit(view=components)
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("timeout","commons.navigation")}',reference=msg)
            if interaction.data['custom_id']=='cancel':
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                return await interaction.response.edit_message(view=components)
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            await msg.edit(view=components)
            self.bot.db['avatars'].update({f'{ctx.author.id}':url})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await interaction.response.send_message(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Config(bot))
