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
from nextcord.ext import commands
import traceback
import re
from utils import log, ui, restrictions as r
import math
import emoji as pymoji

restrictions = r.Restrictions()

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
        moderators = self.bot.db['moderators']
        for admin in self.bot.admins:
            if admin in moderators:
                continue
            moderators.append(admin)
        self.bot.moderators = moderators
        if not hasattr(self.bot, 'trusted_group'):
            self.bot.trusted_group = self.bot.db['trusted']
        restrictions.attach_bot(self.bot)
        self.logger = log.buildlogger(self.bot.package, 'upgrader', self.bot.loglevel)

    def is_user_admin(self,user_id):
        try:
            if user_id in self.bot.config['admin_ids']:
                return True
            else:
                return False
        except:
            print(
                "There was an error in 'is_user_admin(id)', for security reasons permission was resulted into denying!")
            return False

    def is_room_restricted(self, room, db):
        try:
            if room in db['restricted']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def is_room_locked(self, room, db):
        try:
            if room in db['locked']:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    @commands.command(hidden=True,description='Adds a moderator to the instance.')
    @restrictions.admin()
    async def addmod(self,ctx,*,userid):
        try:
            userid = int(userid)
        except:
            try:
                userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} Not a valid user!')
        user = self.bot.get_user(userid)
        if user==None:
            return await ctx.send(f'{self.bot.ui_emojis.error} Not a valid user!')
        if userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} This user is already a moderator!')
        if self.is_user_admin(userid) or user.bot:
            return await ctx.send('are you fr')
        self.bot.db['moderators'].append(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{user.name}#{user.discriminator}'
        if user.discriminator=='0':
            mod = f'@{user.name}'
        await ctx.send(f'{self.bot.ui_emojis.success} **{mod}** is now a moderator!')

    @commands.command(hidden=True,aliases=['remmod','delmod'],description='Removes a moderator from the instance.')
    @restrictions.admin()
    async def removemod(self,ctx,*,userid):
        try:
            userid = int(userid)
        except:
            try:
                userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} Not a valid user!')
        user = self.bot.get_user(userid)
        if user==None:
            return await ctx.send(f'{self.bot.ui_emojis.error} Not a valid user!')
        if not userid in self.bot.db['moderators']:
            return await ctx.send(f'{self.bot.ui_emojis.error} This user is not a moderator!')
        if self.is_user_admin(userid):
            return await ctx.send('are you fr')
        self.bot.db['moderators'].remove(userid)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        mod = f'{user.name}#{user.discriminator}'
        if user.discriminator=='0':
            mod = f'@{user.name}'
        await ctx.send(f'{self.bot.ui_emojis.success} **{mod}** is no longer a moderator!')

    @commands.command(hidden=True, aliases=['newroom'],description='Creates a new room.')
    @restrictions.admin()
    async def make(self,ctx,*,room):
        room = room.lower()
        if not bool(re.match("^[A-Za-z0-9_-]*$", room)):
            return await ctx.send(f'{self.bot.ui_emojis.error} Room names may only contain alphabets, numbers, dashes, and underscores.')
        if room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room already exists!')
        self.bot.db['rooms'].update({room:{}})
        self.bot.db['rules'].update({room:[]})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} Created room `{room}`!')

    @commands.command(hidden=True, description='Renames a room.')
    @restrictions.admin()
    async def rename(self, ctx, room, newroom):
        newroom = newroom.lower()
        if not room.lower() in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room does not exist!')
        if not bool(re.match("^[A-Za-z0-9_-]*$", newroom)):
            return await ctx.send(f'{self.bot.ui_emojis.error} Room names may only contain alphabets, numbers, dashes, and underscores.')
        if newroom in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room already exists!')
        self.bot.db['rooms'].update({newroom: self.bot.db['rooms'][room]})
        self.bot.db['rules'].update({newroom: self.bot.db['rules'][room]})
        self.bot.db['rooms'].pop(room)
        self.bot.db['rules'].pop(room)
        if room in self.bot.db['restricted']:
            self.bot.db['restricted'].remove(room)
            self.bot.db['restricted'].append(newroom)
        if room in self.bot.db['locked']:
            self.bot.db['locked'].remove(room)
            self.bot.db['locked'].append(newroom)
        if room in self.bot.db['roomemojis'].keys():
            self.bot.db['roomemojis'].update({newroom: self.bot.db['roomemojis'][room]})
            self.bot.db['roomemojis'].pop(room)
        if room in self.bot.db['rooms_revolt'].keys():
            self.bot.db['rooms_revolt'].update({newroom: self.bot.db['rooms_revolt'][room]})
            self.bot.db['rooms_revolt'].pop(room)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} Room renamed!')

    @commands.command(hidden=True,description='Creates a new experiment.')
    @restrictions.admin()
    async def addexperiment(self, ctx, experiment, *, experiment_name):
        if experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment already exists!')
        self.bot.db['experiments'].update({experiment: []})
        self.bot.db['experiments_info'].update({experiment: {'name':experiment_name,'description':'A new experiment'}})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'Created experiment `{experiment}`!')

    @commands.command(hidden=True,description='Removes an experiment.')
    @restrictions.admin()
    async def removeexperiment(self, ctx, *, experiment):
        if not experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment doesn\'t exist!')
        self.bot.db['experiments'].pop(experiment)
        self.bot.db['experiments_info'].pop(experiment)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'Deleted experiment `{experiment}`!')

    @commands.command(hidden=True,description='Sets experiment description.')
    @restrictions.admin()
    async def experimentdesc(self, ctx, experiment, *, experiment_desc):
        if not experiment in list(self.bot.db['experiments'].keys()):
            return await ctx.send('This experiment doesn\'t exist!')
        self.bot.db['experiments_info'][experiment].update({'description': experiment_desc})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'Added description to experiment `{experiment}`!')

    @commands.command(hidden=True,description='Sets room description.')
    @restrictions.admin()
    async def roomdesc(self,ctx,room,*,desc=''):
        room = room.lower()
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room does not exist!')
        if len(desc)==0:
            try:
                self.bot.db['descriptions'][room].pop()
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} There is no description to reset for this room.')
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} Description removed.')
        self.bot.db['descriptions'].update({room:desc})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} Updated description!')

    @commands.command(hidden=True, description='Sets room emoji.')
    @restrictions.admin()
    async def roomemoji(self, ctx, room, *, emoji=''):
        room = room.lower()
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room does not exist!')
        if len(emoji) == 0:
            try:
                self.bot.db['roomemojis'].pop(room)
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} There is no emoji to reset for this room.')
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} Emoji removed.')
        if not pymoji.is_emoji(emoji):
            return await ctx.send(f'{self.bot.ui_emojis.error} This is not a valid emoji.')
        self.bot.db['roomemojis'].update({room: emoji})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send('Updated emoji!')

    @commands.command(
        hidden=True,
        description='Restricts/unrestricts room. Only admins will be able to collect to this room when restricted.'
    )
    @restrictions.admin()
    async def roomrestrict(self,ctx,room):
        room = room.lower()
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room does not exist!')
        if room in self.bot.db['restricted']:
            self.bot.db['restricted'].remove(room)
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} Unrestricted `{room}`!')
        else:
            self.bot.db['restricted'].append(room)
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} Restricted `{room}`!')

    @commands.command(
        hidden=True,
        description='Locks/unlocks a room. Only moderators and admins will be able to chat in this room when locked.'
    )
    @restrictions.admin()
    async def roomlock(self,ctx,room):
        room = room.lower()
        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This room does not exist!')
        if room in self.bot.db['locked']:
            self.bot.db['locked'].remove(room)
            await ctx.send(f'{self.bot.ui_emojis.success} Unlocked `{room}`!')
        else:
            self.bot.db['locked'].append(room)
            await ctx.send(f'{self.bot.ui_emojis.success} Locked `{room}`!')
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(
        aliases=['experiment'],description='Shows a list of Unifier experiments, and lets you join or leave them.'
    )
    async def experiments(self,ctx,action='',experiment=''):
        if action.lower()=='enroll' or action.lower()=='add':
            if not ctx.author.guild_permissions.manage_channels and not self.is_user_admin(ctx.author.id):
                return await ctx.send(f'{self.bot.ui_emojis.error} You don\'t have the necessary permissions.')
            if not experiment in list(self.bot.db['experiments'].keys()):
                return await ctx.send(f'{self.bot.ui_emojis.error} This experiment doesn\'t exist!')
            if ctx.guild.id in self.bot.db['experiments'][experiment]:
                return await ctx.send(f'{self.bot.ui_emojis.error} Your server is already a part of this experiment!')
            self.bot.db['experiments'][experiment].append(ctx.guild.id)
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} Enrolled in experiment **'+self.bot.db['experiments_info'][experiment]['name']+'**!')
        elif action.lower()=='unenroll' or action.lower()=='remove':
            if not ctx.author.guild_permissions.manage_channels and not self.is_user_admin(ctx.author.id):
                return await ctx.send(f'{self.bot.ui_emojis.error} You don\'t have the necessary permissions.')
            if not experiment in list(self.bot.db['experiments'].keys()):
                return await ctx.send(f'{self.bot.ui_emojis.error} This experiment doesn\'t exist!')
            if not ctx.guild.id in self.bot.db['experiments'][experiment]:
                return await ctx.send(f'{self.bot.ui_emojis.error} Your server is not a part of this experiment!')
            self.bot.db['experiments'][experiment].remove(ctx.guild.id)
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await ctx.send(f'{self.bot.ui_emojis.success} Unenrolled from experiment **'+self.bot.db['experiments_info'][experiment]['name']+'**!')
        else:
            embed = nextcord.Embed(title=':test_tube: Experiments',
                                   description=f'Help us test Unifier\'s experimental features! Run `{self.bot.command_prefix}experiment enroll <experiment>` to join one.\n\n**WARNING**: These features are experimental and may break things, so proceed at your own risk!',
                                   color=self.bot.colors.blurple)
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
    
    @commands.command(aliases=['link','connect','federate','bridge'],description='Connects the channel to a given room.')
    @commands.has_permissions(manage_channels=True)
    async def bind(self,ctx,*,room=''):
        room = room.lower()
        if self.is_room_restricted(room,self.bot.db) and not self.is_user_admin(ctx.author.id):
            return await ctx.send(f'{self.bot.ui_emojis.error} Only admins can bind channels to restricted rooms.')
        if room=='' or not room: # Added "not room" as a failback
            room = self.bot.config['main_room']
            await ctx.send(f'{self.bot.ui_emojis.warning} No room was given, defaulting to main')
        try:
            data = self.bot.db['rooms'][room]['discord']
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} Ensuring channel is not connected...',
            description='This may take a while.',
            color=self.bot.colors.warning
        )
        msg = await ctx.send(embed=embed)
        hooks = await ctx.channel.webhooks()
        for roomname in list(self.bot.db['rooms'].keys()):
            # Prevent duplicate binding
            try:
                hook_id = self.bot.db['rooms'][roomname]['discord'][f'{ctx.guild.id}'][0]
            except:
                continue
            for hook in hooks:
                if hook.id == hook_id:
                    embed.title = f'{self.bot.ui_emojis.error} Channel already linked!'
                    embed.colour = self.bot.colors.error
                    embed.description = f'This channel is already linked to `{roomname}`!\nRun `{self.bot.command_prefix}unbind {roomname}` to unbind from it.'
                    return await msg.edit(embed=embed)
        try:
            guild = data[f'{ctx.guild.id}']
        except:
            guild = []
        if len(guild) >= 1:
            return await ctx.send(f'Your server is already linked to this room.\n**Accidentally deleted the webhook?** `{self.bot.command_prefix}unlink` it then `{self.bot.command_prefix}link` it back.')
        index = 0
        text = ''
        if len(self.bot.db['rules'][room])==0:
            text = f'No rules exist yet for this room! For now, follow the main room\'s rules.\nYou can always view rules if any get added using `{self.bot.command_prefix}rules {room}`.'
        else:
            for rule in self.bot.db['rules'][room]:
                if text=='':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
        text = f'{text}\n\nPlease display these rules somewhere accessible.\nThis message will be automatically pinned if you accept these rules.'
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} Please agree to the room rules first:',
            description=text,
            color=self.bot.colors.unifier
        )
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label='Accept and bind', custom_id=f'accept',disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label='No thanks', custom_id=f'reject',disabled=False
            )
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        await msg.edit(embed=embed,view=components)

        def check(interaction):
            return interaction.user.id==ctx.author.id and (
                interaction.data['custom_id']=='accept' or
                interaction.data['custom_id']=='reject'
            ) and interaction.channel.id==ctx.channel.id

        try:
            resp = await self.bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            btns.items[0].disabled = True
            btns.items[1].disabled = True
            components = ui.MessageComponents()
            components.add_row(btns)
            await msg.edit(view=components)
            return await ctx.send('Timed out.')
        btns.items[0].disabled = True
        btns.items[1].disabled = True
        components = ui.MessageComponents()
        components.add_row(btns)
        await msg.edit(view=components)
        await resp.response.defer(with_message=True)
        if resp.data['custom_id']=='reject':
            return
        webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
        guild = [webhook.id, ctx.channel.id]
        self.bot.db['rooms'][room]['discord'].update({f'{ctx.guild.id}':guild})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await resp.edit_original_message(content=f'# {self.bot.ui_emojis.success} Linked channel to Unifier network!\nYou can now send messages to the Unifier network through this channel. Say hi!')
        try:
            await msg.pin()
        except:
            pass

    @commands.command(aliases=['unlink','disconnect'],description='Disconnects the server from a given room.')
    @commands.has_permissions(manage_channels=True)
    async def unbind(self,ctx,*,room):
        room = room.lower()
        try:
            data = self.bot.db['rooms'][room]['discord']
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        try:
            try:
                hooks = await ctx.guild.webhooks()
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} I cannot manage webhooks.')
            if f'{ctx.guild.id}' in list(data.keys()):
                hook_ids = data[f'{ctx.guild.id}']
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
            data.pop(f'{ctx.guild.id}')
            self.bot.db['rooms'][room]['discord'] = data
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'# {self.bot.ui_emojis.success} Unlinked channel from Unifier network!\nThis channel is no longer linked, nothing from now will be bridged.')
        except:
            await ctx.send(f'{self.bot.ui_emojis.error} Something went wrong - check my permissions.')
            raise

    @commands.command(description='Maps channels to rooms in bulk.', aliases=['autobind'])
    @restrictions.admin()
    async def map(self, ctx):
        channels = []
        channels_enabled = []
        namelist = []
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.warning} Checking bindable channels...',
                               description='This may take a while.',
                               color=self.bot.colors.warning)
        msg = await ctx.send(embed=embed)
        hooks = await ctx.guild.webhooks()
        for channel in ctx.guild.text_channels:
            duplicate = False
            for roomname in list(self.bot.db['rooms'].keys()):
                # Prevent duplicate binding
                try:
                    hook_id = self.bot.db['rooms'][roomname]['discord'][f'{ctx.guild.id}'][0]
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
                title=f'{self.bot.ui_emojis.rooms} Map channels',
                description=f'The following channels will be mapped.\nIf the channel does not exist, they will be created automatically.\n\n{text}',
                color=self.bot.colors.unifier
            )

            view = ui.MessageComponents()
            selection = nextcord.ui.StringSelect(
                max_values=10 if len(channels) > 10 else len(channels),
                placeholder='Channels...',
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
                        label='Select first 10' if len(channels) > 10 else 'Select all',
                        custom_id='selectall'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label='Deselect all',
                        custom_id='deselect'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='Bind',
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Bind (create as restricted)',
                        custom_id='bind_restricted'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Bind (create as locked)',
                        custom_id='bind_locked'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        label='Cancel',
                        custom_id='cancel'
                    )
                ) if ctx.author.id in self.bot.admins else ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='Bind',
                        custom_id='bind'
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red,
                        label='Cancel',
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
                self.bot.db['rooms'].update({roomname: {}})
                self.bot.db['rules'].update({roomname: []})
                if restricted:
                    self.bot.db['restricted'].append(roomname)
                elif locked:
                    self.bot.db['locked'].append(roomname)
            webhook = await channel.create_webhook(name='Unifier Bridge')
            guild = [webhook.id, channel.id]
            self.bot.db['rooms'][roomname]['discord'].update({f'{ctx.guild.id}': guild})

        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await interaction.edit_original_message(
            content=f'# {self.bot.ui_emojis.success} Linked channels to Unifier network!\nYou can now send messages to the Unifier network through the channels. Say hi!')

    @commands.command(description='Displays room rules for the specified room.')
    async def rules(self,ctx,*,room=''):
        room = room.lower()
        if self.is_room_restricted(room,self.bot.db) and not self.is_user_admin(ctx.author.id):
            return await ctx.send(':eyes:')
        if room=='' or not room:
            room = 'main'

        if not room in list(self.bot.db['rooms'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        
        index = 0
        text = ''
        if room in list(self.bot.db['rules'].keys()):
            rules = self.bot.db['rules'][room]
            if len(rules)==0:
                return await ctx.send(f'{self.bot.ui_emojis.error} The admins haven\'t added rules yet. Though, make sure to always use common sense.')
        else:
            return await ctx.send(f'{self.bot.ui_emojis.error} The admins haven\'t added rules yet. Though, make sure to always use common sense.')
        for rule in rules:
            if text=='':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.rooms} Room rules',description=text,color=self.bot.colors.unifier)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        await ctx.send(embed=embed)

    @commands.command(hidden=True,description="Adds a rule to a given room.")
    @restrictions.admin()
    async def addrule(self,ctx,room,*,rule):
        room = room.lower()
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        if len(self.bot.db['rules'][room]) >= 25:
            return await ctx.send(f'{self.bot.ui_emojis.error} You can only have up to 25 rules in a room!')
        self.bot.db['rules'][room].append(rule)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} Added rule!')

    @commands.command(hidden=True,description="Removes a given rule from a given room.")
    @restrictions.admin()
    async def delrule(self,ctx,room,*,rule):
        room = room.lower()
        try:
            rule = int(rule)
            if rule <= 0:
                raise ValueError()
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Rule must be a number higher than 0.')
        if not room in list(self.bot.db['rules'].keys()):
            return await ctx.send(f'{self.bot.ui_emojis.error} This isn\'t a valid room. Run `{self.bot.command_prefix}rooms` for a full list of rooms.')
        self.bot.db['rules'][room].pop(rule-1)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} Removed rule!')

    @commands.command(hidden=True,description="Allows given user's webhooks to be bridged.")
    @restrictions.admin()
    async def addbridge(self,ctx,*,userid):
        try:
            userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
            user = self.bot.get_user(userid)
            if not user or userid==self.bot.user.id:
                raise ValueError()
            if userid in self.bot.db['external_bridge']:
                return await ctx.send(f'{self.bot.ui_emojis.error} This user is already in the whitelist!')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user!')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} Allow @{user.name} to bridge?',
            description='This will allow messages sent via webhooks created by this user to be bridged through Unifier.',
            color=self.bot.colors.warning
        )
        components = ui.MessageComponents()
        components.add_rows(
            ui.ActionRow(
                nextcord.ui.Button(label='Allow bridge',style=nextcord.ButtonStyle.green,custom_id='allow'),
                nextcord.ui.Button(label='Cancel',style=nextcord.ButtonStyle.gray)
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
        return await ctx.send(f'# {self.bot.ui_emojis.success} Linked bridge to Unifier network!\nThis user\'s webhooks can now bridge messages through Unifier!')

    @commands.command(hidden=True,description='Prevents given user\'s webhooks from being bridged.')
    @restrictions.admin()
    async def delbridge(self, ctx, *, userid):
        try:
            userid = int(userid.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
            user = self.bot.get_user(userid)
            if not user:
                raise ValueError()
            if not userid in self.bot.db['external_bridge']:
                return await ctx.send(f'{self.bot.ui_emojis.error} This user isn\'t in the whitelist!')
        except:
            return await ctx.send(f'{self.bot.ui_emojis.error} Invalid user!')
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} Remove @{user.name} from bridge?',
            description='This will stop this user\'s webhooks from bridging messages.',
            color=self.bot.colors.warning
        )
        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(label='Revoke bridge', style=nextcord.ButtonStyle.red, custom_id='allow'),
                nextcord.ui.Button(label='Cancel', style=nextcord.ButtonStyle.gray)
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
        return await ctx.send(
            f'# {self.bot.ui_emojis.success} Unlinked bridge from Unifier network!\nThis user\'s webhooks can no longer bridge messages through Unifier.')

    @commands.command(description='Shows a list of rooms.')
    async def rooms(self,ctx):
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

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel == 0:
                was_searching = False
                roomlist = list(self.bot.db['rooms'].keys())
                offset = 0
                for x in range(len(roomlist)):
                    if (not show_restricted and self.is_room_restricted(roomlist[x-offset],self.bot.db) or
                            not show_locked and self.is_room_locked(roomlist[x-offset],self.bot.db)):
                        roomlist.pop(x-offset)
                        offset += 1

                maxpage = math.ceil(len(roomlist) / limit) - 1
                if interaction:
                    if page > maxpage:
                        page = maxpage
                embed.title = f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms'
                embed.description = 'Choose a room to view its info!'
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Room...'
                )

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(roomlist):
                        break
                    name = roomlist[index]
                    description = (
                        self.bot.db['descriptions'][roomlist[index]]
                        if roomlist[index] in self.bot.db['descriptions'].keys() else 'This room has no description.'
                    )
                    emoji = (
                        '\U0001F527' if self.is_room_restricted(roomlist[index],self.bot.db) else
                        '\U0001F512' if self.is_room_locked(roomlist[index],self.bot.db) else
                        '\U0001F310'
                    ) if not name in self.bot.db['roomemojis'] else self.bot.db['roomemojis'][name]

                    embed.add_field(
                        name=f'{emoji} `{name}`',
                        value=description,
                        inline=False
                    )
                    selection.add_option(
                        label=name,
                        emoji=emoji,
                        description=description,
                        value=name
                    )

                if len(embed.fields) == 0:
                    embed.add_field(
                        name='No rooms',
                        value='There\'s no rooms here!',
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
                            label='Previous',
                            custom_id='prev',
                            disabled=page <= 0 or selection.disabled,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Next',
                            custom_id='next',
                            disabled=page >= maxpage or selection.disabled,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label='Search',
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search,
                            disabled=selection.disabled
                        )
                    )
                )
            elif panel == 1:
                was_searching = True
                roomlist = list(self.bot.db['rooms'].keys())

                def search_filter(query, query_cmd):
                    if match == 0:
                        return (
                                query.lower() in query_cmd and namematch or
                                (
                                        query.lower() in self.bot.db['descriptions'][query_cmd].lower()
                                        if query_cmd in self.bot.db['descriptions'].keys() else False
                                ) and descmatch
                        )
                    elif match == 1:
                        return (
                                ((query.lower() in query_cmd and namematch) or not namematch) and
                                ((
                                    query.lower() in self.bot.db['descriptions'][query_cmd].lower()
                                    if query_cmd in self.bot.db['descriptions'].keys() else False
                                ) and descmatch or not descmatch)
                        )

                offset = 0
                for x in range(len(roomlist)):
                    room = roomlist[x - offset]
                    if (
                            not show_restricted and self.is_room_restricted(roomlist[x - offset], self.bot.db) or
                            not show_locked and self.is_room_locked(roomlist[x - offset], self.bot.db)
                    ) and not show_restricted or not search_filter(query,room):
                        roomlist.pop(x - offset)
                        offset += 1

                embed.title = f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms / search'
                embed.description = 'Choose a room to view its info!'

                if len(roomlist) == 0:
                    maxpage = 0
                    embed.add_field(
                        name='No rooms',
                        value='There are no rooms matching your search query.',
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder='Room...', disabled=True
                    )
                    selection.add_option(
                        label='No rooms'
                    )
                else:
                    maxpage = math.ceil(len(roomlist) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder='Room...'
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
                        emoji = (
                            '\U0001F527' if self.is_room_restricted(roomlist[index], self.bot.db) else
                            '\U0001F512' if self.is_room_locked(roomlist[index], self.bot.db) else
                            '\U0001F310'
                        ) if not room in self.bot.db['roomemojis'] else self.bot.db['roomemojis'][room]
                        roomdesc = (
                            self.bot.db['descriptions'][room] if room in self.bot.db['descriptions'].keys() else
                            'This room has no description.'
                        )
                        embed.add_field(
                            name=f'{emoji} `{room}`',
                            value=roomdesc,
                            inline=False
                        )
                        selection.add_option(
                            label=room,
                            description=roomdesc if len(roomdesc) <= 100 else roomdesc[:-(len(roomdesc) - 97)] + '...',
                            value=room,
                            emoji=emoji
                        )

                embed.description = f'Searching: {query} (**{len(roomlist)}** results)'
                maxcount = (page + 1) * limit
                if maxcount > len(roomlist):
                    maxcount = len(roomlist)
                embed.set_footer(
                    text=(
                        f'Page {page + 1} of {maxpage + 1} | {page * limit + 1}-{maxcount} of {len(roomlist)}'+
                        ' results'
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
                            label='Previous',
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='Next',
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label='Search',
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
                                'Matches any of' if match == 0 else
                                'Matches both'
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
                            label='Room name',
                            style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label='Room description',
                            style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                        )
                    )
                )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 2:
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms / search / {roomname}'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms / {roomname}'
                )
                description = (
                    self.bot.db['descriptions'][roomname]
                    if roomname in self.bot.db['descriptions'].keys() else 'This room has no description.'
                )
                emoji = (
                    '\U0001F527' if self.is_room_restricted(roomname, self.bot.db) else
                    '\U0001F512' if self.is_room_locked(roomname, self.bot.db) else
                    '\U0001F310'
                ) if not roomname in self.bot.db['roomemojis'] else self.bot.db['roomemojis'][roomname]
                embed.description = f'# **{emoji} `{roomname}`**\n{description}'
                stats = await self.bot.bridge.roomstats(roomname)
                embed.add_field(name='Statistics',value=(
                    f':homes: {stats["guilds"]} servers\n'+
                    f':green_circle: {stats["online"]} online, :busts_in_silhouette: {stats["members"]} members\n'+
                    f':speech_balloon: {stats["messages"]} messages sent today'
                ))
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label='View room rules',
                            custom_id='rules',
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel==3:
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms / search / {roomname} / rules'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {self.bot.user.global_name or self.bot.user.name} rooms / {roomname} / rules'
                )
                index = 0
                text = ''
                if roomname in list(self.bot.db['rules'].keys()):
                    rules = self.bot.db['rules'][roomname]
                else:
                    rules = []
                for rule in rules:
                    if text == '':
                        text = f'1. {rule}'
                    else:
                        text = f'{text}\n{index}. {rule}'
                    index += 1
                if len(rules)==0:
                    text = (
                        'The room admins haven\'t added rules for this room yet.\n'+
                        'Though, do remember to use common sense and refrain from doing things that you shouldn\'t do.'
                    )
                embed.description=text
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if panel == 0:
                embed.set_footer(text=f'Page {page + 1} of {maxpage + 1}')
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
                await msg.edit(view=None)
                break
            if interaction.type == nextcord.InteractionType.component:
                if interaction.data['custom_id'] == 'selection':
                    roomname = interaction.data['values'][0]
                    panel = 2
                    page = 0
                elif interaction.data['custom_id'] == 'back':
                    panel -= 1
                    if panel < 0 or panel==1 and not was_searching:
                        panel = 0
                    page = 0
                elif interaction.data['custom_id'] == 'rules':
                    panel += 1
                elif interaction.data['custom_id'] == 'prev':
                    page -= 1
                elif interaction.data['custom_id'] == 'next':
                    page += 1
                elif interaction.data['custom_id'] == 'search':
                    modal = nextcord.ui.Modal(title='Search...', auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label='Search query',
                            style=nextcord.TextInputStyle.short,
                            placeholder='Type something...'
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
            elif interaction.type == nextcord.InteractionType.modal_submit:
                panel = 1
                query = interaction.data['components'][0]['components'][0]['value']
                namematch = True
                descmatch = True
                match = 0
                page = 0

    @commands.command(description='Enables or disables usage of server emojis as Global Emojis.')
    @commands.has_permissions(manage_guild=True)
    async def toggle_emoji(self,ctx):
        if ctx.guild.id in self.bot.bridged_emojis:
            self.bot.bridged_emojis.remove(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} All members can now no longer use your emojis!')
        else:
            self.bot.bridged_emojis.append(ctx.guild.id)
            await ctx.send(f'{self.bot.ui_emojis.success} All members can now use your emojis!')
        self.bot.db['emojis'] = self.bot.bridged_emojis
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @commands.command(description='Displays or sets custom avatar.')
    async def avatar(self,ctx,*,url=''):
        desc = f'You have no avatar! Run `{self.bot.command_prefix}avatar <url>` or set an avatar in your profile settings.'
        try:
            if f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                avurl = self.bot.db['avatars'][f'{ctx.author.id}']
                desc = f'You have a custom avatar! Run `{self.bot.command_prefix}avatar <url>` to change it, or run `{self.bot.command_prefix}avatar remove` to remove it.'
            else:
                desc = f'You have a default avatar! Run `{self.bot.command_prefix}avatar <url>` to set a custom one.'
                avurl = ctx.author.avatar.url
        except:
            avurl = None
        if not url=='':
            avurl = url
        embed = nextcord.Embed(
            title='This is your UniChat avatar!',
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
                return await ctx.send('You don\'t have a custom avatar!')
            self.bot.db['avatars'].pop(f'{ctx.author.id}')
            return await ctx.send('Custom avatar removed!')
        if not url=='':
            embed.title = 'This is how you\'ll look!'
            embed.description = 'If you\'re satisfied, press the green button!'
        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.green, label='Apply', custom_id=f'apply', disabled=False),
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Cancel', custom_id=f'cancel', disabled=False)
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        if url=='':
            embed.set_footer(text=f'To change your avatar, run {self.bot.command_prefix}avatar <url>.')
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
                return await ctx.send('Timed out.',reference=msg)
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
            return await interaction.response.send_message(f'{self.bot.ui_emojis.success} Avatar successfully added!')

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Config(bot))
