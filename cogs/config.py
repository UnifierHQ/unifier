"""
Unifier - A "simple" bot to unite Discord servers with webhooks
Copyright (C) 2024  Green and ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
import json
import traceback

with open('config.json', 'r') as file:
    data = json.load(file)

admin_ids = data["admin_ids"]

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = 'data.json'
        
        # Ensure necessary keys exist
        self.update({'rules':{},'rooms':{},'rooms_revolt':{},'emojis':[],'nicknames':{},'descriptions':{},
                     'restricted':[],'locked':[],'blocked':{},'banned':{},'moderators':[],
                     'avatars':{},'experiments':{},'experiments_info':{}})

        # Load data
        self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            self.update(data)
        except FileNotFoundError:
            pass  # If the file is not found, initialize an empty dictionary

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)

def is_user_admin(id):
    try:
        global admin_ids
        if id in admin_ids:
            return True
        else:
            return False
    except:
        print("There was an error in 'is_user_admin(id)', for security reasons permission was resulted into denying!")
        return False

def is_room_restricted(room,db):
    try:
        if room in db['restricted']:
            return True
        else:
            return False
    except:
        traceback.print_exc()
        return False

def is_room_locked(room,db):
    try:
        if room in db['locked']:
            return True
        else:
            return False
    except:
        traceback.print_exc()
        return False

class Config(commands.Cog, name=':construction_worker: Config'):
    """Config is an extension that lets Unifier admins configure the bot and server moderators set up Unified Chat in their server.

    Developed by Green and ItsAsheer"""
    def __init__(self,bot):
        self.bot = bot
        if not hasattr(bot, 'db'):
            self.bot.db = AutoSaveDict({})
        if not hasattr(self.bot, 'bridged_emojis'):
            if not 'emojis' in list(self.bot.db.keys()):
                self.bot.db.update({'emojis':[]})
                self.bot.db.save_data()
            self.bot.bridged_emojis = self.bot.db['emojis']
        self.bot.admins = admin_ids
        moderators = self.bot.db['moderators']
        for admin in admin_ids:
            if admin in moderators:
                continue
            moderators.append(admin)
        self.bot.moderators = moderators

    @commands.command(hidde=True)
    async def addmod(self,ctx,*,userid):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can manage moderators!')
        try:
            userid = int(userid)
        except:
            try:
                userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            except:
                return await ctx.send('Not a valid user!')
        user = self.bot.get_user(userid)
        if user==None:
            return await ctx.send('Not a valid user!')
        if userid in self.bot.db['moderators']:
            return await ctx.send('This user is already a moderator!')
        if is_user_admin(userid):
            return await ctx.send('are you fr')
        self.bot.db['moderators'].append(userid)
        self.bot.db.save_data()
        mod = f'{user.name}#{user.discriminator}'
        if user.discriminator=='0':
            mod = f'@{user.name}'
        await ctx.send(f'**{mod}** is now a moderator!')

    @commands.command(hidden=True,aliases=['remmod','delmod'])
    async def removemod(self,ctx,*,userid):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can manage moderators!')
        try:
            userid = int(userid)
        except:
            try:
                userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            except:
                return await ctx.send('Not a valid user!')
        user = self.bot.get_user(userid)
        if user==None:
            return await ctx.send('Not a valid user!')
        if not userid in self.bot.db['moderators']:
            return await ctx.send('This user is not a moderator!')
        if is_user_admin(userid):
            return await ctx.send('are you fr')
        self.bot.db['moderators'].remove(userid)
        self.bot.db.save_data()
        mod = f'{user.name}#{user.discriminator}'
        if user.discriminator=='0':
            mod = f'@{user.name}'
        await ctx.send(f'**{mod}** is no longer a moderator!')

    @commands.command(hidden=True)
    async def make(self,ctx,*,room):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can create rooms!')
        if room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room already exists!')
        self.bot.db['rooms'].update({room:{}})
        self.bot.db['rules'].update({room:[]})
        self.bot.db.save_data()
        await ctx.send(f'Created room `{room}`!')

    @commands.command(hidden=True)
    async def addexperiment(self, ctx, experiment, *, experiment_name):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can add experiments!')
        if experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment already exists!')
        self.bot.db['experiments'].update({experiment: []})
        self.bot.db['experiments_info'].update({experiment: {'name':experiment_name,'description':'A new experiment'}})
        self.bot.db.save_data()
        await ctx.send(f'Created experiment `{experiment}`!')

    @commands.command(hidden=True)
    async def removeexperiment(self, ctx, *, experiment):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can add experiments!')
        if not experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment doesn\'t exist!')
        self.bot.db['experiments'].pop(experiment)
        self.bot.db['experiments_info'].pop(experiment)
        self.bot.db.save_data()
        await ctx.send(f'Deleted experiment `{experiment}`!')

    @commands.command(hidden=True)
    async def experimentdesc(self, ctx, experiment, *, experiment_desc):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify experiments!')
        if not experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment doesn\'t exist!')
        self.bot.db['experiments_info'][experiment].update({'description': experiment_desc})
        self.bot.db.save_data()
        await ctx.send(f'Added description to experiment `{experiment}`!')

    @commands.command(hidden=True)
    async def roomdesc(self,ctx,*,args):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rooms!')
        try:
            room, desc = args.split(' ',1)
        except:
            room = args
            desc = ''
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room does not exist!')
        if len(desc)==0:
            try:
                self.bot.db['descriptions'][room].pop()
            except:
                return await ctx.send('there was no description to begin with...')
            self.bot.db.save_data()
            return await ctx.send('Description removed.')
        self.bot.db['descriptions'].update({room:desc})
        self.bot.db.save_data()
        await ctx.send('Updated description!')

    @commands.command(hidden=True)
    async def roomrestrict(self,ctx,*,room):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rooms!')
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room does not exist!')
        if room in self.bot.db['restricted']:
            self.bot.db['restricted'].remove(room)
            await ctx.send(f'Unrestricted `{room}`!')
        else:
            self.bot.db['restricted'].append(room)
            await ctx.send(f'Restricted `{room}`!')
        self.bot.db.save_data()

    @commands.command(hidden=True)
    async def roomlock(self,ctx,*,room):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rooms!')
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room does not exist!')
        if room in self.bot.db['locked']:
            self.bot.db['locked'].remove(room)
            await ctx.send(f'Unlocked `{room}`!')
        else:
            self.bot.db['locked'].append(room)
            await ctx.send(f'Locked `{room}`!')
        self.bot.db.save_data()

    @commands.command(aliases=['experiment'])
    async def experiments(self,ctx,action='',experiment=''):
        """Shows a list of Unifier experiments, and lets you join or leave them."""
        if action.lower()=='enroll' or action.lower()=='add':
            if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
                return await ctx.send('You don\'t have the necessary permissions.')
            if not experiment in list(self.bot.db['experiments'].keys()):
                return await ctx.send('This experiment doesn\'t exist!')
            if ctx.guild.id in self.bot.db['experiments'][experiment]:
                return await ctx.send('Your server is already a part of this experiment!')
            self.bot.db['experiments'][experiment].append(ctx.guild.id)
            self.bot.db.save_data()
            return await ctx.send('Enrolled in experiment **'+self.bot.db['experiments_info'][experiment]['name']+'**!')
        elif action.lower()=='unenroll' or action.lower()=='remove':
            if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
                return await ctx.send('You don\'t have the necessary permissions.')
            if not experiment in list(self.bot.db['experiments'].keys()):
                return await ctx.send('This experiment doesn\'t exist!')
            if not ctx.guild.id in self.bot.db['experiments'][experiment]:
                return await ctx.send('Your server is not a part of this experiment!')
            self.bot.db['experiments'][experiment].remove(ctx.guild.id)
            self.bot.db.save_data()
            return await ctx.send('Unenrolled from experiment **'+self.bot.db['experiments_info'][experiment]['name']+'**!')
        else:
            embed = discord.Embed(title=':test_tube: Experiments',
                                  description='Help us test Unifier\'s experimental features! Run `u!experiment enroll <experiment>` to join one.\n\n**WARNING**: These features are experimental and may break things, so proceed at your own risk!',
                                  color=0x0000ff)
            for experiment in self.bot.db['experiments']:
                name = self.bot.db['experiments_info'][experiment]['name'] + f" (`{experiment}`"
                description = self.bot.db['experiments_info'][experiment]['description']
                enrolled = ctx.guild.id in self.bot.db['experiments'][experiment]
                if enrolled:
                    name = name + ", active)"
                    description = description + "\n\n**Your server is enrolled in this experiment!**"
                else:
                    name = name + ")"
                embed.add_field(name=name, value=description, inline=False)
            if len(list(self.bot.db['experiments'].keys()))==0:
                embed.add_field(name="no experiments? :face_with_raised_eyebrow:",value='There\'s no experiments available yet!',inline=False)
            await ctx.send(embed=embed)
    
    @commands.command(aliases=['link','connect','federate','bridge'])
    async def bind(self,ctx,*,room=''):
        if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
            return await ctx.send('You don\'t have the necessary permissions.')
        if is_room_restricted(room,self.bot.db) and not is_user_admin(ctx.author.id):
            return await ctx.send('Only Green and ItsAsheer can bind channels to restricted rooms.')
        if room=='' or not room: #Added "not room" as a failback
            room = 'main'
            await ctx.send('**No room was given, defaulting to main**')
        try:
            data = self.bot.db['rooms'][room]
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
        try:
            try:
                guild = data[f'{ctx.guild.id}']
            except:
                guild = []
            if len(guild) >= 1:
                return await ctx.send('Your server is already linked to this room.\n**Accidentally deleted the webhook?** `u!unlink` it then `u!link` it back.')
            index = 0
            text = ''
            if len(self.bot.db['rules'][room])==0:
                text = f'No rules exist yet for this room! For now, follow the main room\'s rules.\nYou can always view rules if any get added using `u!rules {room}`.'
            else:
                for rule in self.bot.db['rules'][room]:
                    if text=='':
                        text = f'1. {rule}'
                    else:
                        text = f'{text}\n{index}. {rule}'
                    index += 1
            text = f'{text}\n\nPlease display these rules somewhere accessible.'
            embed = discord.Embed(title='Please agree to the room rules first:',description=text)
            embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
            ButtonStyle = discord.ButtonStyle
            row = [
                discord.ui.Button(style=ButtonStyle.green, label='Accept and bind', custom_id=f'accept',disabled=False),
                discord.ui.Button(style=ButtonStyle.red, label='No thanks', custom_id=f'reject',disabled=False)
                ]
            btns = discord.ui.ActionRow(row[0],row[1])
            components = discord.ui.MessageComponents(btns)
            msg = await ctx.send(embed=embed,components=components)

            def check(interaction):
                return interaction.user.id==ctx.author.id and (
                    interaction.custom_id=='accept' or
                    interaction.custom_id=='reject'
                    ) and interaction.channel.id==ctx.channel.id

            try:
                resp = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
            except:
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0],row[1])
                components = discord.ui.MessageComponents(btns)
                await msg.edit(components=components)
                return await ctx.send('Timed out.')
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0],row[1])
            components = discord.ui.MessageComponents(btns)
            await resp.response.edit_message(components=components)
            if resp.custom_id=='reject':
                return
            webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
            data = self.bot.db['rooms'][room]
            guild = []
            guild.append(webhook.id)
            data.update({f'{ctx.guild.id}':guild})
            self.bot.db['rooms'][room] = data
            self.bot.db.save_data()
            await ctx.send('Linked channel with network!')
            try:
                await msg.pin()
            except:
                pass
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command(aliases=['unlink','disconnect'])
    async def unbind(self,ctx,*,room=''):
        if room=='':
            return await ctx.send('You must specify the room to unbind from.')
        if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
            return await ctx.send('You don\'t have the necessary permissions.')
        try:
            data = self.bot.db['rooms'][room]
        except:
            return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
        try:
            try:
                hooks = await ctx.guild.webhooks()
            except:
                return await ctx.send('I cannot manage webhooks.')
            if f'{ctx.guild.id}' in list(data.keys()):
                hook_ids = data[f'{ctx.guild.id}']
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
            data.pop(f'{ctx.guild.id}')
            self.bot.db['rooms'][room] = data
            self.bot.db.save_data()
            await ctx.send('Unlinked channel from network!')
        except:
            await ctx.send('Something went wrong - check my permissions.')
            raise

    @commands.command()
    async def rules(self,ctx,*,room=''):
        """Displays room rules for the specified room."""
        if is_room_restricted(room,self.bot.db) and not is_user_admin(ctx.author.id):
            return await ctx.send(':eyes:')
        if room=='' or not room:
            room = 'main'

        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send('This room doesn\'t exist! Run `u!rooms` to get a full list.')
        
        index = 0
        text = ''
        if room in list(self.bot.db['rules'].keys()):
            rules = self.bot.db['rules'][room]
            if len(rules)==0:
                return await ctx.send('The room creator hasn\'t added rules yet. For now, follow `main` room rules.')
        else:
            return await ctx.send('The room creator hasn\'t added rules yet. For now, follow `main` room rules.')
        for rule in rules:
            if text=='':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        embed = discord.Embed(title='Room rules',description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        await ctx.send(embed=embed)

    @commands.command()
    async def addrule(self,ctx,*,args):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rules!')
        try:
            room, rule = args.split(' ',1)
        except:
            return await ctx.send('Rule is missing.')
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send('This room does not exist!')
        self.bot.db['rules'][room].append(rule)
        self.bot.db.save_data()
        await ctx.send('Added rule!')

    @commands.command()
    async def delrule(self,ctx,*,args):
        if not is_user_admin(ctx.author.id):
            return await ctx.send('Only admins can modify rules!')
        try:
            room, rule = args.split(' ',1)
        except:
            return await ctx.send('Rule is missing.')
        try:
            rule = int(rule)
            if rule <= 0:
                raise ValueError()
        except:
            return await ctx.send('Rule must be a number higher than 0.')
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send('This room does not exist!')
        self.bot.db['rules'][room].pop(rule-1)
        self.bot.db.save_data()
        await ctx.send('Removed rule!')

    @commands.command()
    async def rooms(self,ctx):
        embed = discord.Embed(title=f'UniChat rooms (Total: `0`)',description='Use `u!bind <room>` to bind to a room.')
        if len(self.bot.db['rooms'])==0:
            embed.add_field(name='',value='No rooms here <:notlikenevira:1144718936986882088>')
            return await ctx.send(embed=embed)
        count = 0
        for room in self.bot.db['rooms']:
            if is_room_restricted(room,self.bot.db):
                if not is_user_admin(ctx.author.id):
                    continue
                emoji = ':wrench:'
            elif is_room_locked(room,self.bot.db):
                emoji = ':lock:'
            else:
                emoji = ':globe_with_meridians:'
            if room in list(self.bot.db['descriptions'].keys()):
                desc = self.bot.db['descriptions'][room]
            else:
                desc = 'This room has no description.'
            online = 0
            members = 0
            guilds = 0
            for guild_id in self.bot.db['rooms'][room]:
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    online += len(list(filter(lambda x: (x.status!=discord.Status.offline and x.status!=discord.Status.invisible), guild.members)))
                    members += len(guild.members)
                    guilds += 1
                except:
                    pass
            embed.add_field(name=f'{emoji} `{room}` - {guilds} servers (:green_circle: {online} online, :busts_in_silhouette: {members} members)',value=desc,inline=False)
            count += 1
        embed.title = f'UniChat rooms (Total: `{count}`)'
        await ctx.send(embed=embed)

    @commands.command()
    async def toggle_emoji(self,ctx):
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send('You don\'t have the necessary permissions.')
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send('All members can now no longer use your emojis!')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send('All members can now use your emojis!')
        self.bot.db['emojis'] = self.bot.bridged_emojis
        self.bot.db.save_data()

    @commands.command()
    async def about(self,ctx):
        embed = discord.Embed(title="Unifier and Unified Chat",description="Unify servers, make worthwhile conversations.",color=0xed4545)
        embed.add_field(name="Developers",value="@green.\n@itsasheer",inline=False)
        embed.add_field(name="PFP made by",value="@green.\n@thegodlypenguin",inline=False)
        embed.set_footer(text="Version v1.0.0 (Release)")
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(self,ctx,*,url=''):
        desc = 'You have no avatar! Run `u!avatar <url>` or set an avatar in your profile settings.'
        try:
            if f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                avurl = self.bot.db['avatars'][f'{ctx.author.id}']
                desc = 'You have a custom avatar! Run `u!avatar <url>` to change it, or run `u!avatar remove` to remove it.'
            else:
                desc = 'You have a default avatar! Run `u!avatar <url>` to set a custom one for UniChat.'
                avurl = ctx.author.avatar.url
        except:
            avurl = None
        if not url=='':
            avurl = url
        embed = discord.Embed(title='This is your UniChat avatar!',description=desc)
        author = f'{ctx.author.name}#{ctx.author.discriminator}'
        if ctx.author.discriminator == '0':
            author = f'@{ctx.author.name}'
        try:
            embed.set_author(name=author,icon_url=avurl)
            embed.set_thumbnail(url=avurl)
        except:
            return await ctx.send("Invalid URL!")
        if url=='remove':
            if not f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                return await ctx.send('You don\'t have a custom avatar!')
            self.bot.db['avatars'].pop(f'{ctx.author.id}')
            return await ctx.send('Custom avatar removed!')
        if not url=='':
            embed.title = 'This is how you\'ll look!'
            embed.description = 'If you\'re satisfied, press the green button!'
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Apply', custom_id=f'apply', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Cancel', custom_id=f'cancel', disabled=False)
        ]
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        if url=='':
            embed.set_footer(text='To change your avatar, run u!avatar <url>.')
            components = None
        msg = await ctx.send(embed=embed,components=components)
        if not url == '':
            def check(interaction):
                return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

            try:
                interaction = await self.bot.wait_for("component_interaction", check=check, timeout=30.0)
            except:
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0], row[1])
                components = discord.ui.MessageComponents(btns)
                await msg.edit(components=components)
                return await ctx.send('Timed out.',reference=msg)
            if interaction.custom_id=='cancel':
                row[0].disabled = True
                row[1].disabled = True
                btns = discord.ui.ActionRow(row[0], row[1])
                components = discord.ui.MessageComponents(btns)
                return await interaction.response.edit_message(components=components)
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            await msg.edit(components=components)
            self.bot.db['avatars'].update({f'{ctx.author.id}':url})
            self.bot.db.save_data()
            return await interaction.response.send_message('Avatar successfully added!')

def setup(bot):
    bot.add_cog(Config(bot))
