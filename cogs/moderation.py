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
import time
import hashlib
import datetime
from nextcord.ext import commands
import traceback
import ujson as json
from utils import log, ui
from utils import restrictions as r

override_st = False

with open('config.json', 'r') as file:
    data = json.load(file)

externals = data["external"]

restrictions = r.Restrictions()

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
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)
        restrictions.attach_bot(self.bot)

    @commands.command(aliases=['ban'],description='Blocks a user or server from bridging messages to your server.')
    @commands.has_permissions(ban_members=True)
    async def restrict(self,ctx,*,target):
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id:
                return await ctx.send('You can\'t restrict yourself :thinking:')
            if userid==ctx.guild.id:
                return await ctx.send('You can\'t restrict your own server :thinking:')
        except:
            userid = target
            if not len(userid) == 26:
                return await ctx.send('Invalid user/server!')
        if userid in self.bot.moderators:
            return await ctx.send('UniChat moderators are immune to blocks!\n(Though, do feel free to report anyone who abuses this immunity.)')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        else:
            self.bot.db['blocked'].update({f'{ctx.guild.id}':[]})
        if userid in banlist:
            return await ctx.send('User/server already banned!')
        self.bot.db['blocked'][f'{ctx.guild.id}'].append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send('User/server can no longer forward messages to this channel!')

    @commands.command(hidden=True,description='Blocks a user or server from bridging messages through Unifier.')
    @restrictions.moderator()
    async def globalban(self, ctx, target, duration=None, *, reason=None):
        if not ctx.author.id in self.bot.moderators:
            return
        rtt_msg = None
        rtt_msg_content = ''
        if ctx.message.reference:
            msg = ctx.message.reference.cached_message
            if not msg:
                try:
                    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                except:
                    pass
            if msg:
                try:
                    rtt_msg = await self.bot.bridge.fetch_message(msg.id)
                except:
                    return await ctx.send('Could not find message in cache!')
                rtt_msg_content = msg.content
            else:
                return await ctx.send('Could not find message in cache!')
        if rtt_msg:
            if not duration and not reason:
                reason = 'no reason given'
            elif duration and not reason:
                reason = duration
            else:
                reason = duration + ' ' + reason
            duration = target
            target = str(rtt_msg.author_id)
        else:
            if not duration:
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
                return await ctx.send('Invalid duration!')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id and not override_st:
                return await ctx.send('You can\'t restrict yourself :thinking:')
        except:
            userid = target
            if not len(userid) == 26:
                return await ctx.send('Invalid user/server!')
        disclose = False
        if reason.startswith('-disclose'):
            reason = reason.replace('-disclose','',1)
            disclose = True
            while reason.startswith(' '):
                reason = reason.replace(' ','',1)
        discreet = False
        if reason.startswith('-discreet'):
            reason = reason.replace("-discreet", "", 1)
            discreet = True
            while reason.startswith(' '):
                reason = reason.replace(' ','',1)
        if userid in self.bot.moderators and not ctx.author.id == self.bot.config['owner'] and not override_st:
            if not userid == ctx.author.id or not override_st:
                return await ctx.send('You cannot punish other moderators!')
        if userid==self.bot.user.id:
            return await ctx.send('are you fr')
        banlist = self.bot.db['banned']
        if userid in banlist:
            return await ctx.send('User/server already banned!')
        ct = round(time.time())
        nt = ct + duration
        if forever:
            nt = 0
        self.bot.db['banned'].update({f'{userid}':nt})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        if ctx.author.discriminator=='0':
            mod = f'@{ctx.author.name}'
        else:
            mod = f'{ctx.author.name}#{ctx.author.discriminator}'
        embed = nextcord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=reason,color=0xffcc00,timestamp=datetime.datetime.now(datetime.UTC))
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if rtt_msg:
            if len(rtt_msg_content)==0:
                rtt_msg_content = '[no content]'
            if len(rtt_msg_content) > 1024:
                rtt_msg_content = rtt_msg_content[:-(len(rtt_msg_content)-1024)]
            embed.add_field(name='Offending message',value=rtt_msg_content,inline=False)
        if forever:
            embed.colour = 0xff0000
            embed.add_field(name='Actions taken',value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',inline=False)
        else:
            embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',inline=False)
        embed.add_field(name='Did we make a mistake?',value=f'If you think we didn\'t make the right call, you can always appeal your ban using `{self.bot.command_prefix}!appeal`.',inline=False)
        user = self.bot.get_user(userid)
        if not user:
            try:
                user = self.bot.revolt_client.get_user(userid)
                await user.send(f'## {embed.title}\n{embed.description}\n\n**Actions taken**\n{embed.fields[0].value}')
                return await ctx.send('global banned <:nevheh:990994050607906816>')
            except:
                return await ctx.send('global banned <:nevheh:990994050607906816>')
        if user:
            try:
                await user.send(embed=embed)
            except:
                pass

        content = ctx.message.content
        ctx.message.content = ''
        embed = nextcord.Embed(description='A user was recently banned from Unifier!',color=0xff0000)
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

        ctx.message.embeds = [embed]
        
        if not discreet:
            await self.bot.bridge.send("main", ctx.message, 'discord', system=True)
        for platform in externals:
            await self.bot.bridge.send("main", ctx.message, platform, system=True)

        ctx.message.embeds = []
        ctx.message.content = content

        await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.add_modlog(1, user.id, reason, ctx.author.id))
        actions_count, actions_count_recent = self.bot.bridge.get_modlogs_count(user.id)
        log_embed = nextcord.Embed(title='User banned', description=reason, color=0xff0000, timestamp=datetime.datetime.now(datetime.UTC))
        log_embed.add_field(name='Expiry', value=f'never' if forever else f'<t:{nt}:R>', inline=False)
        log_embed.set_author(name=f'@{user.name}',icon_url=user.avatar.url if user.avatar else None)
        log_embed.add_field(
            name='User modlogs info',
            value=f'This user has **{actions_count_recent["warns"]}** recent warnings ({actions_count["warns"]} in ' +
                  f'total) and **{actions_count_recent["bans"]}** recent bans ({actions_count["bans"]} in ' +
                  'total) on record.',
            inline=False)
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    custom_id='delete',
                    label='Delete message',
                    emoji='\U0001F5D1'
                )
            )
        )
        resp_msg = await ctx.send(
            'User was global banned. They may not use Unifier for the given time period.',
            embed=log_embed,
            reference=ctx.message,
            view=components if rtt_msg else None
        )

        if not rtt_msg:
            return

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==resp_msg.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=30.0)
        except:
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        custom_id='delete',
                        label='Delete message',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            return await resp_msg.edit(view=components)
        else:
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        custom_id='delete',
                        label='Delete message',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            await resp_msg.edit(view=components)
            await interaction.response.defer(ephemeral=True)
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        custom_id='delete',
                        label='Original message deleted',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            try:
                await self.bot.bridge.delete_parent(rtt_msg.id)
                if rtt_msg.webhook:
                    raise ValueError()
                await resp_msg.edit(view=components)
                return await interaction.edit_original_message(
                    content=f'{self.bot.ui_emojis.success} Deleted message (parent deleted, copies will follow)'
                )
            except:
                try:
                    deleted = await self.bot.bridge.delete_copies(rtt_msg.id)
                    await resp_msg.edit(view=components)
                    return await interaction.edit_original_message(
                        content=f'{self.bot.ui_emojis.success} Deleted message ({deleted} copies deleted)'
                    )
                except:
                    traceback.print_exc()
                    return await interaction.edit_original_message(
                        content=f'{self.bot.ui_emojis.error} Something went wrong.'
                    )

    @commands.command(hidden=True,description='Blocks a user from using Unifier.')
    @restrictions.owner()
    async def fullban(self,ctx,target):
        if not ctx.author.id in self.bot.admins:
            return

        user = self.bot.get_user(target.replace('<@','',1).replace('>','',1).replace('!','',1))

        if user:
            target = user.id
        else:
            try:
                target = int(target)
            except:
                return await ctx.send('Invalid user!')

        if target==ctx.author.id:
            return await ctx.send(f'{self.bot.ui_emojis.error} You cannot ban yourself :thinking:')

        if target==self.bot.config['owner']:
            return await ctx.send(f'{self.bot.ui_emojis.error} You cannot ban the owner :thinking:')

        if target in self.bot.db['fullbanned']:
            self.bot.db['fullbanned'].remove(target)
            await ctx.send(f'{self.bot.ui_emojis.success} User has been unbanned from the bot.')
        else:
            self.bot.db['fullbanned'].append(target)
            await ctx.send(f'{self.bot.ui_emojis.success} User has been banned from the bot.')

    @commands.command(aliases=['unban'],description='Unblocks a user or server from bridging messages to your server.')
    @commands.has_permissions(ban_members=True)
    async def unrestrict(self,ctx,target):
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            userid = target
            if not len(target) == 26:
                return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user/server!')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        if not userid in banlist:
            return await ctx.send(f'{self.bot.ui_emojis.error} User/server not banned!')
        self.bot.db['blocked'][f'{ctx.guild.id}'].remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} User/server can now forward messages to this channel!')

    @commands.command(hidden=True,description='Unblocks a user or server from bridging messages through Unifier.')
    @restrictions.moderator()
    async def globalunban(self,ctx,*,target):
        if not ctx.author.id in self.bot.moderators:
            return
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id and not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} You can\'t unban yourself :thinking:')
        except:
            userid = target
            if not len(target) == 26:
                return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user/server!')
        banlist = self.bot.db['banned']
        if not f'{userid}' in list(banlist.keys()):
            if f'{userid}' in list(self.bot.bridge.secbans.keys()):
                self.bot.bridge.secbans.pop(f'{userid}')
                return await ctx.send(f'{self.bot.ui_emojis.success} User has been unbanned.')
            return await ctx.send('User/server not banned!')
        self.bot.db['banned'].pop(f'{userid}')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} User has been unbanned.')

    @commands.command(description='Bans a user from appealing their ban.')
    @restrictions.admin()
    async def appealban(self,ctx,*,target):
        if not ctx.author.id in self.bot.admins:
            return
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id and not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} You can\'t ban yourself :thinking:')
        except:
            userid = target
        if userid in self.bot.db['appealban']:
            self.bot.db['appealban'].remove(userid)
            await ctx.send(f'{self.bot.ui_emojis.success} User can now appeal bans.')
        else:
            self.bot.db['appealban'].append(userid)
            await ctx.send(f'{self.bot.ui_emojis.success} User can no longer appeal bans.')
        self.bot.db.save_data()

    @commands.command(description='Appeals your ban, if you have one.')
    async def appeal(self,ctx):
        gbans = self.bot.db['banned']
        banned = False

        if ctx.guild:
            return await ctx.send(f'{self.bot.ui_emojis.error} You can only appeal your ban in DMs.')

        if f'{ctx.author.id}' in list(gbans.keys()):
            ct = time.time()
            if f'{ctx.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{ctx.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{ctx.author.id}')
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    banned = True

        if not banned:
            return await ctx.send(f'{self.bot.ui_emojis.error} You don\'t have an active ban!')

        if ctx.author.id in self.bot.db['appealban']:
            return await ctx.send(f'{self.bot.ui_emojis.error} You cannot appeal this ban, contact staff for more info.')

        actions, _ = self.bot.bridge.get_modlogs(ctx.author.id)

        if len(actions['bans'])==0:
            return await ctx.send(
                f'{self.bot.ui_emojis.error} You\'re currently banned, but we couldn\'t find the ban reason. Contact moderators directly to appeal.'
            )

        ban = actions['bans'][len(actions['bans'])-1]

        embed = nextcord.Embed(
            title='Global restriction',description=ban['reason'],color=0xff0000
        )
        embed.set_author(name=f'@{ctx.author.name}', icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        components = ui.MessageComponents()
        components.add_rows(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green,
                    label='Yes',
                    custom_id='yes'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label='No',
                    custom_id='no'
                )
            )
        )
        msg = await ctx.send(f'{self.bot.ui_emojis.warning} Please confirm that this is the ban you\'re appealing.',embed=embed,view=components)

        def check(interaction):
            return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=None)

        if not interaction.data['custom_id']=='yes':
            return await interaction.response.edit_message(view=None)

        await msg.edit(view=None)

        modal = nextcord.ui.Modal(title='Appeal ban', auto_defer=False)
        modal.add_item(
            nextcord.ui.TextInput(
                style=nextcord.TextInputStyle.paragraph, label='Appeal reason',
                placeholder='Why should we consider your appeal?',
                required=True
            )
        )
        modal.add_item(
            nextcord.ui.TextInput(
                style=nextcord.TextInputStyle.short, label='Sign with your username',
                placeholder='Sign this only if your appeal is in good faith.',
                required=True, min_length=len(ctx.author.name), max_length=len(ctx.author.name)
            )
        )
        await interaction.response.send_modal(modal)

        while True:
            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=600)
            except:
                return await msg.edit(view=None)
            if interaction.data['components'][1]['components'][0]['value'].lower() == ctx.author.name.lower():
                break

        embed = nextcord.Embed(
            title='Ban appeal - reason is as follows',
            description=interaction.data['components'][0]['components'][0]['value'],
            color=self.bot.colors.gold
        )
        embed.set_author(name=f'@{ctx.author.name}',icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.add_field(name='Original ban reason',value=ban['reason'],inline=False)
        guild = self.bot.get_guild(self.bot.config['home_guild'])
        ch = guild.get_channel(self.bot.config['reports_channel'])
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label='Reject', custom_id=f'apreject_{ctx.author.id}',
                disabled=False, emoji=self.bot.ui_emojis.error
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label='Accept & unban', custom_id=f'apaccept_{ctx.author.id}',
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
                name=f'Discussion: @{ctx.author.name}',
                auto_archive_duration=10080
            )
            self.bot.db['report_threads'].update({str(msg.id): thread.id})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        except:
            pass
        return await interaction.response.send_message(
            (
                f"# {self.bot.ui_emojis.success} Your appeal was submitted!\nWe\'ll get back to you once the moderators have"+
                " agreed on a decision. Please be patient and respectful towards moderators while they review your "+
                "appeal."
            ),
            ephemeral=True
        )

    @commands.command(aliases=['account_standing'],description='Shows your instance account standing.')
    async def standing(self,ctx,*,target=None):
        if target and not ctx.author.id in self.bot.moderators:
            target = None
        menu = 0
        page = 0
        is_self = False
        if target:
            orig_id = int(target.replace('<@', '', 1).replace('>', '', 1).replace('!', '', 1))
            try:
                target = self.bot.get_user(int(target.replace('<@','',1).replace('>','',1).replace('!','',1)))
            except:
                return await ctx.send('Invalid target!')
        else:
            orig_id = ctx.author.id
            target = ctx.author
            is_self = True
        if target:
            if target.id == ctx.author.id:
                is_self = True
        embed = nextcord.Embed(
            title='All good!',
            description='You\'re on a clean or good record. Thank you for upholding your Unifier instance\'s rules!\n'+
            '\n:white_check_mark: :white_large_square: :white_large_square: :white_large_square: :white_large_square:',
            color=0x00ff00)

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
            embed.title = "SUSPENDED"
            embed.colour = 0xff0000
            embed.description = (
                    'You\'ve been ' + ('permanently' if noexpiry else 'temporarily') + ' suspended from this Unifier '+
                    'instance.\n\n:white_large_square: :white_large_square: :white_large_square: :white_large_square:'+
                    ' :octagonal_sign:'
            )
        elif 2 < judgement <= 5:
            embed.title = "Fair"
            embed.colour = 0xffff00
            embed.description = (
                    'You\'ve broken one or more rules recently. Please follow the rules next time!' +
                    '\n\n:white_large_square: :warning: :white_large_square: :white_large_square: :white_large_square:'
            )
        elif 5 < judgement <= 10:
            embed.title = "Caution"
            embed.colour = 0xffcc00
            embed.description = (
                    'You\'ve broken many rules recently. Moderators may issue stronger punishments.' +
                    '\n\n:white_large_square: :white_large_square: :biohazard: :white_large_square: :white_large_square:'
            )
        elif judgement > 10:
            embed.title = "WARNING"
            embed.colour = 0xff00dd
            embed.description = (
                    'You\'ve severely or frequently violated rules. A permanent suspension may be imminent.' +
                    '\n\n:white_large_square: :white_large_square: :white_large_square: :bangbang: :white_large_square:'
            )
        if target:
            embed.set_author(name=f'@{target.name}\'s account standing', icon_url=target.avatar.url if target.avatar else None)
        else:
            embed.set_author(name=f'{orig_id}\'s account standing')
        if target:
            if target.bot or target.id in self.bot.db['fullbanned']:
                if target.bot:
                    embed.title = 'Bot account'
                    embed.description = 'This is a bot. Bots cannot have an account standing.'
                    embed.colour = 0xcccccc
                else:
                    embed.title = 'COMPLETELY SUSPENDED'
                    embed.description = ('This user has been completely suspended from the bot.\n'+
                                         'Unlike global bans, the user may also not interact with any part of the bot.')
                    embed.colour = 0xff0000
                return await ctx.send(embed=embed)
        elif orig_id in self.bot.db['fullbanned']:
            embed.title = 'COMPLETELY SUSPENDED'
            embed.description = ('This user has been completely suspended from the bot.\n' +
                                 'Unlike global bans, the user may also not interact with any part of the bot.')
            embed.colour = 0xff0000
            return await ctx.send(embed=embed)
        msg = None
        interaction = None
        while True:
            components = None
            if menu == 0:
                embed.add_field(name='Recent punishments',
                                value=f'{actions_count_recent["warns"]} warnings, {actions_count_recent["bans"]} bans',
                                inline=False)
                embed.add_field(name='All-time punishments',
                                value=f'{actions_count["warns"]} warnings, {actions_count["bans"]} bans',
                                inline=False)
                embed.set_footer(text='Standing is calculated based on recent and all-time punishments. Recent '+
                                 'punishments will have a heavier effect on your standing.')
                components = ui.MessageComponents()
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='warns',
                            label='Warnings',
                            emoji='\U000026A0',
                            style=nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='bans',
                            label='Bans',
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
                        name=f':warning: Warning #{len(actions["warns"])-i}',
                        value=actions['warns'][len(actions['warns'])-i-1]['reason'],
                        inline=False
                    )
                    if i >= len(actions['warns']) - 1:
                        break
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='back',
                            label='Back',
                            style=nextcord.ButtonStyle.gray
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=page==0
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=((page+1)*5)+1 >= len(actions['warns'])
                        )
                    ) if len(embed.fields) >= 1 else ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        )
                    )
                )
                if len(embed.fields) == 0:
                    embed.add_field(name='No warnings',value='There\'s no warnings on record. Amazing!')
                embed.set_footer(text=f'Page {page+1}')
            elif menu == 2:
                while (page * 5) + 1 >= len(actions['bans']) and page > 0:
                    page -= 1
                for i in range(page * 5, (page + 1) * 5):
                    if len(actions['bans']) == 0 or len(actions['bans'])-i-1 < 0:
                        break
                    embed.add_field(
                        name=f':no_entry_sign: Ban #{len(actions["bans"]) - i}',
                        value=actions['bans'][len(actions['bans']) - i - 1]['reason'],
                        inline=False
                    )
                    if i >= len(actions['bans']) - 1:
                        break
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='back',
                            label='Back',
                            style=nextcord.ButtonStyle.gray
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=page==0
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=((page+1)*5)+1 >= len(actions['bans'])
                        )
                    ) if len(embed.fields) >= 1 else ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        nextcord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=nextcord.ButtonStyle.blurple,
                            disabled=True
                        )
                    )
                )
                if len(embed.fields) == 0:
                    embed.add_field(name='No bans', value='There\'s no bans on record. Amazing!')
                embed.set_footer(text=f'Page {page + 1}')
            if not msg:
                if ctx.message.guild and is_self:
                    msg = await ctx.author.send(embed=embed, view=components)
                    await ctx.send('Your account standing has been DMed to you.')
                else:
                    msg = await ctx.send(embed=embed, view=components)
            else:
                if interaction:
                    await interaction.response.edit_message(embed=embed,view=components)
                else:
                    await msg.edit(embed=embed,view=components)
            embed.clear_fields()

            def check(interaction):
                return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

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

    @commands.command(aliases=['guilds'],description='Lists all servers connected to a given room.')
    async def servers(self,ctx,*,room='main'):
        try:
            data = self.bot.db['rooms'][room]
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        text = ''
        for guild_id in data:
            try:
                name = self.bot.get_guild(int(guild_id)).name
            except:
                continue
            if len(text)==0:
                text = f'- {name} (`{guild_id}`)'
            else:
                text = f'{text}\n- {name} (`{guild_id}`)'
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.rooms} Servers connected to `{room}`',description=text)
        await ctx.send(embed=embed)

    @commands.command(hidden=True,description='Warns a user.')
    @restrictions.moderator()
    async def warn(self,ctx,*,target):
        rtt_msg = None
        rtt_msg_content = ''
        if ctx.message.reference:
            msg = ctx.message.reference.cached_message
            if not msg:
                try:
                    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                except:
                    pass
            if msg:
                try:
                    rtt_msg = await self.bot.bridge.fetch_message(msg.id)
                except:
                    return await ctx.send(f'{self.bot.ui_emojis.error} Could not find message in cache!')
                rtt_msg_content = msg.content
            else:
                return await ctx.send(f'{self.bot.ui_emojis.error} Could not find message in cache!')
        if rtt_msg:
            reason = target
            target = str(rtt_msg.author_id)
        else:
            parts = target.split(' ',1)
            if len(parts)==2:
                reason = parts[1]
                target = parts[0]
            else:
                return await ctx.send(f'{self.bot.ui_emojis.error} You need to have a reason to warn this user.')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id and not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} You can\'t warn yourself :thinking:')
        except:
            userid = target
            if not len(userid)==26:
                return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user/server!')
        if userid in self.bot.moderators and not ctx.author.id==self.bot.config['owner']:
            if not userid == ctx.author.id or not override_st:
                return await ctx.send(f'{self.bot.ui_emojis.error} You cannot punish other moderators!')
        if userid==self.bot.user.id:
            return await ctx.send('are you fr')
        if ctx.author.discriminator=='0':
            mod = f'@{ctx.author.name}'
        else:
            mod = f'{ctx.author.name}#{ctx.author.discriminator}'
        embed = nextcord.Embed(title=f'You\'ve been __warned__ by {mod}!',description=reason,color=0xffff00,timestamp=datetime.datetime.now(datetime.UTC))
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if rtt_msg:
            if len(rtt_msg_content)==0:
                rtt_msg_content = '[no content]'
            if len(rtt_msg_content) > 1024:
                rtt_msg_content = rtt_msg_content[:-(len(rtt_msg_content)-1024)]
            embed.add_field(name='Offending message',value=rtt_msg_content,inline=False)
        embed.add_field(
            name='Actions taken',
            value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.',
            inline=False
        )
        user = self.bot.get_user(userid)
        if not user:
            try:
                user = self.bot.revolt_client.get_user(userid)
                await user.send(
                    f'## {embed.title}\n{embed.description}\n\n**Actions taken**\n{embed.fields[0].value}')
                return await ctx.send(f'{self.bot.ui_emojis.success} User has been warned and notified.')
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user! (servers can\'t be warned, warn their staff instead')
        if user.bot:
            return await ctx.send('...why would you want to warn a bot?')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.bridge.add_modlog(0,user.id,reason,ctx.author.id))
        actions_count, actions_count_recent = self.bot.bridge.get_modlogs_count(user.id)
        log_embed = nextcord.Embed(title='User warned',description=reason,color=0xffcc00,timestamp=datetime.datetime.now(datetime.UTC))
        log_embed.set_author(name=f'@{user.name}', icon_url=user.avatar.url if user.avatar else None)
        log_embed.add_field(
            name='User modlogs info',
            value=f'This user has **{actions_count_recent["warns"]}** recent warnings ({actions_count["warns"]} in '+
                  f'total) and **{actions_count_recent["bans"]}** recent bans ({actions_count["bans"]} in '+
                  'total) on record.',
            inline=False)
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    custom_id='delete',
                    label='Delete message',
                    emoji='\U0001F5D1'
                )
            )
        )
        try:
            await user.send(embed=embed)
            resp_msg = await ctx.send(
                f'{self.bot.ui_emojis.success} User has been warned and notified.',
                embed=log_embed,
                reference=ctx.message,
                view=components if rtt_msg else None
            )
        except:
            resp_msg = await ctx.send(f'{self.bot.ui_emojis.success} User has DMs with bot disabled. Warning will be logged.',embed=log_embed,view=components)

        if not rtt_msg:
            return

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==resp_msg.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=30.0)
        except:
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        custom_id='delete',
                        label='Delete message',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            return await resp_msg.edit(view=components)
        else:
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        custom_id='delete',
                        label='Delete message',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            await resp_msg.edit(view=components)
            await interaction.response.defer(ephemeral=True)
            components = ui.MessageComponents()
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        custom_id='delete',
                        label='Original message deleted',
                        emoji='\U0001F5D1',
                        disabled=True
                    )
                )
            )
            try:
                await self.bot.bridge.delete_parent(rtt_msg.id)
                if rtt_msg.webhook:
                    raise ValueError()
                await resp_msg.edit(view=components)
                return await interaction.edit_original_message(
                    content=f'{self.bot.ui_emojis.success} Deleted message (parent deleted, copies will follow)'
                )
            except:
                try:
                    deleted = await self.bot.bridge.delete_copies(rtt_msg.id)
                    await resp_msg.edit(view=components)
                    return await interaction.edit_original_message(
                        content=f'{self.bot.ui_emojis.success} Deleted message ({deleted} copies deleted)'
                    )
                except:
                    traceback.print_exc()
                    return await interaction.edit_original_message(
                        content=f'{self.bot.ui_emojis.error} Something went wrong.'
                    )

    @commands.command(hidden=True,description='Deletes a logged warning.')
    @restrictions.moderator()
    async def delwarn(self,ctx,target,index):
        try:
            index = int(index) - 1
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Invalid index!')
        if index < 0:
            return await ctx.send('what.')
        target = self.bot.get_user(int(target.replace('<@','',1).replace('!','',1).replace('>','',1)))
        try:
            actions, _ = self.bot.bridge.get_modlogs(target.id)
            warn = actions['warns'][index]
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Could not find action!')
        embed = nextcord.Embed(title='Warning deleted',description=warn['reason'],color=0xffcc00)
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
            await ctx.send(f'{self.bot.ui_emojis.success} Warning was deleted!', embed=embed)
        else:
            await ctx.send(f'{self.bot.ui_emojis.error} Could not find warning - maybe the index was too high?')

    @commands.command(hidden=True,description='Deletes a logged ban. Does not unban the user.')
    @restrictions.moderator()
    async def delban(self, ctx, target, index):
        try:
            index = int(index) - 1
        except:
            return await ctx.send('Invalid index!')
        if index < 0:
            return await ctx.send('what.')
        target = self.bot.get_user(int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)))
        try:
            actions, _ = self.bot.bridge.get_modlogs(target.id)
            ban = actions['bans'][index]
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Could not find action!')
        embed = nextcord.Embed(title='Ban deleted', description=ban['reason'], color=0xff0000)
        embed.set_author(name=f'@{target.name}', icon_url=target.avatar.url if target.avatar else None)
        embed.set_footer(text='WARNING: This does NOT unban the user.')
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
            await ctx.send(f'{self.bot.ui_emojis.success} Ban was deleted!', embed=embed)
        else:
            await ctx.send(f'{self.bot.ui_emojis.error} Could not find ban - maybe the index was too high?')

    @commands.command(hidden=True,description="Changes a given user's nickname.")
    @restrictions.moderator()
    async def anick(self, ctx, target, *, nickname=''):
        try:
            userid = int(target.replace('<@', '').replace('!', '').replace('>', ''))
        except ValueError:
            if len(target)==26:
                userid = target
            else:
                return await ctx.send(f"{self.bot.ui_emojis.error} Invalid user mention.")

        # Update or remove the nickname in the database
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(str(userid), None)
        else:
            self.bot.db['nicknames'][str(userid)] = nickname

        # Save changes to the database
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

        await ctx.send(f'{self.bot.ui_emojis.success} Nickname updated.')

    @commands.command(hidden=True,description='Locks Unifier Bridge down.')
    @restrictions.moderator()
    async def bridgelock(self,ctx):
        if not hasattr(self.bot, 'bridge'):
            return await ctx.send(f'{self.bot.ui_emojis.error} Bridge already locked down.')
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.warning} Lock bridge down?',
                               description='This will shut down Revolt and Guilded clients, as well as unload the entire bridge extension.\nLockdown can only be lifted by admins.',
                               color=0xffcc00)
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,label='Lockdown',custom_id='lockdown'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray, label='Cancel'
                )
            )
        )
        components_inac = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red, label='Lockdown', custom_id='lockdown',disabled=True
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray, label='Cancel', disabled=True
                )
            )
        )
        msg = await ctx.send(embed=embed,view=components)

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=30)
        except:
            return await msg.edit(view=components_inac)

        if not interaction.data['custom_id']=='lockdown':
            return await interaction.response.edit_message(view=components_inac)

        embed.title = ':warning: FINAL WARNING!!! :warning:'
        embed.description = 'LOCKDOWNS CANNOT BE REVERSED BY NON-ADMINS!\nDo NOT lock down the chat if you don\'t know what you\'re doing!'
        embed.colour = 0xff0000

        await interaction.response.edit_message(embed=embed)

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=30)
        except:
            return await msg.edit(view=components_inac)

        await interaction.response.edit_message(view=components_inac)

        if not interaction.data['custom_id']=='lockdown':
            return

        self.logger.warn(f'Bridge lockdown issued by {ctx.author.id}!')

        try:
            self.logger.info("Shutting down Revolt client...")
            await self.bot.revolt_session.close()
            del self.bot.revolt_client
            del self.bot.revolt_session
            self.bot.unload_extension('cogs.bridge_revolt')
            self.logger.info("Revolt client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Shutdown failed.")
        try:
            self.logger.info("Shutting down Guilded client...")
            await self.bot.guilded_client.close()
            self.bot.guilded_client_task.cancel()
            del self.bot.guilded_client
            self.bot.unload_extension('cogs.bridge_guilded')
            self.logger.info("Guilded client has been shut down.")
        except Exception as e:
            if not isinstance(e, AttributeError):
                self.logger.exception("Shutdown failed.")
        self.logger.info("Backing up message cache...")
        await self.bot.bridge.backup()
        self.logger.info("Backup complete")
        self.logger.info("Disabling bridge...")
        del self.bot.bridge
        self.bot.unload_extension('cogs.bridge')
        self.logger.info("Bridge disabled")
        self.logger.info("Lockdown complete")
        embed.title = f'{self.bot.ui_emojis.warning} LOCKDOWN COMPLETED'
        embed.description = 'Bridge has been locked down.'
        embed.colour = 0xff0000
        await msg.edit(embed=embed)

    @commands.command(hidden=True,description='Removes Unifier Bridge lockdown.')
    @restrictions.admin()
    async def bridgeunlock(self,ctx):
        if not ctx.author.id in self.bot.admins:
            return
        try:
            self.bot.load_extension('cogs.bridge')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Bridge already online.')
        try:
            await self.bot.bridge.restore()
            self.logger.info('Restored ' + str(len(self.bot.bridge.bridged)) + ' messages')
        except:
            traceback.print_exc()
        if 'revolt' in externals:
            try:
                self.bot.load_extension('cogs.bridge_revolt')
            except Exception as e:
                if not isinstance(e, nextcord.ext.commands.errors.ExtensionAlreadyLoaded):
                    traceback.print_exc()
        if 'guilded' in externals:
            try:
                self.bot.load_extension('cogs.bridge_guilded')
            except Exception as e:
                if not isinstance(e, nextcord.ext.commands.errors.ExtensionAlreadyLoaded):
                    traceback.print_exc()
        await ctx.send(f'{self.bot.ui_emojis.success} Lockdown removed')

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Moderation(bot))
