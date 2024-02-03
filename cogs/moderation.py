import discord
import aiofiles
import ast
import time
import hashlib
from datetime import datetime
from discord.ext import commands

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

class Moderation(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

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
    async def globalban(self,ctx,*,target):
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
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
            if userid==ctx.author.id:
                return await ctx.send('You can\'t restrict yourself :thinking:')
        except:
            return await ctx.send('Invalid user/server!')
        if userid in moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('ok guys no friendly fire pls thanks')
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
        if reason=='':
            embed = discord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=f'no reason given',color=0xffcc00,timestamp=datetime.utcnow())
        else:
            embed = discord.Embed(title=f'You\'ve been __global restricted__ by {mod}!',description=reason,color=0xffcc00,timestamp=datetime.utcnow())
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if forever:
            embed.color = 0xff0000
            embed.add_field(name='Actions taken',value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',inline=False)
        else:
            embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',inline=False)
        user = self.bot.get_user(userid)
        if not user==None:
            try:
                await user.send(embed=embed)
            except:
                pass
        await ctx.send('global banned <:nevheh:990994050607906816>')

    @commands.command(aliases=['unban'])
    async def unrestrict(self,ctx,*,target):
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members):
            return await ctx.send('You cannot unrestrict members/servers.')
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            return await ctx.send('Invalid user/server!')
        banlist = []
        if f'{ctx.guild.id}' in list(self.bot.db['blocked'].keys()):
            banlist = self.bot.db['blocked'][f'{ctx.guild.id}']
        if not f'{userid}' in list(banlist.keys()):
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
            return await ctx.send('Invalid user/server!')
        banlist = self.bot.db['banned']
        if not f'{userid}' in list(banlist.keys()):
            return await ctx.send('User/server not banned!')
        self.bot.db['banned'].pop(f'{userid}')
        self.bot.db.save_data()
        await ctx.send('unbanned, nice')

    @commands.command(aliases=['guilds'])
    async def servers(self,ctx,*,room=''):
        roomid = '_'+room
        if room=='':
            roomid = '_main'
            room = 'main'
        try:
            data = self.bot.db['rooms'][room]
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
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
                pass
                #return await ctx.send('You can\'t warn yourself :thinking:')
        except:
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
        if user==None:
            return await ctx.send('Invalid user! (servers can\'t be warned, warn their staff instead')
        if user.bot:
            return await ctx.send('...why would you want to warn a bot?')
        try:
            await user.send(embed=embed)
        except:
            return await ctx.send('bro has their dms off :skull:')
        await ctx.send('user warned')

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
        try:
            userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            return await ctx.send('Invalid user/server!')
        if userid in self.bot.moderators and not ctx.author.id==356456393491873795:
            return await ctx.send('ok guys no friendly fire pls thanks')
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
        set_author(embed,name=mod,icon_url=ctx.author.avatar)
        if forever:
            embed.color = 0xff0000
            embed.add_field(name='Actions taken',value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',inline=False)
        else:
            embed.add_field(name='Actions taken',value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',inline=False)
        user = self.bot.get_user(userid)
        embed.set_footer(text='lol just kidding')
        if not user==None:
            try:
                await user.send(embed=embed)
            except:
                return await ctx.send('target has their dms with bot off, sadge')
        await ctx.send('hehe')

def setup(bot):
    bot.add_cog(Moderation(bot))
