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

import discord
import time
import hashlib
from datetime import datetime
from discord.ext import commands
import traceback
import json
from utils import log

with open('config.json', 'r') as file:
    data = json.load(file)

externals = data["external"]

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
            total += (multi)
        else:
            raise ValueError('invalid identifier')
    return total

class Moderation(commands.Cog, name=":shield: Moderation"):
    """Moderation allows server moderators and UniChat moderators to punish bad actors.

    Developed by Green and ItsAsheer"""
    def __init__(self,bot):
        self.bot = bot
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)

    def add_modlog(self, type, user, reason, moderator):
        t = time.time()
        try:
            self.bot.db['modlogs'][f'{user}'].append({
                'type': type,
                'reason': reason,
                'time': t,
                'mod': moderator
            })
        except:
            self.bot.db['modlogs'].update({
                f'{user}': [{
                    'type': type,
                    'reason': reason,
                    'time': t,
                    'mod': moderator
                }]
            })
        self.bot.db.save_data()

    def get_modlogs(self, user):
        t = time.time()

        actions = {
            'warns': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 0],
            'bans': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 1]
        }
        actions_recent = {
            'warns': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 0 and log['time'] - t <= 2592000],
            'bans': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 1 and log['time'] - t <= 2592000]
        }

        return actions, actions_recent

    def get_modlogs_count(self, user):
        actions, actions_recent = self.get_modlogs(user)
        return {
            'warns': len(actions['warns']), 'bans': len(actions['bans'])
        }, {
            'warns': len(actions_recent['warns']), 'bans': len(actions_recent['bans'])
        }

    @commands.command(aliases=['ban'])
    async def restrict(self,ctx,*,target):
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members):
            return await ctx.send('You cannot restrict members/servers.')
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
        self.bot.db.save_data()
        await ctx.send('User/server can no longer forward messages to this channel!')

    @commands.command(hidden=True)
    async def globalban(self, ctx, target, duration, *, reason='no reason given'):
        if not ctx.author.id in self.bot.moderators:
            return
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
            if userid==ctx.author.id:
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
        if userid in self.bot.moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('Moderators can\'t moderate other moderators!')
        banlist = self.bot.db['banned']
        if userid in banlist:
            return await ctx.send('User/server already banned!')
        ct = round(time.time())
        nt = ct + duration
        if forever:
            nt = 0
        self.bot.db['banned'].update({f'{userid}':nt})
        self.bot.db.save_data()
        if ctx.author.discriminator=='0':
            mod = f'@{ctx.author.name}'
        else:
            mod = f'{ctx.author.name}#{ctx.author.discriminator}'
        embed = discord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=reason,color=0xffcc00,timestamp=datetime.utcnow())
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if forever:
            embed.colour = 0xff0000
            embed.add_field(name='Actions taken',value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',inline=False)
        else:
            embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',inline=False)
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
        embed = discord.Embed(description='A user was recently banned from Unifier!',color=0xff0000)
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

        self.add_modlog(1, user.id, reason, ctx.author.id)
        actions_count, actions_count_recent = self.get_modlogs_count(user.id)
        log_embed = discord.Embed(title='User banned', description=reason, color=0xff0000, timestamp=datetime.utcnow())
        log_embed.add_field(name='Expiry', value=f'never' if forever else f'<t:{nt}:R>', inline=False)
        log_embed.set_author(name=f'@{user.name}',icon_url=user.avatar.url if user.avatar else None)
        log_embed.add_field(
            name='User modlogs info',
            value=f'This user has **{actions_count_recent["warns"]}** recent warnings ({actions_count["warns"]} in ' +
                  f'total) and **{actions_count_recent["bans"]}** recent bans ({actions_count["bans"]} in ' +
                  'total) on record.',
            inline=False)
        await ctx.send('User was global banned. They may not use Unifier for the given time period.',
                       embed=log_embed)

    @commands.command(aliases=['unban'])
    async def unrestrict(self,ctx,target):
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members):
            return await ctx.send('You cannot unrestrict members/servers.')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            userid = target
            if not len(target) == 26:
                return await ctx.send('Invalid user/server!')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        if not userid in banlist:
            return await ctx.send('User/server not banned!')
        self.bot.db['blocked'][f'{ctx.guild.id}'].remove(userid)
        self.bot.db.save_data()
        await ctx.send('User/server can now forward messages to this channel!')

    @commands.command(hidden=True)
    async def globalunban(self,ctx,*,target):
        if not ctx.author.id in self.bot.moderators:
            return
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            userid = target
            if not len(target) == 26:
                return await ctx.send('Invalid user/server!')
        banlist = self.bot.db['banned']
        if not f'{userid}' in list(banlist.keys()):
            return await ctx.send('User/server not banned!')
        self.bot.db['banned'].pop(f'{userid}')
        self.bot.db.save_data()
        await ctx.send('unbanned, nice')

    @commands.command(aliases=['account_standing'])
    async def standing(self,ctx,*,target=None):
        if target and not ctx.author.id in self.bot.moderators:
            target = None
        menu = 0
        page = 0
        is_self = False
        if target:
            try:
                target = self.bot.get_user(int(target.replace('<@','',1).replace('>','',1).replace('!','',1)))
            except:
                return await ctx.send('Invalid target!')
        else:
            target = ctx.author
            is_self = True
        embed = discord.Embed(
            title='All good!',
            description='You\'re on a clean or good record. Thank you for upholding your Unifier instance\'s rules!\n'+
            '\n:white_check_mark: :white_large_square: :white_large_square: :white_large_square: :white_large_square:',
            color=0x00ff00)
        if not is_self:
            embed.title = f'{target.global_name}\'s account standing'

        actions_count, actions_count_recent = self.get_modlogs_count(target.id)
        actions, _ = self.get_modlogs(target.id)

        gbans = self.bot.db['banned']
        ct = time.time()
        noexpiry = False
        if f'{ctx.author.id}' in list(gbans.keys()):
            banuntil = gbans[f'{ctx.author.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{ctx.author.id}')
                self.bot.db.save_data()
            if banuntil == 0:
                noexpiry = True

        judgement = (
            actions_count['bans'] + actions_count_recent['warns'] + (actions_count_recent['bans']*4)
        )
        if f'{ctx.author.id}' in list(gbans.keys()):
            embed.title = embed.title + "SUSPENDED"
            embed.colour = 0xff0000
            embed.description = (
                    'You\'ve been' + 'permanently' if noexpiry else 'temporarily' + 'suspended from this Unifier '+
                    'instance.\n\n:white_large_square: :white_large_square: :white_large_square: :white_large_square: :octagonal_sign:'
            )
        elif 2 < judgement <= 5:
            embed.title = embed.title + "Fair"
            embed.colour = 0xffff00
            embed.description = (
                    'You\'ve broken one or more rules recently. Please follow the rules next time!' +
                    '\n\n:white_large_square: :warning: :white_large_square: :white_large_square: :white_large_square:'
            )
        elif 5 < judgement <= 10:
            embed.title = embed.title + "Caution"
            embed.colour = 0xffcc00
            embed.description = (
                    'You\'ve broken many rules recently. Moderators may issue stronger punishments.' +
                    '\n\n:white_large_square: :white_large_square: :biohazard: :white_large_square: :white_large_square:'
            )
        else:
            embed.title = embed.title + "WARNING"
            embed.colour = 0xff00dd
            embed.description = (
                    'You\'ve severely or frequently violated rules. A permanent suspension may be imminent.' +
                    '\n\n:white_large_square: :white_large_square: :white_large_square: :bangbang: :white_large_square:'
            )
        embed.set_author(name=f'@{target.name}\'s account standing', icon_url=target.avatar.url if target.avatar else None)
        msg = None
        interaction = None
        while True:
            components = None
            if menu == 0:
                embed.add_field(name='Recent punishments',
                                value=f'{actions_count_recent["warns"]} warnings, {actions_count_recent["bans"]} bans',
                                inline=False)
                embed.add_field(name='All-time punishments',
                                value=f'{actions_count_recent["warns"]} warnings, {actions_count_recent["bans"]} bans',
                                inline=False)
                embed.set_footer(text='Standing is calculated based on recent and all-time punishments. Recent '+
                                 'punishments will have a heavier effect on your standing.')
                components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='warns',
                            label='Warnings',
                            emoji='\U000026A0',
                            style=discord.ButtonStyle.gray
                        ),
                        discord.ui.Button(
                            custom_id='bans',
                            label='Bans',
                            emoji='\U0001F6D1',
                            style=discord.ButtonStyle.red
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
                components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='back',
                            label='Back',
                            style=discord.ButtonStyle.gray
                        )
                    ),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=discord.ButtonStyle.blurple,
                            disabled=page==0
                        ),
                        discord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=discord.ButtonStyle.blurple,
                            disabled=((page+1)*5)+1 >= len(actions['warns'])
                        )
                    ) if len(embed.fields) >= 1 else discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=discord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        discord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=discord.ButtonStyle.blurple,
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
                components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='back',
                            label='Back',
                            style=discord.ButtonStyle.gray
                        )
                    ),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=discord.ButtonStyle.blurple,
                            disabled=page==0
                        ),
                        discord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=discord.ButtonStyle.blurple,
                            disabled=((page+1)*5)+1 >= len(actions['bans'])
                        )
                    ) if len(embed.fields) >= 1 else discord.ui.ActionRow(
                        discord.ui.Button(
                            custom_id='prev',
                            label='Previous',
                            style=discord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        discord.ui.Button(
                            custom_id='next',
                            label='Next',
                            style=discord.ButtonStyle.blurple,
                            disabled=True
                        )
                    )
                )
                if len(embed.fields) == 0:
                    embed.add_field(name='No warnings', value='There\'s no bans on record. Amazing!')
                embed.set_footer(text=f'Page {page + 1}')
            if not msg:
                if ctx.message.guild and is_self:
                    msg = await ctx.author.send(embed=embed, components=components)
                    await ctx.send('Your account standing has been DMed to you.')
                else:
                    msg = await ctx.send(embed=embed, components=components)
            else:
                if interaction:
                    await interaction.response.edit_message(embed=embed,components=components)
                else:
                    await msg.edit(embed=embed,components=components)
            embed.clear_fields()

            def check(interaction):
                return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

            try:
                interaction = await self.bot.wait_for('component_interaction',timeout=60,check=check)
            except:
                return await msg.edit(components=None)
            page = 0
            if interaction.custom_id == 'back':
                menu = 0
            elif interaction.custom_id == 'warns':
                menu = 1
            elif interaction.custom_id == 'bans':
                menu = 2
            elif interaction.custom_id == 'prev':
                page -= 1 if page >= 1 else 0
            elif interaction.custom_id == 'next':
                page += 1

    @commands.command(aliases=['guilds'])
    async def servers(self,ctx,*,room='main'):
        try:
            data = self.bot.db['rooms'][room]
        except:
            return await ctx.send(f'This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a list of all rooms.')
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
        embed = discord.Embed(title=f'Servers connected to `{room}`',description=text)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def warn(self,ctx,*,target):
        if not ctx.author.id in self.bot.moderators:
            return
        reason = ''
        parts = target.split(' ',1)
        if len(parts)==2:
            reason = parts[1]
            target = parts[0]
        else:
            return await ctx.send('You need to have a reason to warn this user.')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id:
                return await ctx.send('You can\'t warn yourself :thinking:')
        except:
            userid = target
            if not len(userid)==26:
                return await ctx.send('Invalid user/server!')
        if userid in self.bot.moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('ok guys no friendly fire pls thanks')
        banlist = self.bot.db['banned']
        if userid in banlist:
            return await ctx.send('User/server already banned!')
        if ctx.author.discriminator=='0':
            mod = f'@{ctx.author.name}'
        else:
            mod = f'{ctx.author.name}#{ctx.author.discriminator}'
        embed = discord.Embed(title=f'You\'ve been __warned__ by {mod}!',description=reason,color=0xffff00,timestamp=datetime.utcnow())
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.',inline=False)
        user = self.bot.get_user(userid)
        if not user:
            try:
                user = self.bot.revolt_client.get_user(userid)
                await user.send(
                    f'## {embed.title}\n{embed.description}\n\n**Actions taken**\n{embed.fields[0].value}')
                return await ctx.send('user warned')
            except:
                return await ctx.send('Invalid user! (servers can\'t be warned, warn their staff instead')
        if user.bot:
            return await ctx.send('...why would you want to warn a bot?')
        self.add_modlog(0,user.id,reason,ctx.author.id)
        actions_count, actions_count_recent = self.get_modlogs_count(user.id)
        log_embed = discord.Embed(title='User warned',description=reason,color=0xffff00,timestamp=datetime.utcnow())
        log_embed.set_author(name=f'@{user.name}', icon_url=user.avatar.url if user.avatar else None)
        log_embed.add_field(
            name='User modlogs info',
            value=f'This user has **{actions_count_recent["warns"]}** recent warnings ({actions_count["warns"]} in '+
                  f'total) and **{actions_count_recent["bans"]}** recent bans ({actions_count["bans"]} in '+
                  'total) on record.',
            inline=False)
        try:
            await user.send(embed=embed)
            await ctx.send('User has been warned and notified.',embed=log_embed)
        except:
            await ctx.send('User has DMs with bot disabled. Warning will be logged.',embed=log_embed)

    @commands.command(hidden=True)
    async def delwarn(self,ctx,target,index):
        if not ctx.author.id in self.bot.moderators:
            return
        try:
            index = int(index) - 1
        except:
            return await ctx.send('Invalid index!')
        if index < 0:
            return await ctx.send('what.')
        target = self.bot.get_user(int(target.replace('<@','',1).replace('!','',1).replace('>','',1)))
        try:
            actions, _ = self.get_modlogs(target.id)
            warn = actions['warns'][index]
        except:
            return await ctx.send('Could not find action!')
        embed = discord.Embed(title='Warning deleted',description=warn['reason'],color=0xffcc00)
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
            await ctx.send('Warning was deleted!', embed=embed)
        else:
            await ctx.send('Could not find warning - maybe the index was too high?')

    @commands.command(hidden=True)
    async def delban(self, ctx, target, index):
        if not ctx.author.id in self.bot.moderators:
            return
        try:
            index = int(index) - 1
        except:
            return await ctx.send('Invalid index!')
        if index < 0:
            return await ctx.send('what.')
        target = self.bot.get_user(int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1)))
        try:
            actions, _ = self.get_modlogs(target.id)
            ban = actions['bans'][index]
        except:
            return await ctx.send('Could not find action!')
        embed = discord.Embed(title='Ban deleted', description=ban['reason'], color=0xff0000)
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
            await ctx.send('Ban was deleted!', embed=embed)
        else:
            await ctx.send('Could not find ban - maybe the index was too high?')

    @commands.command(hidden=True,name='globaIban')
    async def globaiban(self,ctx,*,target):
        if not ctx.author.id in self.bot.moderators:
            return
        reason = ''
        parts = target.split(' ')
        forever = False
        if len(parts) >= 2:
            if len(parts)==2:
                reason = ''
            else:
                reason = target.replace(f'{parts[0]} {parts[1]} ','',1)
            target = parts[0]
            duration = parts[1]
            if (duration.lower()=='inf' or duration.lower()=='infinite' or
                duration.lower()=='forever' or duration.lower()=='indefinite'):
                forever = True
                duration = 0
            else:
                try:
                    duration = timetoint(duration)
                except:
                    return await ctx.send('Invalid duration!')
        else:
            return await ctx.send('Invalid duration!')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            userid = target
            if not len(userid) == 26:
                return await ctx.send('Invalid user/server!')
        if userid in self.bot.moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('ok guys no friendly fire pls thanks')
        obvious = False
        if '-obvious' in reason:
            obvious = True
            reason = reason.replace('-obvious','',1)
            if reason.startswith(' '):
                reason = reason.replace(' ','',1)
        ct = round(time.time())
        nt = ct + duration
        if forever:
            nt = 0
        if ctx.author.discriminator=='0':
            mod = f'@{ctx.author.name}'
        else:
            mod = f'{ctx.author.name}#{ctx.author.discriminator}'
        if reason=='':
            embed = discord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=f'no reason given',color=0xffcc00)
        else:
            embed = discord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=reason,color=0xffcc00)
        if obvious:
            embed.title = 'This is a global restriction TEST!'
            embed.colour = 0x00ff00
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if obvious:
            if forever:
                embed.add_field(name='Actions taken',value=f'- :white_check_mark: NOTHING - this is only a test! ("Expiry" should be never, otherwise something is wrong.)',inline=False)
            else:
                embed.add_field(name='Actions taken',value=f'- :white_check_mark: NOTHING - this is only a test! ("Expiry" should be <t:{nt}:R>, otherwise something is wrong.)',inline=False)
        else:
            if forever:
                embed.colour = 0xff0000
                embed.add_field(name='Actions taken',value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',inline=False)
            else:
                embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',inline=False)
        user = self.bot.get_user(userid)
        if obvious:
            embed.set_footer(text='Please send what you see to the developers!')
        else:
            embed.set_footer(text='lol just kidding')
        if not user:
            try:
                user = self.bot.revolt_client.get_user(userid)
                return await user.send(f'## {embed.title}\n{embed.description}\n\n**Actions taken**\n{embed.fields[0].value}\n\n{embed.footer.text}')
            except:
                return
        if not user==None:
            try:
                await user.send(embed=embed)
            except:
                return await ctx.send('target has their dms with bot off, sadge')
        await ctx.send('hehe')

    @commands.command(hidden=True)
    async def anick(self, ctx, target, *, nickname=''):
        # Check if the user is allowed to run the command
        if not ctx.author.id in self.bot.moderators:
            return

        # Extract user ID from the target mention
        try:
            userid = int(target.replace('<@', '').replace('!', '').replace('>', ''))
        except ValueError:
            if len(target)==26:
                userid = target
            else:
                return await ctx.send("Invalid user mention.")

        # Update or remove the nickname in the database
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(str(userid), None)
        else:
            self.bot.db['nicknames'][str(userid)] = nickname

        # Save changes to the database
        self.bot.db.save_data()

        await ctx.send('Nickname updated.')

    @commands.command(hidden=True)
    async def bridgelock(self,ctx):
        # Check if the user is allowed to run the command
        if not ctx.author.id in self.bot.moderators:
            return
        if not hasattr(self.bot, 'bridge'):
            return await ctx.send('Bridge already locked down.')
        embed = discord.Embed(title='Lock bridge down?',
                              description='This will shut down Revolt and Guilded clients, as well as unload the entire bridge extension.\nLockdown can only be lifted by admins.',
                              color=0xffcc00)
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.red,label='Lockdown',custom_id='lockdown'),
                discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel')
            )
        )
        components_inac = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.red, label='Lockdown', custom_id='lockdown',disabled=True),
                discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel', disabled=True)
            )
        )
        msg = await ctx.send(embed=embed,components=components)

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

        try:
            interaction = await self.bot.wait_for('component_interaction',check=check,timeout=30)
        except:
            return await msg.edit(components=components_inac)

        if not interaction.custom_id=='lockdown':
            return await interaction.response.edit_message(components=components_inac)

        embed.title = ':warning: FINAL WARNING!!! :warning:'
        embed.description = 'LOCKDOWNS CANNOT BE REVERSED BY NON-ADMINS!\nDo NOT lock down the chat if you don\'t know what you\'re doing!'
        embed.colour = 0xff0000

        await interaction.response.edit_message(embed=embed)

        try:
            interaction = await self.bot.wait_for('component_interaction',check=check,timeout=30)
        except:
            return await msg.edit(components=components_inac)

        await interaction.response.edit_message(components=components_inac)

        if not interaction.custom_id=='lockdown':
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
        embed.title = 'LOCKDOWN COMPLETED'
        embed.description = 'Bridge has been locked down.'
        embed.colour = 0xff0000
        await msg.edit(embed=embed)

    @commands.command(hidden=True)
    async def bridgeunlock(self,ctx):
        if not ctx.author.id in self.bot.admins:
            return
        try:
            self.bot.load_extension('cogs.bridge')
        except:
            return await ctx.send('Bridge already online.')
        try:
            await self.bot.bridge.restore()
            self.logger.info('Restored ' + str(len(self.bot.bridge.bridged)) + ' messages')
        except:
            traceback.print_exc()
        if 'revolt' in externals:
            try:
                self.bot.load_extension('cogs.bridge_revolt')
            except Exception as e:
                if not isinstance(e, discord.ext.commands.errors.ExtensionAlreadyLoaded):
                    traceback.print_exc()
        if 'guilded' in externals:
            try:
                self.bot.load_extension('cogs.bridge_guilded')
            except Exception as e:
                if not isinstance(e, discord.ext.commands.errors.ExtensionAlreadyLoaded):
                    traceback.print_exc()
        await ctx.send('Lockdown removed')

def setup(bot):
    bot.add_cog(Moderation(bot))
