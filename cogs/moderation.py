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
import time
import hashlib
import datetime
from nextcord.ext import commands, application_checks
import traceback
from typing import Optional, Literal
from utils import log, ui, langmgr, restrictions as r, restrictions_legacy as r_legacy, slash as slash_helper

override_st = False
restrictions = r.Restrictions()
restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_helper.SlashHelper(language)

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def set_author(embed,**kwargs):
    try:
        embed.set_author(name=kwargs['name'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_author(name=kwargs['name'])

def timetoint(t,timeoutcap=False):
    try:
        return int(t)
    except:
        pass
    if not type(t) is str:
        t = str(t)
    total = 0
    t = t.replace('mo','n')
    if t.count('n')>1 or t.count('d')>1 or t.count('w')>1 or t.count('h')>1 or t.count('m')>1 or t.count('s')>1:
        raise ValueError('each identifier should never recur')
    t = t.replace('n','n ').replace('d','d ').replace('w','w ').replace('h','h ').replace('m','m ').replace('s','s ')
    times = t.split()
    for part in times:
        if part.endswith('n'):
            multi = int(part[:-1])
            if timeoutcap:
                total += (2419200 * multi)
            else:
                total += (2592000 * multi)
        elif part.endswith('d'):
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

class Moderation(commands.Cog, name=":shield: Moderation"):
    """Moderation allows server moderators and instance moderators to punish bad actors.

    Developed by Green and ItsAsheer"""

    def __init__(self,bot):
        global language
        self.bot = bot
        language = self.bot.langmgr
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)
        restrictions.attach_bot(self.bot)
        restrictions_legacy.attach_bot(self.bot)

    @nextcord.slash_command(
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def moderation(self, ctx):
        pass

    @moderation.subcommand(
        description=language.desc('moderation.block'),
        description_localizations=language.slash_desc('moderation.block')
    )
    @application_checks.guild_only()
    @application_checks.has_permissions(ban_members=True)
    async def block(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.block.target')
    ):
        selector = language.get_selector(ctx)

        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.user.id:
                return await ctx.send(selector.get("self_target_user"))
            if userid==ctx.guild.id:
                return await ctx.send(selector.get("self_target_guild"))
        except:
            userid = target
            found = False
            for platform in self.bot.platforms.keys():
                try:
                    self.bot.platforms[platform].get_user(userid)
                    found = True
                    break
                except:
                    continue

            if not found:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user_or_server","commons.moderation")}')
        if userid in self.bot.moderators:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("mod_immunity")}')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        else:
            self.bot.db['blocked'].update({f'{ctx.guild.id}':[]})
        if userid in banlist:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_blocked")}')
        self.bot.db['blocked'][f'{ctx.guild.id}'].append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @moderation.subcommand(
        description=language.desc('moderation.ban'),
        description_localizations=language.slash_desc('moderation.ban')
    )
    @restrictions.moderator()
    async def ban(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.ban.target'),
            duration: str = slash.option('moderation.ban.duration'),
            reason: Optional[str] = slash.option('moderation.ban.reason', required=False),
            discreet: Optional[bool] = slash.option('moderation.ban.discreet', required=False),
            disclose: Optional[bool] = slash.option('moderation.ban.reveal-user', required=False),
    ):
        selector = language.get_selector(ctx)
        if not ctx.user.id in self.bot.moderators:
            return
        if not reason:
            reason = 'no reason given'

        forever = (duration.lower() == 'inf' or duration.lower() == 'infinite' or
                   duration.lower() == 'forever' or duration.lower() == 'indefinite')

        if forever:
            duration = 0
        else:
            try:
                duration = timetoint(duration)
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_duration","commons.moderation")}')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.user.id and not override_st:
                return await ctx.send(selector.get("self_target"))
        except:
            userid = target
        if userid in self.bot.moderators and not ctx.user.id == self.bot.config['owner'] and not override_st:
            if not userid == ctx.user.id or not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("mod_immunity","commons.moderation")}')
        if userid==self.bot.user.id:
            return await ctx.send('are you fr')
        banlist = self.bot.db['banned']
        if userid in banlist:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_banned")}')

        await ctx.response.defer(ephemeral=False, with_message=True)
        ct = round(time.time())
        nt = ct + duration
        if forever:
            nt = 0
        self.bot.db['banned'].update({f'{userid}':nt})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        if ctx.user.discriminator=='0':
            mod = f'@{ctx.user.name}'
        else:
            mod = f'{ctx.user.name}#{ctx.user.discriminator}'
        try:
            user_selector = language.get_selector('commons.moderation',userid)
        except:
            user_selector = selector
        embed = nextcord.Embed(
            title=user_selector.rawfget("ban_title","commons.moderation",values={"moderator":mod}),
            description=reason,
            color=self.bot.colors.error,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        set_author(embed,name=mod,icon_url=ctx.user.avatar)
        if forever:
            embed.colour = self.bot.colors.critical
            embed.add_field(name='Actions taken',value=f'- :zipper_mouth:{user_selector.get("perm_ban","commons.moderation")}\n- :white_check_mark: {user_selector.rawget("perm_ban_appeal","commons.moderation")}',inline=False)
        else:
            embed.add_field(name='Actions taken',value=f'- :warning: {user_selector.rawget("warned","commons.moderation")}\n- :zipper_mouth: {user_selector.rawfget("temp_ban","commons.moderation",values={"expiry":nt})}',inline=False)
        embed.add_field(name=user_selector.rawget("appeal_title","commons.moderation"),value=user_selector.rawfget("appeal_body","commons.moderation",values={"prefix":self.bot.command_prefix}),inline=False)
        user = self.bot.get_user(userid)
        if not user:
            # add NUPS support for this later
            avatar = None
            name = '[unknown]'
            pass
        else:
            avatar = user.avatar.url if user.avatar else None
            name = user.name
            try:
                await user.send(embed=embed)
            except:
                pass

        original_msg = await ctx.original_message()

        content = original_msg.content
        embed = nextcord.Embed(description=language.get("recently_banned","moderation.ban"),color=self.bot.colors.error)
        if disclose:
            if not user:
                embed.set_author(name='@unknown')
            else:
                try:
                    embed.set_author(name=f'@{user.name}',icon_url=user.avatar.url)
                except:
                    embed.set_author(name=f'@{user.name}')
        else:
            embed.set_author(name='@hidden')

        original_msg.embeds = [embed]

        if not discreet:
            try:
                await self.bot.bridge.send(self.bot.config['main_room'], original_msg, 'discord', system=True, content_override='')
            except:
                # ignore fail so ban can be processed anyways
                pass
        for platform in self.bot.platforms.keys():
            try:
                await self.bot.bridge.send(self.bot.config['main_room'], original_msg, platform, system=True, content_override='')
            except:
                # ignore send fails so ban can be processed anyways
                pass

        original_msg.embeds = []
        original_msg.content = content

        try:
            userid = int(userid)
        except:
            pass
        await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.add_modlog(1, userid, reason, ctx.user.id))
        actions_count, actions_count_recent = self.bot.bridge.get_modlogs_count(userid)
        log_embed = nextcord.Embed(title=language.get("success_title","moderation.ban"), description=reason, color=self.bot.colors.error, timestamp=datetime.datetime.now(datetime.timezone.utc))
        log_embed.add_field(name=language.get("expiry","moderation.ban"), value=language.get("never","moderation.ban") if forever else f'<t:{nt}:R>', inline=False)
        log_embed.set_author(name=f'@{name}',icon_url=avatar)
        log_embed.add_field(
            name=language.get("modlogs_title","moderation.ban"),
            value=language.fget("modlogs_body","moderation.ban",values={"recent_warns": actions_count_recent["warns"],"total_warns": actions_count["warns"],"recent_bans": actions_count_recent["bans"],"total_bans": actions_count["bans"]}),
            inline=False)
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    custom_id='delete',
                    label=selector.rawget("delete","commons.moderation"),
                    emoji='\U0001F5D1'
                )
            )
        )
        await ctx.edit_original_message(content=selector.get("success"),embed=log_embed)

        try:
            if not self.bot.config['enable_logging']:
                raise RuntimeError()
            ch = self.bot.get_channel(self.bot.config['logs_channel'])

            await ch.send(embed=log_embed)
        except:
            pass

    @commands.command(description=language.desc('moderation.fullban'))
    @restrictions_legacy.admin()
    async def fullban(self, ctx: commands.Context, target):
        selector = language.get_selector(ctx)

        target.replace('<@', '', 1).replace('>', '', 1).replace('!', '', 1)

        try:
            target = int(target)
            self.bot.get_user(target)
        except:
            pass

        if target==ctx.author.id:
            return await ctx.send(selector.rawget("self_target","moderation.ban"))

        if target==self.bot.config['owner']:
            return await ctx.send(selector.get("owner_immunity"))

        if target in self.bot.admins:
            return await ctx.send(selector.rawget("admin_immunity","commons.moderation"))

        if target in self.bot.db['fullbanned']:
            self.bot.db['fullbanned'].remove(target)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        else:
            self.bot.db['fullbanned'].append(target)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')

        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @moderation.subcommand(
        description=language.desc('moderation.unblock'),
        description_localizations=language.slash_desc('moderation.unblock')
    )
    @application_checks.guild_only()
    @application_checks.has_permissions(ban_members=True)
    async def unblock(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.unblock.target')
    ):
        selector = language.get_selector(ctx)
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            userid = target
            found = False
            for platform in self.bot.platforms.keys():
                try:
                    self.bot.platforms[platform].get_user(userid)
                    found = True
                    break
                except:
                    continue

            if not found:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user_or_server","commons.moderation")}')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        if not userid in banlist:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_blocked")}')
        self.bot.db['blocked'][f'{ctx.guild.id}'].remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @moderation.subcommand(
        description=language.desc('moderation.unban'),
        description_localizations=language.slash_desc('moderation.unban')
    )
    @restrictions.moderator()
    async def unban(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.ban.target')
    ):
        selector = language.get_selector(ctx)

        userid = target.replace('<@','',1).replace('!','',1).replace('>','',1)

        banlist = self.bot.db['banned']
        if not f'{userid}' in list(banlist.keys()):
            if f'{userid}' in list(self.bot.bridge.secbans.keys()):
                self.bot.bridge.secbans.pop(f'{userid}')
                return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_banned")}')
        self.bot.db['banned'].pop(f'{userid}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @moderation.subcommand(
        name='deny-appeals',
        description=language.desc('moderation.deny-appeals'),
        description_localizations=language.slash_desc('moderation.deny-appeals')
    )
    @restrictions.admin()
    async def deny_appeals(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.deny-appeals.target')
    ):
        selector = language.get_selector(ctx)

        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.user.id and not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("self_target","moderation.ban")}')
        except:
            userid = target
        if userid in self.bot.db['appealban']:
            self.bot.db['appealban'].remove(userid)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        else:
            self.bot.db['appealban'].append(userid)
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_set")}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @moderation.subcommand(description='Appeals your ban, if you have one.')
    @commands.dm_only()
    async def appeal(self, ctx: nextcord.Interaction):
        gbans = self.bot.db['banned']
        banned = False
        selector = language.get_selector(ctx)

        if f'{ctx.user.id}' in list(gbans.keys()):
            ct = time.time()
            if f'{ctx.user.id}' in list(gbans.keys()):
                banuntil = gbans[f'{ctx.user.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{ctx.user.id}')
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    banned = True

        if not banned:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_ban")}', ephemeral=True)

        if ctx.user.id in self.bot.db['appealban']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("banned")}', ephemeral=True)

        actions, _ = self.bot.bridge.get_modlogs(ctx.user.id)

        if len(actions['bans'])==0:
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.get("missing_ban")}', ephemeral=True
            )

        ban = actions['bans'][len(actions['bans'])-1]

        embed = nextcord.Embed(
            title=selector.get("ban"),description=ban['reason'],color=self.bot.colors.error
        )
        embed.set_author(name=f'@{ctx.user.name}', icon_url=ctx.user.avatar.url if ctx.user.avatar else None)
        components = ui.MessageComponents()
        components.add_rows(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green,
                    label=selector.rawget("yes","commons.navigation"),
                    custom_id='yes'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.rawget("no","commons.navigation"),
                    custom_id='no'
                )
            )
        )

        msg = await ctx.send(f'{self.bot.ui_emojis.warning} {selector.get("confirm")}', embed=embed, view=components, ephemeral=False)
        # noinspection PyUnresolvedReferences
        msg = await msg.fetch()

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id==msg.id and interaction.user.id==ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=None)

        if not interaction.data['custom_id']=='yes':
            return await interaction.response.edit_message(view=None)

        await msg.edit(view=None)

        modal = nextcord.ui.Modal(title=selector.get("title"), auto_defer=False)
        modal.add_item(
            nextcord.ui.TextInput(
                style=nextcord.TextInputStyle.paragraph, label=selector.get("reason_title"),
                placeholder=selector.get("reason_prompt"),
                required=True
            )
        )
        modal.add_item(
            nextcord.ui.TextInput(
                style=nextcord.TextInputStyle.short, label=selector.rawget("sign_title","bridge.report"),
                placeholder=selector.get("sign_prompt"),
                required=True, min_length=len(ctx.user.name), max_length=len(ctx.user.name)
            )
        )
        await interaction.response.send_modal(modal)

        while True:
            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=600)
            except:
                return await msg.edit(view=None)
            if interaction.data['components'][1]['components'][0]['value'].lower() == ctx.user.name.lower():
                break

        embed = nextcord.Embed(
            title=selector.get("appeal_title"),
            description=interaction.data['components'][0]['components'][0]['value'],
            color=self.bot.colors.gold
        )
        embed.set_author(name=f'@{ctx.user.name}',icon_url=ctx.user.avatar.url if ctx.user.avatar else None)
        embed.add_field(name=selector.get("appeal_ban"),value=ban['reason'],inline=False)
        ch = self.bot.get_channel(self.bot.config['reports_channel'])
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label=selector.rawget("reject","commons.navigation"), custom_id=f'apreject_{ctx.user.id}',
                disabled=False, emoji=self.bot.ui_emojis.error
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label=selector.get("accept"), custom_id=f'apaccept_{ctx.user.id}',
                disabled=False, emoji=self.bot.ui_emojis.success
            )
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        msg: nextcord.Message = await ch.send(
            f'<@&{self.bot.config["moderator_role"]}>', embed=embed, view=components
        )
        try:
            thread = await msg.create_thread(
                name=selector.fget("discussion",values={"username": ctx.user.name}),
                auto_archive_duration=10080
            )
            self.bot.db['report_threads'].update({str(msg.id): thread.id})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        except:
            pass
        return await interaction.response.send_message(
            f'# {self.bot.ui_emojis.success} {selector.get("success_title")}\n{selector.get("success_body")}',
            ephemeral=True
        )

    @moderation.subcommand(
        description=language.desc('moderation.standing'),
        description_localizations=language.slash_desc('moderation.standing')
    )
    async def standing(
            self, ctx: nextcord.Interaction,
            target: Optional[str] = slash.option('moderation.standing.target',required=False)
    ):
        if target and not ctx.user.id in self.bot.moderators:
            target = None

        selector = language.get_selector(ctx)

        menu = 0
        page = 0
        is_self = False
        if target:
            orig_id = int(target.replace('<@', '', 1).replace('>', '', 1).replace('!', '', 1))
            try:
                target = self.bot.get_user(int(target.replace('<@','',1).replace('>','',1).replace('!','',1)))
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user","commons.moderation")}')
        else:
            orig_id = ctx.user.id
            target = ctx.user
            is_self = True
        if target:
            if target.id == ctx.user.id:
                is_self = True
        embed = nextcord.Embed(
            title=selector.get("allgood_title"),
            description=selector.get("allgood_body")+
            '\n\n:white_check_mark: :white_large_square: :white_large_square: :white_large_square: :white_large_square:',
            color=self.bot.colors.success)

        actions_count, actions_count_recent = self.bot.bridge.get_modlogs_count(orig_id)
        actions, _ = self.bot.bridge.get_modlogs(orig_id)

        gbans = self.bot.db['banned']
        ct = time.time()
        noexpiry = False
        if f'{orig_id}' in list(gbans.keys()):
            banuntil = gbans[f'{orig_id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{orig_id}')
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            if banuntil == 0:
                noexpiry = True

        judgement = (
            actions_count['bans'] + actions_count_recent['warns'] + (actions_count_recent['bans']*4)
        )
        if f'{orig_id}' in list(gbans.keys()):
            embed.title = selector.get("suspended_title")
            embed.colour = self.bot.colors.error
            embed.description = selector.get("suspended_body_perm") if noexpiry else selector.get("suspended_body")
        elif 2 < judgement <= 5:
            embed.title = selector.get("fair_title")
            embed.colour = 0xffff00
            embed.description = (
                    selector.get("fair_body")+
                    '\n\n:white_large_square: :warning: :white_large_square: :white_large_square: :white_large_square:'
            )
        elif 5 < judgement <= 10:
            embed.title = selector.get("caution_title")
            embed.colour = self.bot.colors.warning
            embed.description = (
                    selector.get("caution_body")+
                    '\n\n:white_large_square: :white_large_square: :biohazard: :white_large_square: :white_large_square:'
            )
        elif judgement > 10:
            embed.title = selector.get("warning_title")
            embed.colour = self.bot.colors.purple
            embed.description = (
                    selector.get("warning_body")+
                    '\n\n:white_large_square: :white_large_square: :white_large_square: :bangbang: :white_large_square:'
            )
        if target:
            embed.set_author(name=f'@{target.name}\'s account standing', icon_url=target.avatar.url if target.avatar else None)
        else:
            embed.set_author(name=f'{orig_id}\'s account standing')
        if target:
            if target.bot or target.id in self.bot.db['fullbanned']:
                if target.bot:
                    embed.title = selector.get("bot_title")
                    embed.description = selector.get("bot_body")
                    embed.colour = 0xcccccc
                else:
                    embed.title = selector.get("fullban_title")
                    embed.description = selector.get("fullban_body")
                    embed.colour = self.bot.colors.critical
                return await ctx.send(embed=embed)
        elif orig_id in self.bot.db['fullbanned']:
            embed.title = selector.get("fullban_title")
            embed.description = selector.get("fullban_body")
            embed.colour = self.bot.colors.critical
            return await ctx.send(embed=embed)
        msg = None
        interaction = None
        while True:
            components = None
            if menu == 0:
                embed.add_field(name=selector.get("recent"),
                                value=selector.fget("punishments",values={"warns":actions_count_recent["warns"],"bans":actions_count_recent["bans"]}),
                                inline=False)
                embed.add_field(name=selector.get("alltime"),
                                value=selector.fget("punishments",values={"warns":actions_count["warns"],"bans":actions_count["bans"]}),
                                inline=False)
                embed.set_footer(text=selector.get("info"))
                components = ui.MessageComponents()
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='warns',
                            label=selector.rawget("warnings","commons.moderation"),
                            emoji='\U000026A0',
                            style=nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='bans',
                            label=selector.rawget("bans","commons.moderation"),
                            emoji='\U0001F6D1',
                            style=nextcord.ButtonStyle.red
                        )
                    )
                )
            elif menu == 1:
                while (page * 5) + 1 >= len(actions['warns']) and page > 0:
                    page -= 1
                for i in range(page * 5, (page + 1) * 5):
                    if len(actions['warns']) == 0 or len(actions['warns'])-i-1 < 0:
                        break
                    embed.add_field(
                        name=f':warning: {selector.fget("warning",values={"id":len(actions["warns"])-i})}',
                        value=actions['warns'][len(actions['warns'])-i-1]['reason'],
                        inline=False
                    )
                    if i >= len(actions['warns']) - 1:
                        break
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label=selector.rawget("prev","commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=page==0
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label=selector.rawget("next","commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=((page+1)*5)+1 >= len(actions['warns'])
                        )
                    ) if len(embed.fields) >= 1 else ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label=selector.rawget("prev","commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label=selector.rawget("next","commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='back',
                            label=selector.rawget("back", "commons.navigation"),
                            style=nextcord.ButtonStyle.gray
                        )
                    )
                )
                if len(embed.fields) == 0:
                    embed.add_field(name=selector.get("no_warns_title"),value=selector.get("no_warns_body"))
                embed.set_footer(text=f'Page {page+1}')
            elif menu == 2:
                while (page * 5) + 1 >= len(actions['bans']) and page > 0:
                    page -= 1
                for i in range(page * 5, (page + 1) * 5):
                    if len(actions['bans']) == 0 or len(actions['bans'])-i-1 < 0:
                        break
                    embed.add_field(
                        name=f':no_entry_sign: {selector.fget("ban",values={"id":len(actions["bans"])-i})}',
                        value=actions['bans'][len(actions['bans']) - i - 1]['reason'],
                        inline=False
                    )
                    if i >= len(actions['bans']) - 1:
                        break
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label=selector.rawget("prev", "commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=page == 0
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label=selector.rawget("next", "commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=((page + 1) * 5) + 1 >= len(actions['warns'])
                        )
                    ) if len(embed.fields) >= 1 else ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label=selector.rawget("prev", "commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label=selector.rawget("next", "commons.navigation"),
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='back',
                            label=selector.rawget("back", "commons.navigation"),
                            style=nextcord.ButtonStyle.gray
                        )
                    )
                )
                if len(embed.fields) == 0:
                    embed.add_field(name=selector.get("no_bans_title"),value=selector.get("no_bans_body"))
                embed.set_footer(text=f'Page {page + 1}')
            if not msg:
                if ctx.guild and is_self:
                    msg = await ctx.user.send(embed=embed, view=components)
                    await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')
                else:
                    msg = await ctx.send(embed=embed, view=components)
                    msg = await msg.fetch()
            else:
                if interaction:
                    await interaction.response.edit_message(embed=embed,view=components)
                else:
                    await msg.edit(embed=embed,view=components)
            embed.clear_fields()

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.message.id==msg.id and interaction.user.id==ctx.user.id

            try:
                interaction = await self.bot.wait_for('interaction',timeout=60,check=check)
            except:
                return await msg.edit(view=None)
            page = 0
            if interaction.data['custom_id'] == 'back':
                menu = 0
            elif interaction.data['custom_id'] == 'warns':
                menu = 1
            elif interaction.data['custom_id'] == 'bans':
                menu = 2
            elif interaction.data['custom_id'] == 'prev':
                page -= 1 if page >= 1 else 0
            elif interaction.data['custom_id'] == 'next':
                page += 1

    @moderation.subcommand(
        description=language.desc('moderation.identify'),
        description_localizations=language.slash_desc('moderation.identify')
    )
    @application_checks.guild_only()
    async def identify(
            self, ctx: nextcord.Interaction,
            message: str = slash.option('moderation.identify.message')
    ):
        selector = language.get_selector(ctx)
        try:
            msg = await ctx.channel.fetch_message(int(message))
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_message","commons.interaction")}')
        try:
            msg_obj = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("not_found","commons.interaction")}')
        if msg_obj.source == 'discord':
            try:
                username = self.bot.get_user(int(msg_obj.author_id)).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.get_guild(int(msg_obj.guild_id)).name
            except:
                guildname = '[unknown]'
        elif msg_obj.source == 'revolt':
            try:
                username = self.bot.revolt_client.get_user(msg_obj.author_id).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.revolt_client.get_server(msg_obj.guild_id).name
            except:
                guildname = '[unknown]'
        else:
            try:
                username = self.bot.guilded_client.get_user(msg_obj.author_id).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.guilded_client.get_server(msg_obj.guild_id).name
            except:
                guildname = '[unknown]'
        await ctx.send(
            selector.fget("sent_by",values={"username":username,"userid":msg_obj.author_id,"servername":guildname,"serverid":msg_obj.guild_id,"source":msg_obj.source,"messageid":msg_obj.id})
        )

    @nextcord.message_command(name='Identify origin')
    @application_checks.guild_only()
    async def identify_ctx(self, interaction, msg: nextcord.Message):
        selector = language.get_selector('moderation.identify', userid=interaction.user.id)

        if interaction.user.id in self.bot.db['fullbanned']:
            return
        try:
            msg_obj = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await interaction.response.send_message(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_message","commons.interaction")}',ephemeral=True)
        if msg_obj.source == 'discord':
            try:
                username = self.bot.get_user(int(msg_obj.author_id)).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.get_guild(int(msg_obj.guild_id)).name
            except:
                guildname = '[unknown]'
        elif msg_obj.source == 'revolt':
            try:
                username = self.bot.revolt_client.get_user(msg_obj.author_id).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.revolt_client.get_server(msg_obj.guild_id).name
            except:
                guildname = '[unknown]'
        else:
            try:
                username = self.bot.guilded_client.get_user(msg_obj.author_id).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.guilded_client.get_server(msg_obj.guild_id).name
            except:
                guildname = '[unknown]'
        await interaction.response.send_message(
            selector.fget("sent_by",values={"username":username,"userid":msg_obj.author_id,"servername":guildname,"serverid":msg_obj.guild_id,"source":msg_obj.source,"messageid":msg_obj.id})
        )

    @moderation.subcommand(
        description=language.desc('moderation.delete'),
        description_localizations=language.slash_desc('moderation.delete')
    )
    @application_checks.guild_only()
    @restrictions.no_admin_perms()
    @restrictions.not_banned()
    async def delete(
            self, ctx: nextcord.Interaction,
            message: str = slash.option('moderation.delete.message')
    ):
        """Deletes all bridged messages. Does not delete the original."""

        selector = language.get_selector(ctx)

        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{ctx.user.id}' in list(gbans.keys()):
            banuntil = gbans[f'{ctx.user.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{ctx.user.id}')
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            else:
                return
        if f'{ctx.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{ctx.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{ctx.guild.id}')
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            else:
                return

        try:
            msg = await self.bot.bridge.fetch_message(message)
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_message","commons.interaction")}')

        if not ctx.user.id == msg.author_id and not ctx.user.id in self.bot.moderators:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_ownership")}')

        status_msg = await ctx.send(f'{self.bot.ui_emojis.loading} {selector.get("deleting")}')

        try:
            await self.bot.bridge.delete_parent(message)
            if msg.webhook:
                raise ValueError()
            return await status_msg.edit(content=f'{self.bot.ui_emojis.success} ' + selector.get("parent_delete"))
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(message)
                await self.bot.bridge.delete_message(msg)
                return await status_msg.edit(content=f'{self.bot.ui_emojis.success} ' + selector.fget("children_delete",values={"count": deleted}))
            except:
                traceback.print_exc()
                await status_msg.edit(content=f'{self.bot.ui_emojis.error} ' + selector.get("error"))

    @nextcord.message_command(name='Delete message')
    @application_checks.guild_only()
    async def delete_ctx(self, interaction, msg: nextcord.Message):
        selector = language.get_selector('moderation.delete', userid=interaction.user.id)

        if interaction.user.id in self.bot.db['fullbanned']:
            return
        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{interaction.user.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.user.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.user.id}')
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            else:
                return
        if f'{interaction.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.guild.id}')
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            else:
                return
        if f'{interaction.user.id}' in list(gbans.keys()) or f'{interaction.guild.id}' in list(gbans.keys()):
            return await interaction.response.send_message(f'{self.bot.ui_emojis.error} {selector.fget("banned",values={"prefix": self.bot.command_prefix})}',
                                                           ephemeral=True)
        msg_id = msg.id

        try:
            msg = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await interaction.response.send_message(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_message","commons.interaction")}', ephemeral=True)

        if not interaction.user.id == msg.author_id and not interaction.user.id in self.bot.moderators:
            return await interaction.response.send_message(f'{self.bot.ui_emojis.error} {selector.get("no_ownership")}', ephemeral=True)

        await interaction.response.send_message(f'{self.bot.ui_emojis.loading} {selector.get("deleting")}', ephemeral=True)

        try:
            await self.bot.bridge.delete_parent(msg_id)
            if msg.webhook:
                raise ValueError()
            return await interaction.edit_original_message(
                content=f'{self.bot.ui_emojis.success} ' + selector.get("parent_delete")
            )
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(msg_id)
                await self.bot.bridge.delete_message(msg)
                return await interaction.edit_original_message(
                    content=f'{self.bot.ui_emojis.success} ' + selector.fget("children_delete",values={"count": deleted})
                )
            except:
                traceback.print_exc()
                return await interaction.edit_original_message(
                    content=f'{self.bot.ui_emojis.error} ' + selector.get("error")
                )

    @moderation.subcommand(
        description=language.desc('moderation.warn'),
        description_localizations=language.slash_desc('moderation.warn')
    )
    @restrictions.moderator()
    async def warn(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.warn.target'),
            reason: str = slash.option('moderation.warn.reason')
    ):
        selector = language.get_selector(ctx)
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.user.id and not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("self_target")}')
        except:
            userid = target
            found = False
            for platform in self.bot.platforms.keys():
                try:
                    self.bot.platforms[platform].get_user(userid)
                    found = True
                    break
                except:
                    continue

            if not found:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user_or_server","commons.moderation")}')
        if userid in self.bot.moderators and not ctx.user.id==self.bot.config['owner']:
            if not userid == ctx.user.id or not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("mod_immunity","commons.moderation")}')
        if userid==self.bot.user.id:
            return await ctx.send(selector.rawget("fr","commons.moderation"))
        if ctx.user.discriminator=='0':
            mod = f'@{ctx.user.name}'
        else:
            mod = f'{ctx.user.name}#{ctx.user.discriminator}'
        try:
            user_selector = language.get_selector('commons.moderation',userid)
        except:
            user_selector = selector
        embed = nextcord.Embed(
            title=user_selector.rawfget("warn_title","commons.moderation",values={"moderator":mod}),
            description=reason,
            color=self.bot.colors.warning,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        set_author(embed,name=mod,icon_url=ctx.user.avatar)
        embed.add_field(
            name=user_selector.rawget("actions_taken","commons.moderation"),
            value=f'- :warning: {user_selector.rawget("warned","commons.moderation")}',
            inline=False
        )
        user = self.bot.get_user(userid)
        if not user:
            try:
                user = self.bot.revolt_client.get_user(userid)
                await user.send(
                    f'## {embed.title}\n{embed.description}\n\n**Actions taken**\n{embed.fields[0].value}')
                return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user_warn","commons.moderation")}')
        if user.bot:
            return await ctx.send(selector.get("bot"))
        await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.add_modlog(0,user.id,reason,ctx.user.id))
        actions_count, actions_count_recent = self.bot.bridge.get_modlogs_count(user.id)
        log_embed = nextcord.Embed(
            title=language.get("warned","moderation.warn"),
            description=reason,
            color=self.bot.colors.warning,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        log_embed.set_author(name=f'@{user.name}', icon_url=user.avatar.url if user.avatar else None)
        log_embed.add_field(
            name=language.get("modlogs_title", "moderation.ban"),
            value=language.fget("modlogs_body", "moderation.ban", values={"recent_warns": actions_count_recent["warns"],"total_bans": actions_count["bans"]}),
            inline=False
        )
        try:
            await user.send(embed=embed)
            await ctx.edit_original_message(
                content=f'{self.bot.ui_emojis.success} {selector.get("success")}',embed=log_embed
            )
        except:
            await ctx.edit_original_message(
                content=f'{self.bot.ui_emojis.success} {selector.get("success_nodm")}',embed=log_embed
            )

    @moderation.subcommand(
        name='delete-warning',
        description=language.desc('moderation.delete-warning'),
        description_localizations=language.slash_desc('moderation.delete-warning')
    )
    @restrictions.moderator()
    async def delete_warning(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.delete-warning.target'),
            index: int = slash.option('moderation.delete-warning.index')
    ):
        selector = language.get_selector(ctx)

        try:
            index = int(index) - 1
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_index","commons.moderation")}')
        if index < 0:
            return await ctx.send(selector.rawget("what","commons.moderation"))
        try:
            target = self.bot.get_user(int(target.replace('<@','',1).replace('!','',1).replace('>','',1)))
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user","commons.moderation")}')
        try:
            actions, _ = self.bot.bridge.get_modlogs(target.id)
            warn = actions['warns'][index]
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("no_action","commons.moderation")}')
        embed = nextcord.Embed(
            title=selector.get("title"),
            description=warn['reason'],
            color=self.bot.colors.warning
        )
        embed.set_author(name=f'@{target.name}', icon_url=target.avatar.url if target.avatar else None)
        searched = 0
        deleted = False
        for i in range(len(self.bot.db['modlogs'][f'{target.id}'])):
            if self.bot.db['modlogs'][f'{target.id}'][i]['type']==0:
                if searched==index:
                    self.bot.db['modlogs'][f'{target.id}'].pop(i)
                    deleted = True
                    break
                searched += 1
        if deleted:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}', embed=embed)
        else:
            await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("failed")}')

    @moderation.subcommand(
        name='delete-ban',
        description=language.desc('moderation.delete-ban'),
        description_localizations=language.slash_desc('moderation.delete-ban')
    )
    @restrictions.moderator()
    async def delete_ban(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.delete-ban.target'),
            index: int = slash.option('moderation.delete-ban.index')
    ):
        selector = language.get_selector(ctx)

        try:
            index = int(index) - 1
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_index","commons.moderation")}')
        if index < 0:
            return await ctx.send(selector.rawget("what","commons.moderation"))
        try:
            target = self.bot.get_user(int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)))
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("invalid_user","commons.moderation")}')
        try:
            actions, _ = self.bot.bridge.get_modlogs(target.id)
            ban = actions['bans'][index]
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("no_action","commons.moderation")}')
        embed = nextcord.Embed(
            title=selector.get("title"),
            description=ban['reason'],
            color=self.bot.colors.error
        )
        embed.set_author(name=f'@{target.name}', icon_url=target.avatar.url if target.avatar else None)
        embed.set_footer(text=selector.get("disclaimer"))
        searched = 0
        deleted = False
        for i in range(len(self.bot.db['modlogs'][f'{target.id}'])):
            if self.bot.db['modlogs'][f'{target.id}'][i]['type'] == 1:
                if searched == index:
                    self.bot.db['modlogs'][f'{target.id}'].pop(i)
                    deleted = True
                    break
                searched += 1
        if deleted:
            await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}', embed=embed)
        else:
            await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("failed")}')

    @moderation.subcommand(
        description=language.desc('moderation.anick'),
        description_localizations=language.slash_desc('moderation.anick')
    )
    @restrictions.moderator()
    async def anick(
            self, ctx: nextcord.Interaction,
            target: str = slash.option('moderation.anick.target'),
            nickname: Optional[str] = slash.option('moderation.anick.nickname')
    ):
        selector = language.get_selector(ctx)
        userid = target.replace('<@', '').replace('!', '').replace('>', '')

        # Update or remove the nickname in the database
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(str(userid), None)
        else:
            self.bot.db['nicknames'][str(userid)] = nickname

        # Save changes to the database
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @moderation.subcommand(
        description=language.desc('moderation.bridge-lock'),
        description_localizations=language.slash_desc('moderation.bridge-lock')
    )
    @restrictions.moderator()
    async def bridgelock(self, ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)

        if not hasattr(self.bot, 'bridge'):
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("already_locked")}')
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.warning} {selector.get("warning_title")}',
                               description=selector.get("warning_body"),
                               color=self.bot.colors.warning)
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,label=selector.get("lockdown"),custom_id='lockdown'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,label=selector.rawget("cancel","commons.moderation")
                )
            )
        )
        components_inac = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,label=selector.get("lockdown"),custom_id='lockdown',disabled=True
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,label=selector.rawget("cancel","commons.moderation"),disabled=True
                )
            )
        )
        msg = await ctx.send(embed=embed,view=components)
        msg = await msg.fetch()

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.user.id==ctx.user.id and interaction.message.id==msg.id

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=30)
        except:
            return await msg.edit(view=components_inac)

        if not interaction.data['custom_id']=='lockdown':
            return await interaction.response.edit_message(view=components_inac)

        embed.title = f':rotating_light: {selector.get("fwarning_title")} :rotating_light:'
        embed.description = selector.get("fwarning_body")
        embed.colour = self.bot.colors.critical

        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red, label=selector.rawget("double_confirm", "commons.moderation"), custom_id='lockdown'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray, label=selector.rawget("cancel", "commons.moderation")
                )
            )
        )
        components_inac = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red, label=selector.rawget("double_confirm", "commons.moderation"),
                    custom_id='lockdown', disabled=True
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray, label=selector.rawget("cancel", "commons.moderation"),
                    disabled=True
                )
            )
        )

        await interaction.response.edit_message(embed=embed)

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=30)
        except:
            return await msg.edit(view=components_inac)

        await interaction.response.edit_message(view=components_inac)

        if not interaction.data['custom_id']=='lockdown':
            return

        self.logger.warn(f'Bridge lockdown issued by {ctx.user.id}!')
        self.logger.info("Backing up message cache...")
        await self.bot.bridge.backup()
        self.logger.info("Backup complete")
        self.logger.info("Disabling bridge...")
        del self.bot.bridge
        self.bot.unload_extension('cogs.bridge')
        self.logger.info("Bridge disabled")
        self.logger.info("Lockdown complete")
        embed.title = f'{self.bot.ui_emojis.warning} {selector.get("success_title")}'
        embed.description = selector.get("success_body")
        await msg.edit(embed=embed)

    @commands.command(name='bridge-unlock',description=language.desc('moderation.bridge-unlock'))
    @restrictions_legacy.admin()
    async def bridgeunlock(self, ctx):
        selector = language.get_selector(ctx)
        try:
            self.bot.load_extension('cogs.bridge')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_locked")}')
        try:
            await self.bot.bridge.restore()
            self.logger.info('Restored ' + str(len(self.bot.bridge.bridged)) + ' messages')
        except:
            traceback.print_exc()
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @moderation.subcommand(
        name='under-attack',
        description=language.desc('moderation.under-attack'),
        description_localizations=language.slash_desc('moderation.under-attack')
    )
    @application_checks.guild_only()
    @restrictions.under_attack()
    async def under_attack(self, ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)

        if f'{ctx.guild.id}' in self.bot.db['underattack']:
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.warning} {selector.get("disable_title")}',
                description=selector.get("disable_body")
            )
        else:
            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.warning} {selector.get("enable_title")}',
                description=selector.get("enable_body")+'\n\n'+selector.get("disclaimer")
            )
            embed.set_footer(text=selector.get("notify"))
        embed.colour = self.bot.colors.warning

        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=(
                        selector.rawget("deactivate","commons.navigation")
                        if f'{ctx.guild.id}' in self.bot.db['underattack'] else
                        selector.rawget("activate","commons.navigation")
                    ),
                    custom_id='accept'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel'
                )
            )
        )

        msg = await ctx.send(embed=embed, view=components)
        msg = await msg.fetch()

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=None)

        if interaction.data['custom_id'] == 'cancel':
            return await interaction.response.edit_message(view=None)

        await msg.edit(view=None)

        was_attack = f'{ctx.guild.id}' in self.bot.db['underattack']

        if was_attack:
            self.bot.db['underattack'].remove(f'{ctx.guild.id}')
        else:
            self.bot.db['underattack'].append(f'{ctx.guild.id}')

        embed.title = f'{self.bot.ui_emojis.success} ' + (
            selector.get("disabled_title") if was_attack else selector.get("enabled_title")
        )
        embed.description = selector.get("disabled_body") if was_attack else selector.get("enabled_body")
        embed.colour = self.bot.colors.success

        await msg.edit(embed=embed)

    @moderation.subcommand(
        description=language.desc('moderation.alert'),
        description_localizations=language.slash_desc('moderation.alert')
    )
    @restrictions.moderator()
    @restrictions.no_admin_perms()
    async def alert(
            self, ctx: nextcord.Interaction,
            risk_type: str = slash.option('moderation.alert.risk_type'),
            level: Literal['emergency','warning','advisory','clear'] = slash.option('moderation.alert.level'),
            message: str = slash.option('moderation.alert.message')
    ):
        selector = language.get_selector(ctx)

        risk_type = risk_type.lower()
        if not risk_type in self.bot.bridge.alert.titles.keys():
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        level = level.lower()
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.get("send_title")}',
            description=selector.fget("send_body",values={"level":level}),
            color=self.bot.colors.warning
        )
        if not level == 'advisory':
            embed.set_footer(text=selector.get("willping"))
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("send"),
                    custom_id='accept'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel'
                )
            )
        )

        msg = await ctx.send(embed=embed, view=components)
        msg = await msg.fetch()

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=None)

        await interaction.response.edit_message(view=None)

        if interaction.data['custom_id'] == 'cancel':
            return

        embed.title = embed.title.replace(self.bot.ui_emojis.warning, self.bot.ui_emojis.loading, 1)
        await msg.edit(embed=embed)

        alert = {
            'type': risk_type,
            'severity': level,
            'description': message
        }

        parent_id = await self.bot.bridge.send(self.bot.config['alerts_room'], ctx.message, alert=alert)

        parent_id_2 = None
        if not level == 'advisory':
            parent_id_2 = await self.bot.bridge.send(self.bot.config['main_room'], ctx.message, alert=alert)

        for platform in self.bot.platforms.keys():
            if parent_id:
                await self.bot.bridge.send(
                    self.bot.config['alerts_room'], ctx.message, platform=platform, id_override=parent_id, alert=alert
                )
            if not level == 'advisory' and parent_id_2:
                await self.bot.bridge.send(
                    self.bot.config['main_room'], ctx.message, platform=platform, id_override=parent_id_2, alert=alert
                )

        embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
        embed.description = selector.get("success_body")
        embed.colour = self.bot.colors.success

        await msg.edit(embed=embed)

    @moderation.subcommand(
        description=language.desc('moderation.advisory'),
        description_localizations=language.slash_desc('moderation.advisory')
    )
    @application_checks.guild_only()
    @restrictions.moderator()
    @restrictions.not_banned()
    @restrictions.no_admin_perms()
    async def advisory(
            self, ctx: nextcord.Interaction,
            risk_type: str = slash.option('moderation.alert.risk_type'),
            message: str = slash.option('moderation.alert.message')
    ):
        selector = language.get_selector('moderation.alert', userid=ctx.user.id)

        risk_type = risk_type.lower()
        if not risk_type in self.bot.bridge.alert.titles.keys():
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')
        if risk_type == 'drill':
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_drill")}')
        level = 'advisory'
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.get("send_title")}',
            description=selector.fget("send_body", values={"level": level}),
            color=self.bot.colors.warning
        )
        embed.set_footer(
            text=selector.get("misuse_unifier") if self.bot.user.id == 1187093090415149056 else selector.get("misuse")
        )
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("send"),
                    custom_id='accept'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel","commons.navigation"),
                    custom_id='cancel'
                )
            )
        )

        msg = await ctx.send(embed=embed, view=components)
        msg = await msg.fetch()

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=None)

        await interaction.response.edit_message(view=None)

        if interaction.data['custom_id'] == 'cancel':
            return

        embed.title = embed.title.replace(self.bot.ui_emojis.warning, self.bot.ui_emojis.loading, 1)
        await msg.edit(embed=embed)

        alert = {
            'type': risk_type,
            'severity': level,
            'description': message
        }

        parent_id = await self.bot.bridge.send(self.bot.config['alerts_room'], ctx.message, alert=alert)

        for platform in self.bot.platforms.keys():
            if parent_id:
                await self.bot.bridge.send(
                    self.bot.config['alerts_room'], ctx.message, platform=platform, id_override=parent_id, alert=alert
                )

        embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
        embed.description = selector.get("success_body")
        embed.colour = self.bot.colors.success

        await msg.edit(embed=embed)

    async def alert_search(self, query: str):
        possible = []
        for risk in self.bot.bridge.alert.titles.keys():
            if query in risk:
                possible.append(risk)

        return possible

    @alert.on_autocomplete("risk_type")
    async def alert_autocomplete(self, ctx: nextcord.Interaction, risk_type: str):
        return await ctx.response.send_autocomplete(await self.alert_search(risk_type))

    @advisory.on_autocomplete("risk_type")
    async def advisory_autocomplete(self, ctx: nextcord.Interaction, risk_type: str):
        return await ctx.response.send_autocomplete(await self.alert_search(risk_type))

    async def cog_command_error(self, ctx: nextcord.Interaction, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Moderation(bot))
