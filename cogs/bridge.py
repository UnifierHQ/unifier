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
import os

import discord
import hashlib

import revolt
from discord.ext import commands
import traceback
import time
from datetime import datetime
import random
import string
import copy
import json
import re
from tld import get_tld
from utils import rapidphish
import threading

with open('config.json', 'r') as file:
    data = json.load(file)

home_guild = data["home_guild"]
logs_channel = data["logs_channel"]
reports_channel = data["reports_channel"]
externals = data["external"]

# Configure PR and PR referencing here, if you need it for whatever reason.
allow_prs = data["allow_prs"]
pr_room_index = data["pr_room_index"] # If this is 0, then the oldest room will be used as the PR room.
pr_ref_room_index = data["pr_ref_room_index"]

mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def genid():
    value = ''
    for i in range(6):
        letter = random.choice(string.ascii_lowercase + string.digits)
        value = '{0}{1}'.format(value, letter)
    return value

def is_room_locked(room, db):
    try:
        if room in db['locked']:
            return True
        else:
            return False
    except:
        traceback.print_exc()
        return False

def findurl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]


def bypass_killer(string):
    if not [*string][len(string) - 1].isalnum():
        return string[:-1]
    else:
        raise RuntimeError()

class Bridge(commands.Cog, name=':link: Bridge'):
    """Bridge is the heart of Unifier, it's the extension that handles the bridging and everything chat related.

    Developed by Green and ItsAsheer"""
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self.bot, 'bridged'):
            self.bot.bridged = {}
        if not hasattr(self.bot, 'bridged_external'):
            self.bot.bridged_external = {}
        if not hasattr(self.bot, 'bridged_obe'):
            # OBE = Owned By External
            # Message wasn't sent from Discord.
            self.bot.bridged_obe = {}
        if not hasattr(self.bot, 'bridged_urls'):
            self.bot.bridged_urls = {}
        if not hasattr(self.bot, 'owners'):
            self.bot.owners = {}
        if not hasattr(self.bot, 'origin'):
            self.bot.origin = {}
        if not hasattr(self.bot, 'prs'):
            self.bot.prs = {}
        if not hasattr(self.bot, 'notified'):
            self.bot.notified = []
        if not hasattr(self.bot, 'reports'):
            self.bot.reports = {}
        if not hasattr(self.bot, 'webhook_cache'):
            self.bot.webhook_cache = {}
        if not hasattr(self.bot, 'webhook_cache_sync'):
            self.bot.webhook_cache_sync = {}

    def clueless_gen(self, user, identifier):
        from PIL import Image
        import requests
        import io
        response = requests.get(user)
        user_resp = response
        bg = Image.open('clueless.png').convert('RGBA')
        user = Image.open(io.BytesIO(user_resp.content)).convert('RGBA').resize((80, 80))
        bg.paste(user, (40, 8), user)
        bg.save(f'cached/{identifier}_clueless_output.png')
        return f'{identifier}_clueless_output.png'

    def think(self, user1, user2, username, identifier):
        from PIL import Image, ImageDraw, ImageFont
        import requests
        import io
        response = requests.get(user1)
        user1_resp = response
        response = requests.get(user2)
        user2_resp = response
        bg = Image.open('think.png').convert('RGBA')
        user1 = Image.open(io.BytesIO(user1_resp.content)).convert('RGBA').resize((150, 150))
        user2 = Image.open(io.BytesIO(user2_resp.content)).convert('RGBA').resize((200, 200))
        bg.paste(user1, (280, 170), user1)
        bg.paste(user2, (753, 180), user2)
        im_draw = ImageDraw.Draw(bg)
        font = ImageFont.truetype('Kollektif.ttf', 50)
        components = username.split('(')
        component = components[len(components) - 1].replace(')', '')
        if len(component) == 6 and len(username.split('(')) >= 2:
            username = username[:-9]
        text = f'THINK, {username.upper()}, THINK!'
        text_width, text_height = im_draw.textsize(text, font)
        width = 1116 - text_width
        width = width / 2
        width = int(width)
        im_draw.text((width, 620), text, font=font, fill=(255, 255, 255, 255))
        bg.save(f'cached/{identifier}_think_output.png')
        return f'{identifier}_think_output.png'

    def omniman(self, user1, user2, identifier):
        from PIL import Image
        import requests
        import io
        response = requests.get(user1)
        user1_resp = response
        response = requests.get(user2)
        user2_resp = response
        bg = Image.open('omni.png').convert('RGBA')
        user1 = Image.open(io.BytesIO(user1_resp.content)).convert('RGBA').resize((150, 150))
        user2 = Image.open(io.BytesIO(user2_resp.content)).convert('RGBA').resize((200, 200))
        bg.paste(user1, (400, 150), user1)
        bg.paste(user2, (863, 180), user2)
        bg2 = Image.open('omni1.png').convert('RGBA').resize((1318, 711))
        bg2.paste(user1, (330, -10), user1)
        bg2.paste(user2, (863, 180), user2)
        lst = [bg2, bg]
        bg.save(f'cached/{identifier}_think_output.gif', 'GIF', append_images=lst, save_all=True, duration=[1600, 800, 800],
                optimize=False, loop=0)
        return f'{identifier}_think_output.gif'

    async def image_forward(self,ctx,msg_resp,filename):
        gbans = self.bot.db['banned']

        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            ct = time.time()
            cdt = datetime.utcnow()
            if f'{ctx.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{ctx.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{ctx.author.id}')
                    self.bot.db.update()
                else:
                    return
            if f'{ctx.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{ctx.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{ctx.guild.id}')
                    self.bot.db.update()
                else:
                    return

        if ctx.author.id == self.bot.user.id:
            return

        try:
            hooks = await ctx.channel.webhooks()
        except:
            return
        found = False
        origin_room = 0

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{ctx.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{ctx.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    if key in self.bot.db['locked'] and not ctx.author.id in self.bot.admins:
                        return
                    break
                index += 1
            if found:
                break

        if not found:
            return

        roomname = list(self.bot.db['rooms'].keys())[origin_room]
        if is_room_locked(roomname, self.bot.db) and not ctx.author.id in self.bot.admins:
            return

        if not found:
            return

        user_hash = encrypt_string(f'{ctx.author.id}')[:3]
        guild_hash = encrypt_string(f'{ctx.guild.id}')[:3]
        identifier = ' (' + user_hash + guild_hash + ')'
        identifier_og = identifier

        hookmsg_ids = {}
        msg_urls = {}

        identifier_cache = identifier
        banned = False

        # Forwarding
        results = []
        sameguild_id = []
        threads = []
        trimmed = None

        try:
            if f'{ctx.author.id}' in self.bot.db['avatars']:
                url = self.bot.db['avatars'][f'{ctx.author.id}']
            else:
                url = ctx.author.avatar.url
        except:
            url = None

        for key in data:
            blocked = False
            sameguild = False
            if len(identifier) == 0:
                # restore identifier
                identifier = identifier_cache
            if int(key) == ctx.guild.id:
                sameguild = True
                identifier = ''
            if key in list(gbans.keys()):
                continue
            banlist = []
            if key in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][key]
            if (ctx.author.id in banlist or ctx.guild.id in banlist) and not ctx.author.id in self.bot.moderators:
                continue
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []

            guild = self.bot.get_guild(int(key))
            try:
                hooks = []
                try:
                    for hook_id in hook_ids:
                        if f'{hook_id}' in list(self.bot.webhook_cache[key].keys()):
                            hooks = [self.bot.webhook_cache[key][f'{hook_id}']]
                            break
                except:
                    pass
                if len(hooks) == 0:
                    hooks = await guild.webhooks()
                    for hook in hooks:
                        if not key in list(self.bot.webhook_cache.keys()):
                            self.bot.webhook_cache.update({key: {}})
                            self.bot.webhook_cache_sync.update({key: {}})
                        try:
                            hook_sync = await self.bot.loop.run_in_executor(None,
                                                                            lambda: discord.SyncWebhook.partial(
                                                                                hook.id, hook.token).fetch())
                            self.bot.webhook_cache_sync[key].update({f'{hook.id}': hook_sync})
                            self.bot.webhook_cache[key].update({f'{hook.id}': hook})
                        except:
                            continue
            except:
                continue

            for webhook in hooks:
                if webhook.id in hook_ids:
                    if not msg_resp == None:
                        ButtonStyle = discord.ButtonStyle
                        try:
                            if msg_resp.webhook_id == None:
                                msg_url = self.bot.bridged_urls[f'{msg_resp.id}'][f'{webhook.guild_id}']
                            else:
                                try:
                                    try:
                                        reference_msg_id = self.bot.bridged[f'{msg_resp.id}'][f'{webhook.guild_id}']
                                        msg_url = self.bot.bridged_urls[f'{reference_msg_id}'][f'{webhook.guild_id}']
                                    except:
                                        msg_url = self.bot.bridged_urls[f'{msg_resp.id}'][f'{webhook.guild_id}']
                                except:
                                    for key in self.bot.bridged:
                                        entry = self.bot.bridged[key]
                                        if msg_resp.id in entry.values():
                                            try:
                                                reference_msg_id = self.bot.bridged[f'{key}'][f'{webhook.guild_id}']
                                                msg_url = self.bot.bridged_urls[f'{reference_msg_id}'][
                                                    f'{webhook.guild_id}']
                                            except:
                                                msg_url = self.bot.bridged_urls[f'{key}'][f'{webhook.guild_id}']
                                            break
                            identifier = msg_resp.author.name.split('(')
                            identifier = identifier[len(identifier) - 1].replace(')', '')
                            if len(identifier)==6 and len(msg_resp.author.name.split('(')) >= 2:
                                author = f'@{msg_resp.author.name[:-9]}'
                            else:
                                author = f'@{msg_resp.author.name}'
                            if not trimmed:
                                clean_content = discord.utils.remove_markdown(msg_resp.content)

                                components = clean_content.split('<@')
                                offset = 0
                                if clean_content.startswith('<@'):
                                    offset = 1

                                while offset < len(components):
                                    try:
                                        userid = int(components[offset].split('>', 1)[0])
                                    except:
                                        offset += 1
                                        continue
                                    user = self.bot.get_user(userid)
                                    if user:
                                        clean_content = clean_content.replace(f'<@{userid}>',
                                                                              f'@{user.global_name}').replace(
                                            f'<@!{userid}>', f'@{user.global_name}')
                                    offset += 1
                                if len(clean_content) > 80:
                                    trimmed = clean_content[:-(len(clean_content) - 77)] + '...'
                                else:
                                    trimmed = clean_content
                                trimmed = trimmed.replace('\n', ' ')
                            btns = discord.ui.ActionRow(
                                discord.ui.Button(style=ButtonStyle.link, label=f'Reacting to {author}',
                                                  disabled=False,
                                                  url=msg_url)
                            )
                            if len(trimmed) > 0:
                                btns2 = discord.ui.ActionRow(
                                    discord.ui.Button(style=ButtonStyle.green, label=trimmed, disabled=True)
                                )
                            else:
                                btns2 = discord.ui.ActionRow(
                                    discord.ui.Button(style=ButtonStyle.green,
                                                      label=f'x{len(msg_resp.embeds) + len(msg_resp.attachments)}',
                                                      emoji='\U0001F3DE', disabled=True)
                                )
                        except:
                            try:
                                if msg_resp.author.id == self.bot.user.id:
                                    btns = discord.ui.ActionRow(
                                        discord.ui.Button(style=ButtonStyle.gray,
                                                          label=f'Reacting to [system message]', disabled=True)
                                    )
                                else:
                                    btns = discord.ui.ActionRow(
                                        discord.ui.Button(style=ButtonStyle.gray,
                                                          label=f'Reacting to [unknown]', disabled=True)
                                    )
                            except:
                                btns = discord.ui.ActionRow(
                                    discord.ui.Button(style=ButtonStyle.gray,
                                                      label=f'Reacting to [unknown]', disabled=True)
                                )
                    try:
                        if blocked or banned:
                            btns = discord.ui.ActionRow(
                                discord.ui.Button(style=discord.ButtonStyle.red, label=f'Reacting to [hidden]',
                                                  disabled=True)
                            )
                            raise ValueError()
                        components = discord.ui.MessageComponents(btns, btns2)
                    except:
                        components = discord.ui.MessageComponents(btns)

                    try:
                        if f'{ctx.author.id}' in self.bot.db['avatars']:
                            url = self.bot.db['avatars'][f'{ctx.author.id}']
                        else:
                            url = ctx.author.avatar.url
                    except:
                        url = None
                    author = ctx.author.global_name
                    if f'{ctx.author.id}' in list(self.bot.db['nicknames'].keys()):
                        author = self.bot.db['nicknames'][f'{ctx.author.id}']
                    if sameguild:
                        author = ctx.author.nick
                        if author == None:
                            author = ctx.author.global_name
                    if not f'{ctx.author.id}' in list(self.bot.owners.keys()):
                        self.bot.owners.update({f'{ctx.author.id}': []})
                    if sameguild:
                        msg = await webhook.send(avatar_url=url, username=author,
                                                 file=discord.File(fp="cached/"+filename), allowed_mentions=mentions,
                                                 components=components, wait=True)
                    else:
                        msg = await webhook.send(avatar_url=url, username=author + identifier_og,
                                                 file=discord.File(fp="cached/" + filename), allowed_mentions=mentions,
                                                 components=components, wait=True)
                    if sameguild:
                        sameguild_id = msg.id
                        self.bot.origin.update({f'{msg.id}': [ctx.guild.id, ctx.channel.id]})
                    else:
                        hookmsg_ids.update({f'{msg.guild.id}': msg.id})
                    self.bot.owners[f'{ctx.author.id}'].append(msg.id)
                    msg_urls.update({f'{msg.guild.id}': f'https://discord.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}'})

        for thread in threads:
            await self.bot.loop.run_in_executor(None, lambda: thread.join())
        self.bot.bridged.update({f'{sameguild_id}': hookmsg_ids})
        self.bot.bridged_urls.update({f'{sameguild_id}': msg_urls})
        try:
            os.remove("cached/"+filename)
        except:
            raise
            pass

    @commands.context_command(name='Reaction image')
    async def reaction(self, ctx, message: discord.Message):
        hooks = await ctx.guild.webhooks()
        webhook = None
        origin_room = 0
        found = False
        for hook in hooks:
            if hook.channel_id == ctx.channel.id and hook.user.id == self.bot.user.id:
                webhook = hook
                index = 0
                for key in self.bot.db['rooms']:
                    data = self.bot.db['rooms'][key]
                    if f'{ctx.guild.id}' in list(data.keys()):
                        hook_ids = data[f'{ctx.guild.id}']
                    else:
                        hook_ids = []
                    if webhook.id in hook_ids:
                        origin_room = index
                        found = True
                        if key in self.bot.db['locked'] and not ctx.author.id in self.bot.admins:
                            return
                        break
                    index += 1
                break

        if not found:
            return await ctx.send('I couldn\'t identify the UniChat room of this channel.',ephemeral=True)
        try:
            roomname = list(self.bot.db['rooms'].keys())[origin_room]
            if roomname in self.bot.db['locked'] and not ctx.author.id in self.bot.admins:
                return await ctx.send('This room is locked!',ephemeral=True)
        except:
            return await ctx.send('I couldn\'t identify the UniChat room of this channel.',ephemeral=True)
        if not ctx.channel.permissions_for(ctx.author).send_messages:
            return await ctx.send('You can\'t type in here!',ephemeral=True)
        if not webhook or not f'{webhook.id}' in f'{self.bot.db["rooms"]}':
            return await ctx.send('This isn\'t a UniChat room!', ephemeral=True)
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.blurple,label='Clueless',custom_id='clueless'),
                discord.ui.Button(style=discord.ButtonStyle.blurple, label='THINK, MARK, THINK!', custom_id='think'),
            ),
            discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.green, label='THICC, MARK, THICC!', custom_id='thicc'),
            )
        )
        msg = await ctx.send('Choose a reaction image to generate!\n\n**Blue**: Static images\n**Green**: GIFs', ephemeral=True, components=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for('component_interaction', check=check, timeout=60)
        except:
            try:
                return await msg.edit(content='Timed out.', components=None)
            except:
                return

        await interaction.response.edit_message(content='Generating...', components=None)
        msgid = msg.id
        filename = ''
        try:
            if interaction.custom_id=='clueless':
                link1 = message.author.avatar.url
                filename = await self.bot.loop.run_in_executor(None, lambda: self.clueless_gen(link1, msgid))
            elif interaction.custom_id=='think':
                link1 = ctx.author.avatar.url
                link2 = message.author.avatar.url
                filename = await self.bot.loop.run_in_executor(None, lambda: self.think(link1, link2, message.author.global_name, msgid))
            elif interaction.custom_id=='thicc':
                link1 = ctx.author.avatar.url
                link2 = message.author.avatar.url
                filename = await self.bot.loop.run_in_executor(None, lambda: self.omniman(link1, link2, msgid))
        except:
            await msg.edit('**oh no**\nAn unexpected error occurred generating the image. Please contact the developers.')
            raise
        try:
            await self.image_forward(ctx,message,filename)
        except:
            await msg.edit('**oh no**\nAn unexpected error occurred sending the image. Please contact the developers.')
            raise
        await msg.edit('Sent reaction image!')

    @commands.command(aliases=['find'])
    async def identify(self, ctx):
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members) and not ctx.author.id in self.bot.moderators:
            return
        try:
            msg = ctx.message.reference.cached_message
            if msg == None:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except:
            return await ctx.send('Invalid message!')
        hookfound = False
        for key in self.bot.db['rooms']:
            room_guilds = self.bot.db['rooms'][key]
            if f'{msg.webhook_id}' in f'{room_guilds}':
                hookfound = True
                break
        if not hookfound:
            return await ctx.send('I didn\'t forward this!')
        identifier = msg.author.name.split('(')
        identifier = identifier[len(identifier) - 1].replace(')', '')
        username = msg.author.name[:-9]
        found = False
        origin_guild = None
        origin_user = None
        for guild in self.bot.guilds:
            hashed = encrypt_string(f'{guild.id}')
            guildhash = identifier[3:]
            if hashed.startswith(guildhash):
                origin_guild = guild
                userhash = identifier[:-3]
                try:
                    matches = list(filter(lambda x: encrypt_string(f'{x.id}').startswith(userhash), guild.members))
                    if len(matches) == 1:
                        origin_user = matches[0]
                    else:
                        if len(matches)==0:
                            raise ValueError()
                        text = f'Found multiple matches for {origin_guild.name} ({origin_guild.id})'
                        for match in matches:
                            text = text + '\n{match} ({match.id})'
                        return await ctx.send(text)
                    found = True
                except:
                    continue

        if found:
            if ctx.author.id in self.bot.moderators:
                try:
                    for key in self.bot.bridged:
                        origin_msg = self.bot.bridged[key]
                        values = list(origin_msg.values())
                        if ctx.message.reference.message_id in values:
                            origin_msg_id = key
                            break
                    await ctx.send(
                        f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})\nOriginal ID {origin_msg_id}')
                except:
                    await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})\nCould not find origin message ID')
                    raise
            else:
                await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})')
        else:
            await ctx.send('Could not identify user!')

    @commands.command()
    async def getbridged(self, ctx, *, msg_id):
        if not ctx.author.id in self.bot.moderators:
            return
        try:
            content = self.bot.bridged[msg_id]
            await ctx.send(f'{content}')
        except:
            await ctx.send('No matches found!')

    @commands.command()
    async def nickname(self, ctx, *, nickname=''):
        if len(nickname) > 25:
            return await ctx.send('Please keep your nickname within 25 characters.')
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(f'{ctx.author.id}', None)
        else:
            self.bot.db['nicknames'].update({f'{ctx.author.id}': nickname})
        self.bot.db.save_data()
        await ctx.send('Nickname updated.')

    @commands.command()
    async def emojis(self, ctx, *, index=1):
        """Shows a list of all global emojis available in Unified Chat."""
        text = ''
        index = index - 1
        if index < 0:
            return await ctx.send('what')
        offset = index * 20
        emojis = []
        for emoji in self.bot.emojis:
            if emoji.guild_id in self.bot.db['emojis']:
                emojis.append(emoji)
        for i in range(20):
            try:
                emoji = emojis[i + offset]
            except:
                break
            emoji_text = f'<:{emoji.name}:{emoji.id}>'
            if emoji.animated:
                emoji_text = f'<a:{emoji.name}:{emoji.id}>'
            if len(text) == 0:
                text = f'- {emoji_text} {emoji.name}'
            else:
                text = f'{text}\n- {emoji_text} {emoji.name}'
        if len(text) == 0:
            return await ctx.send('Out of range!')
        pages = len(emojis) // 20
        if len(emojis) % 20 > 0:
            pages += 1
        embed = discord.Embed(title='UniChat Emojis list',
                              description='To use an emoji, simply send `[emoji: emoji_name]`.\nIf there\'s emojis with duplicate names, use `[emoji2: emoji_name]` to send the 2nd emoji with that name.\n' + text)
        embed.set_footer(text=f'Page {index + 1}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def emoji(self, ctx, *, emoji=''):
        # wip
        return

    @commands.command(aliases=['modcall'])
    @commands.cooldown(rate=1, per=1800, type=commands.BucketType.user)
    async def modping(self,ctx):
        """Ping all moderators to the chat! Use only when necessary, or else."""
        hooks = await ctx.channel.webhooks()
        found = False
        room = ''
        for hook in hooks:
            for key in self.bot.db['rooms']:
                if not f'{ctx.guild.id}' in list(self.bot.db['rooms'][key].keys()):
                    continue
                if hook.id in self.bot.db['rooms'][key][f'{ctx.guild.id}']:
                    found = True
                    room = key
                    break
            if found:
                break

        if not found:
            return await ctx.send('This isn\'t a UniChat room!')

        hook_id = self.bot.db['rooms'][room][f'{home_guild}'][0]
        guild = self.bot.get_guild(home_guild)
        hooks = await guild.webhooks()

        author = f'{ctx.author.name}#{ctx.author.discriminator}'
        if ctx.author.discriminator=='0':
            author = f'@{ctx.author.name}'

        for hook in hooks:
            if hook_id==hook.id:
                ch = guild.get_channel(hook.channel_id)
                try:
                    role = data["moderator_role"]
                except:
                    return await ctx.send('This instance doesn\'t have a moderator role set up. Contact your Unifier admins.')
                await ch.send(f'<@&{role}> **{author}** ({ctx.author.id}) needs your help!\n\nSent from server **{ctx.guild.name}** ({ctx.guild.id})',allowed_mentions=discord.AllowedMentions(roles=True,everyone=False,users=False))
                return await ctx.send('Moderators called!')

        await ctx.send('It appears the home guild has configured Unifier wrong, and I cannot ping its UniChat moderators.')

    @modping.error
    async def modping_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            t = int(error.retry_after)
            await ctx.send(f'You\'ve recently pinged the moderators, try again in **{t//60}** minutes and **{t%60}** seconds.')
        else:
            await ctx.send('Something went wrong pinging moderators. Please contact the developers.')

    @commands.command()
    async def delete(self, ctx):
        """Deletes all bridged messages. Does not delete the original."""
        try:
            msg_id = ctx.message.reference.message_id
        except:
            return await ctx.send('No message!')

        ownedby = []
        if f'{ctx.author.id}' in list(self.bot.owners.keys()):
            ownedby = self.bot.owners[f'{ctx.author.id}']

        obe = False
        obe_source = 'revolt'
        guild_id = ''
        channel_id = ''

        # Is this the parent?
        if not f'{msg_id}' in list(self.bot.bridged.keys()):
            # Not the parent.
            found = False
            for key in self.bot.bridged:
                if str(msg_id) in str(self.bot.bridged[key]):
                    # Found the parent!
                    found = True
                    msg_id = int(key)
                    break
            if not found:
                # Nothing, possibly OBE?
                for key in self.bot.bridged_obe:
                    if str(msg_id) in str(self.bot.bridged_obe[key]):
                        # The parent is OBE!
                        found = True
                        msg_id = key
                        obe_source = self.bot.bridged_obe[key]['source']
                        guild_id = self.bot.bridged_obe[msg_id]['server']
                        break
                if not found:
                    return await ctx.send('Could not find message in cache!')

        if not msg_id in ownedby and not ctx.author.id in self.bot.moderators:
            return await ctx.send('You didn\'t send this message!')

        hooks = await ctx.channel.webhooks()
        found = False
        origin_room = 0

        if obe:
            for key in self.bot.db['rooms_revolt']:
                # insert stuff here
                if f'{guild_id}' in list(self.bot.db['rooms_revolt'][key].keys()):
                    channel_id = self.bot.db['rooms_revolt'][key][f'{guild_id}'][0]
                    found = True
                    break

        if not found:
            return

        found = False
        roomname = ''

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{ctx.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{ctx.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    roomname = key
                    break
                index += 1
            if found:
                break

        if not found:
            return

        deleted = 0

        try:
            origins = self.bot.origin[f'{msg_id}']
            guild = self.bot.get_guild(origins[0])
            ch = guild.get_channel(origins[1])
            try:
                if obe:
                    if obe_source=='revolt' and 'revolt' in externals:
                        server_id = self.bot.bridged_obe[msg_id]['server']
                        guild = self.bot.bridged_obe.get_server(guild_id)
                        ch = guild.get_channel(channel_id)
                        msg = await ch.fetch_message(msg_id)
                        await msg.delete()
                        if not msg.author.bot:
                            return await ctx.send('Deleted parent, bridged messages should be automatically deleted.')
                else:
                    msg = await ch.fetch_message(msg_id)
                    await msg.delete()
                    if msg.webhook_id == None:
                        # Parent is a user/bot message.
                        # Since we have something to delete bridged copies on parent delete,
                        # don't bother deleting the copies.
                        # (note: webhook parents don't have bridged copies automatically deleted)
                        return await ctx.send('Deleted parent, bridged messages should be automatically deleted.')
            except:
                # Parent may be a webhook message, so try to delete as webhook.
                if not obe:
                    if key in list(data.keys()):
                        hook_ids = data[key]
                    else:
                        hook_ids = []
                    try:
                        hooks = await guild.webhooks()
                    except:
                        raise ValueError('no hooks')
                    for webhook in hooks:
                        if webhook.id in hook_ids:
                            await webhook.delete_message(msg_id)
                            break
        except:
            # Failed to delete, move on
            pass

        for key in data:
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.delete_message(self.bot.bridged[f'{msg_id}'][key])
                        deleted += 1
                    except:
                        # likely deleted msg
                        # skip cache check as it's already been done
                        pass
                    break

        ext_deleted = 0

        if 'revolt' in externals:
            data = self.bot.db['rooms_revolt'][roomname]
            if obe:
                should_delete = self.bot.bridged_obe[msg_id]
            else:
                should_delete = self.bot.bridged_revolt[f'{msg_id}']
            for key in data:
                guild = self.bot.revolt_client.get_server(key)
                ch = guild.get_channel(data[guild.id])
                if guild.id in list(should_delete.keys()):
                    msg = await ch.fetch_message(should_delete[guild.id])
                    try:
                        await msg.delete()
                        ext_deleted += 1
                    except:
                        pass

        if ctx.author.id in self.bot.moderators:
            await ctx.send(f'Deleted {deleted} forwarded messages ({ext_deleted} from externals)')
        else:
            await ctx.send('Deleted message!')

    @commands.context_command(name='Delete message')
    async def delete_ctx(self, ctx, msg: discord.Message):
        gbans = self.bot.db['banned']
        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            return await ctx.send('You or your guild is currently **global restricted**.', ephemeral=True)
        msg_id = msg.id

        ownedby = []
        if f'{ctx.author.id}' in list(self.bot.owners.keys()):
            ownedby = self.bot.owners[f'{ctx.author.id}']
        if not msg_id in ownedby and not ctx.author.id in self.bot.moderators:
            return await ctx.send('You didn\'t send this message!', ephemeral=True)
        if not msg.webhook_id and msg.author.id==ctx.author.id:
            return await ctx.send(':moyai:', ephemeral=True)

        # Is this the parent?
        if not f'{msg_id}' in list(self.bot.bridged.keys()):
            # Not the parent.
            found = False
            for key in self.bot.bridged:
                if str(msg_id) in str(self.bot.bridged[key]):
                    # Found the parent!
                    found = True
                    msg_id = int(key)
                    break
            if not found:
                # Nothing.
                return await ctx.send('Could not find message in cache!', ephemeral=True)

        hooks = await ctx.channel.webhooks()
        found = False
        origin_room = 0

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{ctx.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{ctx.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        deleted = 0

        try:
            origins = self.bot.origin[f'{msg_id}']
            guild = self.bot.get_guild(origins[0])
            ch = guild.get_channel(origins[1])
            try:
                msg = await ch.fetch_message(msg_id)
                await msg.delete()
                if msg.webhook_id == None:
                    # Parent is a user/bot message.
                    # Since we have something to delete bridged copies on parent delete,
                    # don't bother deleting the copies.
                    # (note: webhook parents don't have bridged copies automatically deleted)
                    return await ctx.send('Deleted parent, bridged messages should be automatically deleted.',
                                          ephemeral=True)
            except:
                # Parent may be a webhook message, so try to delete as webhook.
                if key in list(data.keys()):
                    hook_ids = data[key]
                else:
                    hook_ids = []
                try:
                    hooks = await guild.webhooks()
                except:
                    raise ValueError('no hooks')
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        await webhook.delete_message(msg_id)
                        break
        except:
            # Failed to delete, move on
            pass

        msg_orig = await ctx.send("Deleting...", ephemeral=True)

        for key in data:
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.delete_message(self.bot.bridged[f'{msg_id}'][key])
                        deleted += 1
                    except:
                        # likely deleted msg
                        # skip cache check as it's already been done
                        pass
                    break

        if ctx.author.id in self.bot.moderators:
            await msg_orig.edit(content=f'Deleted {deleted} forwarded messages')
        else:
            await msg_orig.edit(content='Deleted message!')

    @commands.context_command(name='Report message')
    async def report(self, ctx, msg: discord.Message):
        gbans = self.bot.db['banned']
        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            return await ctx.send('You or your guild is currently **global restricted**.', ephemeral=True)

        if not f'{msg.id}' in list(self.bot.bridged.keys()):
            # Not the parent.
            found = False
            for key in self.bot.bridged:
                if str(msg.id) in str(self.bot.bridged[key]):
                    # Found the parent!
                    found = True
                    msg_id = int(key)
                    break
            if not found:
                # Nothing.
                return await ctx.send('Could not find message in cache!', ephemeral=True)
        hooks = await ctx.guild.webhooks()
        webhook = None
        for hook in hooks:
            if hook.channel_id == ctx.channel.id and hook.user.id == self.bot.user.id:
                webhook = hook
        if not webhook or not f'{webhook.id}' in f'{self.bot.db["rooms"]}':
            return await ctx.send('This isn\'t a UniChat room!', ephemeral=True)
        roomname = None
        for room in list(self.bot.db['rooms'].keys()):
            if str(webhook.id) in str(self.bot.db['rooms'][room]):
                roomname = room
                break
        if not roomname:
            return await ctx.send('I could not identify the room this was sent in.',ephemeral=True)
        userid = msg.author.id
        if not msg.webhook_id==None:
            userid = int(list(filter(lambda x: msg.id in self.bot.owners[x], list(self.bot.owners.keys())))[0])
        if not f'{msg.id}' in f'{self.bot.bridged}':
            if msg.webhook_id:
                if not msg.webhook_id == webhook.id:
                    return await ctx.send('I didn\'t send this message!')
                userid = int(list(filter(lambda x: msg.id in self.bot.owners[x], list(self.bot.owners.keys())))[0])
        content = copy.deepcopy(msg.content)  # Prevent tampering w/ original content
        ButtonStyle = discord.ButtonStyle
        btns = discord.ui.ActionRow(
            discord.ui.Button(style=ButtonStyle.blurple, label='Spam', custom_id=f'spam', disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Abuse or harassment', custom_id=f'abuse',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Explicit or dangerous content', custom_id=f'explicit',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Violates other room rules', custom_id=f'other',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Something else', custom_id=f'misc', disabled=False)
        )
        btns_abuse = discord.ui.ActionRow(
            discord.ui.Button(style=ButtonStyle.blurple, label='Impersonation', custom_id=f'abuse_1', disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Harassment', custom_id=f'abuse_2',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Intentional misinformation', custom_id=f'abuse_3',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Derogatory language', custom_id=f'abuse_4',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Other', custom_id=f'abuse_5', disabled=False)
        )
        btns_explicit = discord.ui.ActionRow(
            discord.ui.Button(style=ButtonStyle.blurple, label='Adult content', custom_id=f'explicit_1',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Graphic/gory content', custom_id=f'explicit_2',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Encouraging real-world harm', custom_id=f'explicit_3',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Illegal content', custom_id=f'explicit_4',
                              disabled=False),
            discord.ui.Button(style=ButtonStyle.blurple, label='Other', custom_id=f'explicit_5', disabled=False)
        )
        btns2 = discord.ui.ActionRow(
            discord.ui.Button(style=ButtonStyle.gray, label='Cancel', custom_id=f'cancel', disabled=False)
        )
        components = discord.ui.MessageComponents(btns, btns2)
        msg = await ctx.send('How does this message violate our rules?', components=components, ephemeral=True)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for('component_interaction', check=check, timeout=60)
        except:
            try:
                return await ctx.interaction.edit_original_message(content='Timed out.', components=None)
            except:
                return

        cat = interaction.component.label
        asked = True
        if interaction.custom_id == 'abuse':
            components = discord.ui.MessageComponents(btns_abuse, btns2)
            await interaction.response.edit_message(content='In what way?', components=components)
        elif interaction.custom_id == 'explicit':
            components = discord.ui.MessageComponents(btns_explicit, btns2)
            await interaction.response.edit_message(content='In what way?', components=components)
        elif interaction.custom_id == 'cancel':
            return await interaction.response.edit_message(content='Cancelled.', components=None)
        else:
            asked = False
        if asked:
            try:
                interaction = await self.bot.wait_for('component_interaction', check=check, timeout=60)
            except:
                try:
                    return await ctx.interaction.edit_original_message(content='Timed out.', components=None)
                except:
                    return
            cat2 = interaction.component.label
            if interaction.custom_id == 'cancel':
                return await interaction.response.edit_message(content='Cancelled.', components=None)
        else:
            cat2 = 'none'
        self.bot.reports.update({f'{ctx.author.id}_{userid}_{msg.id}': [cat, cat2, content, roomname]})
        reason = discord.ui.ActionRow(
            discord.ui.InputText(style=discord.TextStyle.long, label='Additional details',
                                 placeholder='Add additional context or information that we should know here.',
                                 required=False)
        )
        signature = discord.ui.ActionRow(
            discord.ui.InputText(style=discord.TextStyle.short, label='Sign with your username',
                                 placeholder='Sign this only if your report is truthful and in good faith.',
                                 required=True, min_length=len(ctx.author.name), max_length=len(ctx.author.name))
        )
        modal = discord.ui.Modal(title='Report message', custom_id=f'{userid}_{msg.id}',
                                 components=[reason, signature])
        await interaction.response.send_modal(modal)

    @commands.Cog.listener()
    async def on_modal_submit(self, interaction):
        context = interaction.components[0].components[0].value
        if not interaction.components[1].components[0].value.lower() == interaction.user.name.lower():
            return
        if context is None or context == '':
            context = 'no context given'
        author = f'@{interaction.user.name}'
        if not interaction.user.discriminator == '0':
            author = f'{interaction.user.name}#{interaction.user.discriminator}'
        try:
            report = self.bot.reports[f'{interaction.user.id}_{interaction.custom_id}']
        except:
            return await interaction.response.send_message('Something went wrong while submitting the report.', ephemeral=True)
        cat = report[0]
        cat2 = report[1]
        content = report[2]
        roomname = report[3]
        userid = int(interaction.custom_id.split('_')[0])
        if len(content) > 2048:
            content = content[:-(len(content) - 2048)]
        embed = discord.Embed(title='Message report - content is as follows', description=content, color=0xffbb00)
        embed.add_field(name="Reason", value=f'{cat} => {cat2}', inline=False)
        embed.add_field(name='Context', value=context, inline=False)
        embed.add_field(name="Sender ID", value=str(userid), inline=False)
        embed.add_field(name="Message room", value=roomname, inline=False)
        embed.add_field(name="Message ID", value=interaction.custom_id.split('_')[1], inline=False)
        embed.add_field(name="Reporter ID", value=str(interaction.user.id), inline=False)
        try:
            embed.set_footer(text=f'Submitted by {author} - please do not disclose actions taken against the user.', icon_url=interaction.user.avatar.url)
        except:
            embed.set_footer(text=f'Submitted by {author} - please do not disclose actions taken against the user.')
        try:
            user = self.bot.get_user(userid)
            sender = f'@{user.name}'
            if not user.discriminator == '0':
                sender = f'{user.name}#{user.discriminator}'
            try:
                embed.set_author(name=sender, icon_url=user.avatar.url)
            except:
                embed.set_author(name=sender)
        except:
            embed.set_author(name='[unknown, check sender ID]')
        guild = self.bot.get_guild(home_guild)
        ch = guild.get_channel(reports_channel)
        btns = discord.ui.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.red, label='Delete message', custom_id=f'rpdelete_{interaction.custom_id.split("_")[1]}',
                              disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.green, label='Mark as reviewed',
                              custom_id=f'rpreview_{interaction.custom_id.split("_")[1]}',
                              disabled=False)
        )
        components = discord.ui.MessageComponents(btns)
        await ch.send(embed=embed, components=components)
        self.bot.reports.pop(f'{interaction.user.id}_{interaction.custom_id}')
        return await interaction.response.send_message(
            "# :white_check_mark: Your report was submitted!\nThanks for your report! Our moderators will have a look at it, then decide what to do.\nFor privacy reasons, we will not disclose actions taken against the user.",
            ephemeral=True)

    @commands.Cog.listener()
    async def on_component_interaction(self, interaction):
        if interaction.custom_id.startswith('rp') and not interaction.user.id in self.bot.moderators:
            return await interaction.response.send_message('buddy you\'re not a global moderator :skull:',ephemeral=True)
        if interaction.custom_id.startswith('rpdelete'):
            msg_id = int(interaction.custom_id.replace('rpdelete_','',1))
            btns = discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.red, label='Delete message',
                                  custom_id=f'rpdelete_{interaction.custom_id.split("_")[1]}',
                                  disabled=True),
                discord.ui.Button(style=discord.ButtonStyle.green, label='Mark as reviewed',
                                  custom_id=f'rpreview_{interaction.custom_id.split("_")[1]}',
                                  disabled=False)
            )
            components = discord.ui.MessageComponents(btns)

            # Is this the parent?
            if not f'{msg_id}' in list(self.bot.bridged.keys()):
                # Not the parent.
                found = False
                for key in self.bot.bridged:
                    if str(msg_id) in str(self.bot.bridged[key]):
                        # Found the parent!
                        found = True
                        msg_id = int(key)
                        break
                if not found:
                    # Nothing.
                    return await interaction.response.send_message('Could not find message in cache!', ephemeral=True)

            roomname = interaction.message.embeds[0].fields[3].value
            origin_room = 0

            for room in list(self.bot.db['rooms'].keys()):
                if room==roomname:
                    data = self.bot.db['rooms'][room]
                    break
                origin_room += 1

            deleted = 0

            try:
                origins = self.bot.origin[f'{msg_id}']
                guild = self.bot.get_guild(origins[0])
                ch = guild.get_channel(origins[1])
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.delete()
                    if msg.webhook_id == None:
                        # Parent is a user/bot message.
                        # Since we have something to delete bridged copies on parent delete,
                        # don't bother deleting the copies.
                        # (note: webhook parents don't have bridged copies automatically deleted)
                        await interaction.message.edit(components=None)
                        return await interaction.response.send_message('Deleted parent, bridged messages should be automatically deleted.',
                                              ephemeral=True)
                except:
                    # Parent may be a webhook message, so try to delete as webhook.
                    if key in list(data.keys()):
                        hook_ids = data[key]
                    else:
                        hook_ids = []
                    try:
                        hooks = await guild.webhooks()
                    except:
                        raise ValueError('no hooks')
                    for webhook in hooks:
                        if webhook.id in hook_ids:
                            await webhook.delete_message(msg_id)
                            break
            except:
                # Failed to delete, move on
                pass

            msg_orig = await interaction.response.send_message("Deleting...", ephemeral=True)

            for key in data:
                if key in list(data.keys()):
                    hook_ids = data[key]
                else:
                    hook_ids = []
                guild = self.bot.get_guild(int(key))
                try:
                    hooks = await guild.webhooks()
                except:
                    continue
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        try:
                            await webhook.delete_message(self.bot.bridged[f'{msg_id}'][key])
                            deleted += 1
                        except:
                            # likely deleted msg
                            # skip cache check as it's already been done
                            pass
                        break

            await interaction.message.edit(components=None)
            await msg_orig.edit(content=f'Deleted {deleted} forwarded messages')
        elif interaction.custom_id.startswith('rpreview_'):
            btns = discord.ui.ActionRow(
                discord.ui.Button(style=discord.ButtonStyle.red, label='Delete message',
                                  custom_id=f'rpdelete_{interaction.custom_id.split("_")[1]}',
                                  disabled=True),
                discord.ui.Button(style=discord.ButtonStyle.green, label='Mark as reviewed',
                                  custom_id=f'rpreview_{interaction.custom_id.split("_")[1]}',
                                  disabled=True)
            )
            components = discord.ui.MessageComponents(btns)
            embed = interaction.message.embeds[0]
            embed.color = 0x00ff00
            author = f'@{interaction.user.name}'
            if not interaction.user.discriminator == '0':
                author = f'{interaction.user.name}#{interaction.user.discriminator}'
            embed.title = f'This report has been reviewed by {author}!'
            await interaction.response.edit_message(embed=embed,components=components)

    @commands.command(hidden=True)
    async def testreg(self, ctx, *, args=''):
        if not ctx.author.id == 356456393491873795:
            return
        if 'dereg' in args:
            await self.bot.register_application_commands(commands=[])
            return await ctx.send('gone, reduced to atoms (hopefully)')
        toreg = []
        for command in self.bot.commands:
            if isinstance(command, commands.core.ContextMenuCommand):
                toreg.append(command)
        await self.bot.register_application_commands(commands=toreg)
        return await ctx.send(f'Registered {len(toreg)} commands to bot')

    @commands.Cog.listener()
    async def on_message(self, message):
        author_rp = message.author
        content_rp = message.content
        if not message.webhook_id == None:
            # webhook msg
            return

        if message.guild == None:
            return

        if message.content.startswith(self.bot.command_prefix):
            cmd = message.content.replace(self.bot.command_prefix, '', 1).split()[0]
            if not self.bot.get_command(cmd) == None:
                return

        gbans = self.bot.db['banned']

        if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
            ct = time.time()
            cdt = datetime.utcnow()
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    self.bot.db.update()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.update()
                else:
                    return

        if message.author.id == self.bot.user.id:
            return

        try:
            hooks = await message.channel.webhooks()
        except:
            return
        found = False
        origin_room = 0

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{message.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{message.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    if key in self.bot.db['locked'] and not message.author.id in self.bot.admins:
                        return
                    break
                index += 1
            if found:
                break

        if not found:
            return

        roomname = list(self.bot.db['rooms'].keys())[origin_room]
        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        og_embeds = []
        if message.author.bot or len(message.embeds) > 0:
            for emb in message.embeds:
                og_embeds.append(emb)

        if not found:
            return

        if 'discord.gg/' in message.content or 'discord.com/invite/' in message.content:
            try:
                await message.delete()
            except:
                pass
            return await message.channel.send(f'<@{message.author.id}> Invites aren\'t allowed!')

        # Low-latency RapidPhish implementation
        # Prevent message tampering
        urls = findurl(message.content)
        filtered = message.content.replace('\\', '')
        for url in urls:
            filtered = filtered.replace(url, '', 1)
        for word in filtered.split():
            # kill hyperlinks :woke:
            if '](' in word:
                # likely hyperlink, lets kill it
                if word.startswith('['):
                    word = word[1:]
                if word.endswith(')'):
                    word = word[:-1]
                word = word.replace(')[', ' ')
                words = word.split()
                found = False
                for word2 in words:
                    words2 = word2.replace('](', ' ').split()
                    for word3 in words2:
                        if '.' in word3:
                            if not word3.startswith('http://') or not word3.startswith('https://'):
                                word3 = 'http://' + word3
                            while True:
                                try:
                                    word3 = await self.bot.loop.run_in_executor(None, lambda: bypass_killer(word3))
                                except:
                                    break
                            if len(word3.split('.')) == 1:
                                continue
                            else:
                                if word3.split('.')[1] == '':
                                    continue
                            try:
                                get_tld(word3.lower(), fix_protocol=True)
                                if '](' in word3.lower():
                                    word3 = word3.replace('](', ' ', 1).split()[0]
                                urls.append(word3.lower())
                                found = True
                            except:
                                pass

                if found:
                    # successful link detection from hyperlink yippee
                    continue
            if '.' in word:
                while True:
                    try:
                        word = await self.bot.loop.run_in_executor(None, lambda: bypass_killer(word))
                    except:
                        break
                if len(word.split('.')) == 1:
                    continue
                else:
                    if word.split('.')[1] == '':
                        continue
                try:
                    get_tld(word.lower(), fix_protocol=True)
                    if '](' in word.lower():
                        word = word.replace('](', ' ', 1).split()[0]
                    urls.append(word.lower())
                except:
                    pass

        key = 0
        for url in urls:
            url = url.lower()
            urls[key] = url
            if not url.startswith('http://') and not url.startswith('https://'):
                urls[key] = f'http://{url}'
            if '](' in url:
                urls[key] = url.replace('](', ' ', 1).split()[0]
            key = key + 1

        if len(urls) > 0:
            rpresults = rapidphish.compare_urls(urls, 0.85)
            if not rpresults.final_verdict=='safe':
                try:
                    await message.delete()
                except:
                    pass
                if author_rp.discriminator == '0':
                    user = f'@{author_rp.name}'
                else:
                    user = f'{author_rp.name}#{author_rp.discriminator}'
                embed = discord.Embed(title='Suspicious link detected <:nevsus:1024028464954744832>',
                                      description='RapidPhish Low-Latency Implementation has detected a suspicious link. But don\'t worry, we\'ve scanned it and took the appropriate action that you\'ve set us to take. <:neviraldi:981611276985831424>\n\nWe\'ll send the results here for you to see.',
                                      color=0x0000ff, timestamp=datetime.utcnow())
                try:
                    embed.set_author(name=user, icon_url=author_rp.avatar)
                except:
                    embed.set_author(name=user, icon_url=author_rp.avatar)
                embed.set_footer(text='Protected by RapidPhish LLI')
                content = content_rp
                if len(content) > 1020:
                    content = content_rp[:-(len(content_rp) - 1017)]
                embed.add_field(name='Message', value=f'||{content}||', inline=False)
                embed.add_field(name='User ID', value=f'{author_rp.id}', inline=False)
                embed.add_field(name='Detected by', value='RapidPhish', inline=False)
                embed.add_field(name='Action taken', value='forwarding blocked', inline=True)
                guild = self.bot.get_guild(home_guild)
                ch = guild.get_channel(reports_channel)
                await ch.send(embed=embed)
                try:
                    await message.channel.send('One or more URLs were flagged as potentially dangerous. **This incident has been reported.**',reference=message)
                except:
                    await message.channel.send('One or more URLs were flagged as potentially dangerous. **This incident has been reported.**')
                return

        if not message.guild.explicit_content_filter == discord.ContentFilter.all_members:
            return await message.channel.send(
                '**Hold up a sec!**\nThis server isn\'t letting Discord make sure nothing NSFW is being sent in SFW channels, meaning adult content could be sent over UniChat. We don\'t want that!'
                + '\n\nPlease ask your server admins to enable explicit content scanning for **all members**.',
                reference=message)
        elif message.channel.nsfw:
            return await message.channel.send(
                '**Hold up a sec!**\nThis channel is marked as NSFW, meaning Discord won\'t go mad when you try sending adult content over UniChat. We don\'t want that!'
                + '\n\nPlease ask your server admins to unmark this channel as NSFW.', reference=message)

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = ' (' + user_hash + guild_hash + ')'

        hookmsg_ids = {}
        msg_urls = {}

        emojified = False

        content = message.content.split('[emoji')
        parse_index = -1
        og_msg_content = message.content
        for element in content:
            parse_index += 1
            if not message.content.startswith('[emoji') and parse_index == 0:
                continue
            if message.author.bot or not '[emoji' in message.content:
                break
            if not ']' in element:
                continue
            parts = element.split(']')[0].split(': ')
            try:
                name = parts[1]
                if name.endswith('\\'):
                    raise ValueError()
            except:
                continue

            noindex = False
            try:
                index = int(parts[0])
            except:
                noindex = True
                index = 1

            skip = []
            failed = False
            emoji_text = ''

            for x in range(index):
                emoji = discord.utils.find(
                    lambda e: e.name == name and not e.id in skip and e.guild_id in self.bot.db['emojis'],
                    self.bot.emojis)
                if emoji == None:
                    failed = True
                    break
                skip.append(emoji.id)
                emoji_text = f'<:{emoji.name}:{emoji.id}>'
                if emoji.animated:
                    emoji_text = f'<a:{emoji.name}:{emoji.id}>'

            if failed:
                continue

            if noindex:
                message.content = message.content.replace(f'[emoji: {name}]', emoji_text, 1)
            else:
                message.content = message.content.replace(f'[emoji{index}: {name}]', emoji_text, 1)
            emojified = True

        if og_msg_content == message.content:
            emojified = False

        is_pr = False
        is_pr_ref = False
        ref_id = ''
        if origin_room == pr_room_index:
            is_pr = True
            pr_id = genid()
            pr_ids = {}
        if origin_room == pr_ref_room_index:
            passed = True
            if message.content.startswith('['):
                components = message.content.split(']', 1)
                if len(components) == 1:
                    passed = False
                else:
                    ref_id = components[0].replace('[', '')
                    if ref_id == 'latest' or ref_id == 'newest' or ref_id == 'recent':
                        ref_id = list(self.bot.prs.keys())[len(list(self.bot.prs.keys())) - 1]
                    if not ref_id in list(self.bot.prs.keys()):
                        return await message.channel.send('This isn\'t a valid PR ID!')
                    else:
                        content = components[1]
                        while content.startswith(' ') or content.startswith('\n'):
                            if content.startswith(' '):
                                content = content.replace(' ', '', 1)
                            else:
                                content = content.replace('\n', '', 1)
                        if len(content) == 0:
                            passed = False
            else:
                passed = False
            if passed:
                is_pr = True
                is_pr_ref = True
                message.content = content

        if not allow_prs:
            is_pr = False
            is_pr_ref = False

        pr_deletefail = False

        if emojified or is_pr:
            try:
                await message.delete()
            except:
                if is_pr_ref:
                    return await message.channel.send(
                        'I need to be able to delete messages in order to process PR references.', reference=message)
                elif is_pr and not emojified:
                    pr_deletefail = True
                    await message.channel.send(f'Assigned PR ID: `{pr_id}`\nUse this to reference this PR message.',
                                               reference=message)
                else:
                    return await message.channel.send(
                        'I need to be able to delete messages in order to process global emojis.', reference=message)

        identifier_cache = identifier
        banned = False

        if not (message.type == discord.MessageType.default or
                message.type == discord.MessageType.reply or
                message.type == discord.MessageType.application_command):
            return

        # Forwarding
        results = []
        sameguild_id = []
        threads = []
        trimmed = None
        for key in data:
            blocked = False
            sameguild = False
            if len(identifier) == 0:
                # restore identifier
                identifier = identifier_cache
            if int(key) == message.guild.id:
                sameguild = True
                identifier = ''
                if not emojified and not is_pr or pr_deletefail:
                    if is_pr and not is_pr_ref:
                        pr_ids.update({f'{message.guild.id}': message.id})

                    # Not using webhooks - make parent the message.
                    self.bot.origin.update({f'{message.id}': [message.guild.id, message.channel.id]})
                    continue
            if key in list(gbans.keys()):
                continue
            banlist = []
            if key in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][key]
            if (
                    message.author.id in banlist or message.guild.id in banlist) and not message.author.id in self.bot.moderators:
                continue
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = []
                try:
                    for hook_id in hook_ids:
                        if f'{hook_id}' in list(self.bot.webhook_cache[key].keys()):
                            hooks = [self.bot.webhook_cache[key][f'{hook_id}']]
                            break
                except:
                    pass
                if len(hooks) == 0:
                    hooks = await guild.webhooks()
                    for hook in hooks:
                        if not key in list(self.bot.webhook_cache.keys()):
                            self.bot.webhook_cache.update({key: {}})
                            self.bot.webhook_cache_sync.update({key: {}})
                        try:
                            hook_sync = await self.bot.loop.run_in_executor(None, lambda: discord.SyncWebhook.partial(hook.id, hook.token).fetch())
                            self.bot.webhook_cache_sync[key].update({f'{hook.id}': hook_sync})
                            self.bot.webhook_cache[key].update({f'{hook.id}': hook})
                        except:
                            continue
            except:
                continue
            dont_attach = False

            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        if f'{message.author.id}' in self.bot.db['avatars']:
                            url = self.bot.db['avatars'][f'{message.author.id}']
                        else:
                            url = message.author.avatar.url
                    except:
                        url = None
                    files = []
                    index = 0
                    for attachment in message.attachments:
                        if dont_attach:
                            break
                        if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                            not 'image' in attachment.content_type) or attachment.size > 25000000:
                            continue
                        try:
                            try:
                                file = await attachment.to_file(use_cached=True, spoiler=attachment.is_spoiler())
                            except:
                                file = await attachment.to_file(use_cached=True, spoiler=False)
                            files.append(file)
                            index += 1
                        except:
                            pass
                    msg = None
                    if not message.reference == None:
                        msg = message.reference.cached_message
                        if msg == None:
                            try:
                                msg = await message.channel.fetch_message(message.reference.message_id)
                            except:
                                pass
                    if (not message.reference == None and not msg == None) or is_pr:
                        if not message.reference == None and not msg == None:
                            if f'{msg.author.id}' in list(gbans.keys()) or f'{msg.guild.id}' in list(gbans.keys()):
                                banned = True
                            elif (
                                    msg.author.id in banlist or msg.guild.id in banlist) and not msg.author.id in self.bot.moderators:
                                blocked = True
                            if msg == None:
                                msg = await message.channel.fetch_message(message.reference.message_id)

                            if not msg.webhook_id == None:
                                author = f'@{msg.author.name}'
                                identifier_resp = author.split('(')
                                identifier_resp = identifier_resp[len(identifier_resp) - 1]
                                author = author[:-(2 + len(identifier_resp))]
                            else:
                                author = f'@{msg.author.global_name}'
                            content = discord.utils.remove_markdown(msg.clean_content)
                            if len(msg.content) == 0:
                                if len(msg.attachments) == 0:
                                    if len(msg.embeds) > 0:
                                        content = '[embed]'
                                    else:
                                        content = '[no content]'
                                else:
                                    content = ''
                                    for attachment in msg.attachments:
                                        if content == '':
                                            content = f'[{attachment.filename}]'
                                        else:
                                            content = f'{content}\n[{attachment.filename}]'
                            if banned or blocked:
                                author = '[hidden]'
                                if banned:
                                    content = '**GLOBAL BANNED - MESSAGE HIDDEN**\nThe author of this message replied to a global banned user or server. Global bans are placed on users and servers that break UniChat rules continuously or/and severely.'
                                elif blocked:
                                    content = '**SERVER BANNED - MESSAGE HIDDEN**\nThe author of this message replied to a server banned user or server. Server bans are placed on users and servers by this server\'s moderators.\nAsk them to unblock the origin user or server.'
                            embed = discord.Embed(title=f'Replying to {author}', description=content, color=0xeba134)
                            if not msg.author.avatar == None and not banned and not blocked:
                                embed.set_author(name=author, icon_url=msg.author.avatar.url)
                            else:
                                embed.set_author(name=author)
                        embeds = og_embeds.copy()
                        components = None

                        if not message.reference == None and not blocked and not banned:
                            if not message.author.bot:
                                embeds = []
                            else:
                                embeds = message.embeds
                            ButtonStyle = discord.ButtonStyle
                            if banned or blocked:
                                btns = discord.ui.ActionRow(
                                    discord.ui.Button(style=ButtonStyle.red, label=f'Replying to [hidden]',
                                                      disabled=True)
                                )
                            else:
                                try:
                                    globalmoji = False
                                    if msg.webhook_id == None:
                                        msg_url = self.bot.bridged_urls[f'{msg.id}'][f'{webhook.guild_id}']
                                    else:
                                        try:
                                            try:
                                                reference_msg_id = self.bot.bridged[f'{msg.id}'][f'{webhook.guild_id}']
                                                globalmoji = True
                                                msg_url = self.bot.bridged_urls[f'{reference_msg_id}'][f'{webhook.guild_id}']
                                            except:
                                                msg_url = self.bot.bridged_urls[f'{msg.id}'][f'{webhook.guild_id}']
                                        except:
                                            for key in self.bot.bridged:
                                                entry = self.bot.bridged[key]
                                                if msg.id in entry.values():
                                                    try:
                                                        reference_msg_id = self.bot.bridged[f'{key}'][f'{webhook.guild_id}']
                                                        msg_url = self.bot.bridged_urls[f'{reference_msg_id}'][f'{webhook.guild_id}']
                                                    except:
                                                        msg_url = self.bot.bridged_urls[f'{key}'][f'{webhook.guild_id}']
                                                    break
                                    if globalmoji:
                                        author = f'@{msg.author.name}'
                                    if not trimmed:
                                        clean_content = discord.utils.remove_markdown(msg.content)

                                        components = clean_content.split('<@')
                                        offset = 0
                                        if clean_content.startswith('<@'):
                                            offset = 1

                                        while offset < len(components):
                                            try:
                                                userid = int(components[offset].split('>',1)[0])
                                            except:
                                                offset += 1
                                                continue
                                            user = self.bot.get_user(userid)
                                            if user:
                                                clean_content = clean_content.replace(f'<@{userid}>',f'@{user.global_name}').replace(f'<@!{userid}>',f'@{user.global_name}')
                                            offset += 1
                                        if len(clean_content) > 80:
                                            trimmed = clean_content[:-(len(clean_content) - 77)] + '...'
                                        else:
                                            trimmed = clean_content
                                        trimmed = trimmed.replace('\n', ' ')
                                    btns = discord.ui.ActionRow(
                                        discord.ui.Button(style=ButtonStyle.link, label=f'Replying to {author}',
                                                          disabled=False,
                                                          url=msg_url)
                                    )
                                    if len(trimmed) > 0:
                                        btns2 = discord.ui.ActionRow(
                                            discord.ui.Button(style=ButtonStyle.blurple, label=trimmed, disabled=True)
                                        )
                                    else:
                                        btns2 = discord.ui.ActionRow(
                                            discord.ui.Button(style=ButtonStyle.blurple,
                                                              label=f'x{len(msg.embeds) + len(msg.attachments)}',
                                                              emoji='\U0001F3DE', disabled=True)
                                        )
                                except:
                                    if is_pr_ref and sameguild and not blocked and not banned:
                                        btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=ButtonStyle.link, label=f'Replying to {author}',
                                                              disabled=False,
                                                              url=f'https://discord.com/channels/{webhook.guild_id}/{webhook.channel_id}/{message.reference.message_id}')
                                        )
                                    else:
                                        try:
                                            if msg.author.id == self.bot.user.id:
                                                btns = discord.ui.ActionRow(
                                                    discord.ui.Button(style=ButtonStyle.gray,
                                                                      label=f'Replying to [system message]', disabled=True)
                                                )
                                            else:
                                                btns = discord.ui.ActionRow(
                                                    discord.ui.Button(style=ButtonStyle.gray,
                                                                      label=f'Replying to [unknown]', disabled=True)
                                                )
                                        except:
                                            btns = discord.ui.ActionRow(
                                                discord.ui.Button(style=ButtonStyle.gray,
                                                                  label=f'Replying to [unknown]', disabled=True)
                                            )
                        try:
                            if blocked or banned:
                                btns = discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.red, label=f'Replying to [hidden]',
                                                      disabled=True)
                                )
                                raise ValueError()
                            if is_pr:
                                if is_pr_ref:
                                    try:
                                        if f'{webhook.guild.id}' in list(self.bot.db['rooms']['pr'].keys()):
                                            hook = self.bot.db['rooms']['pr'][f'{webhook.guild.id}'][0]
                                        else:
                                            raise ValueError()
                                        try:
                                            hook = self.bot.webhook_cache[f'{webhook.guild.id}'][hook]
                                        except:
                                            hooks_2 = await webhook.guild.webhooks()
                                            for hook_obj in hooks_2:
                                                if hook_obj.id == hook:
                                                    hook = hook_obj
                                                    break
                                        reference_msg_id = self.bot.prs[ref_id][f'{webhook.guild_id}']
                                        ref_btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=discord.ButtonStyle.link,
                                                              label=f'Reference to PR #{ref_id}',
                                                              url=f'https://discord.com/channels/{webhook.guild_id}/{hook.channel_id}/{reference_msg_id}',
                                                              emoji='\U0001F517',
                                                              disabled=False)
                                        )
                                    except:
                                        traceback.print_exc()
                                        ref_btns = discord.ui.ActionRow(
                                            discord.ui.Button(style=discord.ButtonStyle.gray,
                                                              label=f'Reference to PR #{ref_id}', emoji='\U0001F517',
                                                              disabled=True)
                                        )
                                else:
                                    ref_btns = discord.ui.ActionRow(
                                        discord.ui.Button(style=discord.ButtonStyle.blurple, label=f'PR ID: {pr_id}',
                                                          emoji='\U0001F4AC', disabled=True)
                                    )
                                try:
                                    components = discord.ui.MessageComponents(ref_btns, btns, btns2)
                                except:
                                    try:
                                        components = discord.ui.MessageComponents(ref_btns, btns)
                                    except:
                                        components = discord.ui.MessageComponents(ref_btns)
                            else:
                                components = discord.ui.MessageComponents(btns, btns2)
                        except:
                            components = discord.ui.MessageComponents(btns)
                        author_resp = message.author.global_name
                        if f'{message.author.id}' in list(self.bot.db['nicknames'].keys()):
                            author_resp = self.bot.db['nicknames'][f'{message.author.id}']
                        if sameguild:
                            author_resp = message.author.nick
                            if author_resp == None:
                                author_resp = message.author.global_name
                        try:
                            msg = await webhook.send(avatar_url=url, username=author_resp + identifier,
                                                     content=message.content, embeds=embeds,
                                                     files=files, allowed_mentions=mentions, wait=True,
                                                     components=components)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}': [message.guild.id, message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}': msg.id})
                            if is_pr and not is_pr_ref:
                                pr_ids.update({f'{webhook.guild_id}': msg.id})
                            if not f'{message.author.id}' in list(self.bot.owners.keys()):
                                self.bot.owners.update({f'{message.author.id}': []})
                            self.bot.owners[f'{message.author.id}'].append(msg.id)
                            msg_urls.update({f'{msg.guild.id}':f'https://discord.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}'})
                        except discord.HTTPException as e:
                            if e.code == 413:
                                files = []
                                msg = await webhook.send(avatar_url=url, username=author + identifier,
                                                         content=message.content, embeds=embeds,
                                                         allowed_mentions=mentions, wait=True)
                                await message.channel.send(
                                    'An attachment or two was too large - attachments will not be sent.\nPlease send a URL instead.',
                                    reference=message)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}': [message.guild.id, message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}': msg.id})
                            if is_pr and not is_pr_ref:
                                pr_ids.update({f'{webhook.guild_id}': msg.id})
                            if not f'{message.author.id}' in list(self.bot.owners.keys()):
                                self.bot.owners.update({f'{message.author.id}': []})
                            self.bot.owners[f'{message.author.id}'].append(msg.id)
                            msg_urls.update({f'{msg.guild.id}': f'https://discord.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}'})
                    else:
                        if message.author.bot:
                            embeds = message.embeds
                        else:
                            embeds = []
                        author = message.author.global_name
                        if f'{message.author.id}' in list(self.bot.db['nicknames'].keys()):
                            author = self.bot.db['nicknames'][f'{message.author.id}']
                        if sameguild:
                            author = message.author.nick
                            if author == None:
                                author = message.author.global_name
                        try:
                            if not f'{message.author.id}' in list(self.bot.owners.keys()):
                                self.bot.owners.update({f'{message.author.id}': []})
                            if webhook.guild_id in self.bot.db['experiments']['threaded_bridge']:
                                synchook = self.bot.webhook_cache_sync[f'{webhook.guild_id}'][f'{webhook.id}']

                                def thread_msg():
                                    sameguild_tr = sameguild
                                    guild_id = synchook.guild_id
                                    msg = synchook.send(avatar_url=url, username=author + identifier,
                                                             content=message.content, embeds=embeds,
                                                             files=files, allowed_mentions=mentions, wait=True)
                                    results.append(msg)

                                    if sameguild_tr:
                                        sameguild_id.append(msg.id)
                                    if not sameguild_tr:
                                        hookmsg_ids.update({f'{guild_id}': msg.id})
                                    self.bot.owners[f'{message.author.id}'].append(msg.id)
                                    msg_urls.update({f'{guild_id}': f'https://discord.com/channels/{guild_id}/{msg.channel.id}/{msg.id}'})

                                thread = threading.Thread(target=thread_msg)
                                thread.start()
                                threads.append(thread)
                                if sameguild:
                                    await self.bot.loop.run_in_executor(None, lambda: thread.join())
                                    sameguild_id = sameguild_id[0]
                                    self.bot.origin.update({f'{sameguild_id}': [message.guild.id, message.channel.id]})
                            else:
                                msg = await webhook.send(avatar_url=url, username=author + identifier,
                                                         content=message.content, embeds=embeds,
                                                         files=files, allowed_mentions=mentions, wait=True)
                                if sameguild:
                                    sameguild_id = msg.id
                                    self.bot.origin.update({f'{msg.id}': [message.guild.id, message.channel.id]})
                                else:
                                    hookmsg_ids.update({f'{msg.guild.id}': msg.id})
                                self.bot.owners[f'{message.author.id}'].append(msg.id)
                                msg_urls.update({f'{msg.guild.id}': f'https://discord.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}'})
                        except discord.HTTPException as e:
                            if e.code == 413:
                                files = []
                                msg = await webhook.send(avatar_url=url, username=author + identifier,
                                                         content=message.content, embeds=embeds,
                                                         allowed_mentions=mentions, wait=True)
                                await message.channel.send(
                                    'An attachment or two was too large - attachments will not be sent.\nPlease send a URL instead.',
                                    reference=message)
                            if sameguild:
                                sameguild_id = msg.id
                                self.bot.origin.update({f'{msg.id}': [message.guild.id, message.channel.id]})
                            else:
                                hookmsg_ids.update({f'{msg.guild.id}': msg.id})
                            if is_pr and not is_pr_ref:
                                pr_ids.update({f'{webhook.guild_id}': msg.id})
                            if not f'{message.author.id}' in list(self.bot.owners.keys()):
                                self.bot.owners.update({f'{message.author.id}': []})
                            self.bot.owners[f'{message.author.id}'].append(msg.id)
                        except:
                            await message.channel.send('**oh no**\nAn unexpected error occurred handling this message. Please contact the developers.')
                            raise
        files = []
        if 'revolt' in externals:
            testrooms = {"01HDS71G78AT18B9DEW3K6KXST":["01HDS71G78TTV3J3HMX3FB180Q"]}

            for attachment in message.attachments:
                file = await attachment.to_file(use_cached=True, spoiler=attachment.is_spoiler())
                files.append(revolt.File(file.fp.read(),filename=file.filename,spoiler=file.spoiler))

            # for guild in self.bot.db['rooms_revolt'][roomname]:
            for guild in testrooms:
                guild = self.bot.revolt_client.get_server(guild)
                ch = guild.get_channel(testrooms[guild.id][0])
                # ch = guild.get_channel(self.bot.db['rooms_revolt'][roomname][guild.id])
                try:
                    persona = revolt.Masquerade(name=author + identifier, avatar=message.author.avatar.url)
                except:
                    persona = revolt.Masquerade(name=author + identifier, avatar=None)
                await ch.send(content=message.content,attachments=files,masquerade=persona)

        for thread in threads:
            await self.bot.loop.run_in_executor(None, lambda: thread.join())
        self.bot.owners[f'{message.author.id}'].append(message.id)
        if is_pr and not is_pr_ref:
            self.bot.prs.update({pr_id: pr_ids})
        msg_urls.update({f'{message.guild.id}':f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'})
        if emojified or is_pr_ref or is_pr:
            self.bot.bridged.update({f'{sameguild_id}': hookmsg_ids})
            self.bot.bridged_urls.update({f'{sameguild_id}': msg_urls})
        else:
            self.bot.bridged.update({f'{message.id}': hookmsg_ids})
            self.bot.bridged_urls.update({f'{message.id}': msg_urls})
        try:
            del files
        except:
            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content == after.content:
            return

        message = after

        if message.guild == None:
            return

        gbans = self.bot.db['banned']

        if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
            ct = time.time()
            cdt = datetime.utcnow()
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    self.bot.db.update()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.update()
                else:
                    return

        if not message.webhook_id == None:
            # webhook msg, dont bother
            return

        if message.author.id == self.bot.user.id:
            return

        hooks = await message.channel.webhooks()
        found = False
        origin_room = 0

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{message.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{message.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    if key in self.bot.db['locked'] and not message.author.id in self.bot.admins:
                        return
                    break
                index += 1
            if found:
                break

        if not found:
            return

        roomname = list(self.bot.db['rooms'].keys())[origin_room]
        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = user_hash + guild_hash

        for key in data:
            if int(key) == message.guild.id:
                continue
            if key in gbans:
                continue
            banlist = []
            if f'{message.guild.id}' in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][f'{message.guild.id}']
            if message.author.id in banlist and not message.author.id in self.bot.moderators:
                continue
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.edit_message(self.bot.bridged[f'{message.id}'][key],
                                                   content=message.content, allowed_mentions=mentions)
                    except:
                        # likely deleted msg
                        try:
                            self.bot.bridged[f'{message.id}']
                        except:
                            # message wiped from cache
                            return
                        pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        gbans = self.bot.db['banned']

        if f'{message.author.id}' in gbans or f'{message.guild.id}' in gbans:
            return

        if not message.webhook_id == None:
            # webhook msg, dont bother
            return

        if message.author.id == self.bot.user.id:
            return

        try:
            hooks = await message.channel.webhooks()
        except:
            hooks = await message.guild.webhooks()

        found = False
        origin_room = 0

        for webhook in hooks:
            index = 0
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{message.guild.id}' in list(data.keys()):
                    hook_ids = data[f'{message.guild.id}']
                else:
                    hook_ids = []
                if webhook.id in hook_ids:
                    origin_room = index
                    found = True
                    break
                index += 1
            if found:
                break

        if not found:
            return

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        guild_hash = encrypt_string(f'{message.guild.id}')[:3]
        identifier = user_hash + guild_hash

        guild = self.bot.get_guild(home_guild)
        ch = guild.get_channel(logs_channel)

        roomname = list(self.bot.db['rooms'].keys())[origin_room]

        content = message.content

        if len(message.content) == 0:
            content = '[no content]'
        embed = discord.Embed(title=f'Message deleted from `{roomname}`', description=content)
        embed.add_field(name='Embeds', value=f'{len(message.embeds)} embeds, {len(message.attachments)} files',
                        inline=False)
        embed.add_field(name='IDs', value=f'MSG: {message.id}\nSVR: {message.guild.id}\nUSR: {message.author.id}',
                        inline=False)
        if message.author.discriminator == '0':
            author = f'@{message.author.name}'
        else:
            author = f'{message.author.name}#{message.author.discriminator}'
        try:
            embed.set_author(name=author, icon_url=message.author.avatar.url)
        except:
            embed.set_author(name=author)
        await ch.send(embed=embed)

        for key in data:
            if int(key) == message.guild.id:
                continue
            if key in gbans:
                continue
            banlist = []
            if f'{message.guild.id}' in list(self.bot.db['blocked'].keys()):
                banlist = self.bot.db['blocked'][f'{message.guild.id}']
            if message.author.id in banlist and not message.author.id in self.bot.moderators:
                continue
            if key in list(data.keys()):
                hook_ids = data[key]
            else:
                hook_ids = []
            sent = False
            guild = self.bot.get_guild(int(key))
            try:
                hooks = await guild.webhooks()
            except:
                continue
            for webhook in hooks:
                if webhook.id in hook_ids:
                    try:
                        await webhook.delete_message(self.bot.bridged[f'{message.id}'][key])
                    except:
                        # likely deleted msg
                        try:
                            self.bot.bridged[f'{message.id}']
                        except:
                            # message wiped from cache
                            return
                        pass


def setup(bot):
    bot.add_cog(Bridge(bot))
