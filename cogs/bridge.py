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
import ast
import os
from io import BytesIO
from tld import get_tld
from utils import rapidphish
import threading

with open('config.json', 'r') as file:
    data = json.load(file)

home_guild = data["home_guild"]
logs_channel = data["logs_channel"]
reports_channel = data["reports_channel"]
externals = data["external"]
owner = data["owner"]
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

class ExternalReference:
    def __init__(self, guild_id, channel_id, message_id):
        self.guild = guild_id
        self.channel = channel_id
        self.id = message_id

class SelfDeleteException(Exception):
    pass

class UnifierMessage:
    def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room, external_urls=None, webhook=False):
        self.author_id = author_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.id = original
        self.copies = copies
        self.external_copies = external_copies
        self.urls = urls
        self.external_urls = external_urls or {}
        self.source = source
        self.room = room
        self.webhook = webhook

    async def fetch_id(self, guild_id):
        if guild_id == self.guild_id:
            return self.id

        return self.copies[guild_id][1]

    async def fetch_channel(self, guild_id):
        if guild_id == self.guild_id:
            return self.channel_id

        return self.copies[guild_id][0]

    async def fetch_url(self, guild_id):
        if guild_id==self.guild_id:
            return f'https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.id}'

        return self.urls[guild_id]

    async def fetch_external_url(self, source, guild_id):
        return self.external_urls[source][guild_id]

    async def fetch_external(self, platform: str, guild_id: str):
        return ExternalReference(guild_id, self.external_copies[platform][guild_id][0], self.external_copies[platform][guild_id][1])

class UnifierBridge:

    def __init__(self, bot, webhook_cache=None):
        self.bot = bot
        self.bridged = []
        self.prs = {}
        self.webhook_cache = webhook_cache or {}

    async def fetch_message(self,message_id):
        for message in self.bridged:
            if str(message.id)==str(message_id) or str(message_id) in str(message.copies) or str(message_id) in str(message.external_copies):
                return message
        raise ValueError("No message found")

    async def indexof(self,message_id):
        index = 0
        for message in self.bridged:
            if str(message.id)==str(message_id) or str(message_id) in str(message.copies) or str(message_id) in str(message.external_copies):
                return index
            index += 1
        raise ValueError("No message found")

    async def delete_parent(self, message):
        if not message.webhook_id:
            await message.delete()
            return
        msg: UnifierMessage = await self.fetch_message(message.id)
        if msg.source=='discord':
            guild = self.bot.get_guild(int(msg.guild_id))
            ch = guild.get_channel(int(msg.channel_id))
            todelete = await ch.fetch_message(int(msg.id))
            await todelete.delete()
        elif msg.source=='revolt':
            ch = await self.bot.revolt_client.fetch_channel(msg.channel_id)
            todelete = await ch.fetch_message(msg.id)
            await todelete.delete()

    async def delete_copies(self, message):
        msg: UnifierMessage = await self.fetch_message(message.id)
        count = 0

        async def delete_discord(msgs):
            count = 0
            for key in list(self.bot.db['rooms'][msg.room].keys()):
                guild = self.bot.get_guild(key)
                hooks = await guild.webhooks()
                webhook = None

                # Fetch webhook
                for hook in hooks:
                    if int(self.bot.db['rooms'][msg.room][key])==hook.id:
                        webhook: discord.Webhook = hook
                        break

                if not webhook:
                    # No webhook found
                    continue

                try:
                    await webhook.delete_message(int(msgs[key]))
                    count += 1
                except:
                    pass
            return count

        async def delete_revolt(msgs):
            count = 0
            for key in list(self.bot.db['rooms_revolt'][msg.room].keys()):
                try:
                    ch = await self.bot.revolt_client.fetch_channel(self.bot.db['rooms_revolt'][msg.room][key])
                    todelete = await ch.fetch_message(msgs['revolt'][key])
                    await todelete.delete()
                    count += 1
                except:
                    continue
            return count

        if msg.source=='discord':
            count += await delete_discord(msg.copies)
        elif msg.source=='revolt':
            count += await delete_revolt(msg.copies)

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                count += await delete_discord(msg.external_copies['revolt'])
            elif platform=='revolt':
                count += await delete_revolt(msg.external_copies['revolt'])

        return count

    async def send(self, room: str, message: discord.Message or revolt.Message,
                   platform: str = 'discord', postthread: bool = False):
        source = 'discord'
        if type(message) is revolt.Message:
            source = 'revolt'

        user_hash = encrypt_string(f'{message.author.id}')[:3]
        if source == 'revolt':
            guild_hash = encrypt_string(f'{message.server.id}')[:3]
        else:
            guild_hash = encrypt_string(f'{message.guild.id}')[:3]

        if platform=='revolt':
            if not 'cogs.bridge_revolt' in list(self.bot.extensions.keys()):
                raise ValueError("Revolt Support not initialized.")
        elif platform=='guilded':
            if not 'cogs.bridge_guilded' in list(self.bot.extensions.keys()):
                raise ValueError("Guilded Support not initialized.")
        elif not platform=='discord':
            raise ValueError("Unsupported platform")

        guilds = self.bot.db['rooms'][room]
        if platform=='revolt':
            guilds = self.bot.db['rooms_revolt'][room]

        try:
            roomindex = list(self.bot.db['rooms'].keys()).index(room)
        except:
            raise ValueError('Invalid room')

        is_pr = roomindex == pr_room_index
        is_pr_ref = False
        pr_id = ""

        # PR ID generation
        if is_pr:
            pr_id = genid()

        # PR ID identification
        if roomindex == pr_ref_room_index and message.content.startswith('['):
            components = message.content.replace('[','',1).split(']')
            if len(components) >= 2:
                if len(components[1]) > 0 and len(components[0])==6:
                    if (components[0].lower()=='latest' or components[0].lower() == 'recent' or
                            components[0].lower() == 'newest'):
                        is_pr_ref = True
                        pr_id = self.prs[len(self.prs)-1]
                        message.content = message.content.replace(f'[{components[0]}]','',1)
                    else:
                        if components[0].lower() in list(self.prs.keys()):
                            is_pr_ref = True
                            pr_id = components[0].lower()
                            message.content = message.content.replace(f'[{components[0]}]', '', 1)

        # Global Emojis processing
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

        should_resend = (is_pr or emojified) and source=='discord'

        # Try to delete message if it should be resent as a webhook message
        if should_resend:
            try:
                await message.delete()
            except:
                raise SelfDeleteException('Could not delete parent message')

        message_ids = {}
        urls = {}
        limit_notified = False
        trimmed = ''

        # Threading
        thread_sameguild = []
        thread_urls = {}
        threads = []

        # Broadcast message
        for guild in list(guilds.keys()):
            if source=='revolt':
                sameguild = guild == str(message.server.id)
            else:
                sameguild = guild == str(message.guild.id)

            # Destination guild object
            destguild = None

            if platform == 'discord':
                destguild = self.bot.get_guild(int(guild))
                if not destguild:
                    continue
            elif platform == 'revolt':
                try:
                    destguild = self.bot.revolt_client.get_server(guild)
                except:
                    continue

            if sameguild:
                if not should_resend or not platform=='discord':
                    if platform=='discord':
                        urls.update({f'{message.guild.id}':f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'})
                    continue

            # Reply processing
            reply_msg = None
            components = None
            pr_actionrow = None

            try:
                if source=='revolt':
                    msgid = message.replies[0].id
                else:
                    msgid = message.reference.message_id
                reply_msg = await self.fetch_message(msgid)
            except:
                pass
            if platform=='discord':
                if is_pr or is_pr_ref:
                    button_style = discord.ButtonStyle.blurple
                    if source == 'revolt':
                        button_style = discord.ButtonStyle.red
                    if is_pr:
                        pr_actionrow = discord.ui.ActionRow(
                            discord.ui.Button(style=button_style, label=f'PR ID: {pr_id}',
                                              emoji='\U0001F4AC', disabled=True)
                        )
                    else:
                        try:
                            msg = await self.fetch_message(self.prs[pr_id])
                        except:
                            # Hide PR reference to avoid issues
                            is_pr_ref = False
                        else:
                            pr_actionrow = discord.ui.ActionRow(
                                discord.ui.Button(style=discord.ButtonStyle.url, label=f'Referencing PR {pr_id}',
                                                  emoji='\U0001F517', disabled=True,url=await msg.fetch_url(guild))
                            )
                if reply_msg:
                    if not trimmed:
                        try:
                            content = message.reference.cached_message.content
                        except:
                            if source=='revolt':
                                msg = await message.channel.fetch_message(message.replies[0].id)
                            else:
                                msg = await message.channel.fetch_message(message.reference.message_id).content
                            content = msg.content
                        clean_content = discord.utils.remove_markdown(content)

                        msg_components = clean_content.split('<@')
                        offset = 0
                        if clean_content.startswith('<@'):
                            offset = 1

                        while offset < len(msg_components):
                            try:
                                userid = int(msg_components[offset].split('>', 1)[0])
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

                    button_style = discord.ButtonStyle.blurple
                    author_text = '[unknown]'
                    try:
                        if source=='revolt':
                            button_style = discord.ButtonStyle.red
                        if reply_msg.source=='revolt':
                            user = self.bot.revolt_client.get_user(reply_msg.author_id)
                            if not user.display_name:
                                author_text = f'@{user.name}'
                            else:
                                author_text = f'@{user.display_name}'
                        else:
                            user = self.bot.get_user(int(reply_msg.author_id))
                            author_text = f'@{user.global_name}'
                        if f'{reply_msg.author_id}' in list(self.bot.db['nicknames'].keys()):
                            author_text = '@'+self.bot.db['nicknames'][f'{reply_msg.author_id}']
                    except:
                        pass

                    # Add PR buttons too.
                    if is_pr or is_pr_ref:
                        components = discord.ui.MessageComponents(
                            pr_actionrow,
                            discord.ui.ActionRow(
                                discord.ui.Button(style=discord.ButtonStyle.url,label='Replying to '+author_text,
                                                  url=await reply_msg.fetch_url(guild))
                            ),
                            discord.ui.ActionRow(
                                discord.ui.Button(style=button_style, label=trimmed, disabled=True)
                            )
                        )
                    else:
                        components = discord.ui.MessageComponents(
                            discord.ui.ActionRow(
                                discord.ui.Button(style=discord.ButtonStyle.url, label='Replying to '+author_text,
                                                  url=await reply_msg.fetch_url(guild))
                            ),
                            discord.ui.ActionRow(
                                discord.ui.Button(style=button_style, label=trimmed, disabled=True)
                            )
                        )

            # Attachment processing
            files = []
            size_total = 0

            async def to_file(source_file):
                if platform=='discord':
                    if source=='discord':
                        try:
                            return await source_file.to_file(use_cached=True, spoiler=source_file.is_spoiler())
                        except:
                            return await source_file.to_file(use_cached=True, spoiler=False)
                    elif source=='revolt':
                        filebytes = await source_file.read()
                        return discord.File(fp=BytesIO(filebytes), filename=source_file.filename)
                elif platform=='revolt':
                    if source=='discord':
                        f = await source_file.to_file(use_cached=True)
                        return revolt.File(f.fp.read(), filename=f.filename)
                    elif source=='revolt':
                        filebytes = await source_file.read()
                        return revolt.File(filebytes, filename=source_file.filename)

            for attachment in message.attachments:
                if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                        not 'image' in attachment.content_type) or attachment.size > 25000000:
                    continue
                size_total += attachment.size
                if size_total > 25000000:
                    if not limit_notified:
                        limit_notified = True
                        if source=='revolt':
                            await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                                       replies=[revolt.MessageReply(message)])
                        else:
                            await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',reference=message)
                    break
                files.append(await to_file(attachment))

            identifier = ' (' + user_hash + guild_hash + ')'

            # Username
            if source == 'revolt':
                if not message.author.display_name:
                    author = message.author.name
                else:
                    author = message.author.display_name
            else:
                author = message.author.global_name
            if f'{message.author.id}' in list(self.bot.db['nicknames'].keys()):
                author = self.bot.db['nicknames'][f'{message.author.id}']

            # Avatar
            try:
                if f'{message.author.id}' in self.bot.db['avatars']:
                    url = self.bot.db['avatars'][f'{message.author.id}']
                else:
                    url = message.author.avatar.url
            except:
                url = None

            # Add identifier
            msg_author = author
            if not sameguild:
                msg_author = author + identifier

            # Send message
            embeds = message.embeds
            if not message.author.bot:
                embeds = []

            if platform=='discord':
                try:
                    if str(message.guild.id) in str(self.bot.db['experiments']['threaded_bridge']) and not components:
                        synchook = None
                        try:
                            synchook = self.bot.webhook_cache_sync[f'{guild}'][f'{self.bot.db["rooms"][room][guild]}']
                        except:
                            hooks = await destguild.webhooks()
                            for hook in hooks:
                                if hook.id in self.bot.db['rooms'][room][guild]:
                                    synchook = await self.bot.loop.run_in_executor(None, lambda: discord.SyncWebhook.partial(hook.id, hook.token).fetch())
                                    try:
                                        self.bot.webhook_cache_sync[f'{guild}'].update(
                                            {f'{synchook.id}':synchook})
                                    except:
                                        self.bot.webhook_cache_sync.update({f'{guild}': {f'{synchook.id}': synchook}})
                                    break
                        if not synchook:
                            continue

                        def thread_msg():
                            sameguild_tr = sameguild
                            guild_id = synchook.guild_id
                            msg = synchook.send(avatar_url=url, username=msg_author,
                                                content=message.content, embeds=embeds,
                                                files=files, allowed_mentions=mentions, wait=True)

                            if sameguild_tr:
                                thread_sameguild.append(msg.id)
                            else:
                                message_ids.update({f'{guild_id}':[msg.channel.id, msg.id]})
                            thread_urls.update(
                                {f'{guild_id}': f'https://discord.com/channels/{guild_id}/{msg.channel.id}/{msg.id}'})

                        thread = threading.Thread(target=thread_msg)
                        thread.start()
                        threads.append(thread)
                    else:
                        raise ValueError()
                except:
                    traceback.print_exc()
                    webhook = None
                    try:
                        webhook = self.bot.webhook_cache[f'{guild}'][f'{self.bot.db["rooms"][room][guild]}']
                    except:
                        hooks = await destguild.webhooks()
                        for hook in hooks:
                            if f'{guild}' in list(self.bot.webhook_cache.keys()):
                                self.bot.webhook_cache[f'{guild}'].update({f'{hook.id}':hook})
                            else:
                                self.bot.webhook_cache.update({f'{guild}':{f'{hook.id}': hook}})
                            if hook.id in self.bot.db['rooms'][room][guild]:
                                webhook = hook
                                break
                    if not webhook:
                        continue
                    msg = await webhook.send(avatar_url=url, username=msg_author,embeds=embeds,
                                             content=message.content,files=files, allowed_mentions=mentions,
                                             components=components, wait=True)
                    if sameguild:
                        thread_sameguild = [msg.id]
                    else:
                        message_ids.update({f'{destguild.id}':[webhook.channel.id,msg.id]})
                    urls.update({f'{destguild.id}':f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'})

            elif platform=='revolt':
                try:
                    ch = destguild.get_channel(self.bot.db['rooms_revolt'][room][guild][0])
                except:
                    ch = await self.bot.revolt_client.fetch_channel(self.bot.db['rooms_revolt'][room][guild][0])

                # Processing replies for Revolt here for efficiency
                replies = []
                try:
                    if reply_msg:
                        if reply_msg.source=='revolt':
                            try:
                                msg = await ch.fetch_message(await reply_msg.fetch_id(destguild.id))
                                replies = [revolt.MessageReply(msg)]
                            except:
                                pass
                        else:
                            msg_ref = await reply_msg.fetch_external('revolt',destguild.id)
                            msg = await ch.fetch_message(msg_ref.id)
                            replies = [revolt.MessageReply(msg)]
                except:
                    pass

                rvtcolor = None
                if message.author.id in list(self.bot.db['colors'].keys()):
                    color = self.bot.db['colors'][message.author.id]
                    if color == 'inherit':
                        try:
                            color = message.author.roles[len(message.author.roles) - 1].colour.replace('#', '')
                            rgbtuple = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                            rvtcolor = f'rgb{rgbtuple}'
                        except:
                            pass
                    else:
                        try:
                            rgbtuple = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                            rvtcolor = f'rgb{rgbtuple}'
                        except:
                            pass
                try:
                    persona = revolt.Masquerade(name=msg_author, avatar=url, colour=rvtcolor)
                except:
                    persona = revolt.Masquerade(name=msg_author, avatar=None, colour=rvtcolor)

                msg = await ch.send(
                    content=message.content, embeds=message.embeds, attachments=files, replies=replies,
                    masquerade=persona
                )

                message_ids.update({destguild.id:[ch.id,msg.id]})

        # Update cache
        for thread in threads:
            await self.bot.loop.run_in_executor(None, lambda:thread.join())
        urls = urls | thread_urls
        message_ids = message_ids
        if len(thread_sameguild) > 0:
            parent_id = thread_sameguild[0]
        else:
            parent_id = message.id
        try:
            index = await self.indexof(message.id)
            msg_object = await self.fetch_message(message.id)
            if msg_object.source==platform:
                msg_object.copies = msg_object.copies | message_ids
            else:
                try:
                    msg_object.external_copies[platform] = msg_object.external_copies[platform] | message_ids
                except:
                    msg_object.external_copies.update({platform:message_ids})
            msg_object.urls = msg_object.urls | urls
            self.bridged[index] = msg_object
        except:
            copies = {}
            external_copies = {}
            if source==platform:
                copies = message_ids
            else:
                external_copies = {platform:message_ids}
            if source=='revolt':
                server_id = message.server.id
            else:
                server_id = message.guild.id
            self.bridged.append(UnifierMessage(
                author_id=message.author.id,
                guild_id=server_id,
                channel_id=message.channel.id,
                original=parent_id,
                copies=copies,
                external_copies=external_copies,
                urls=urls,
                source=source,
                webhook=should_resend,
                room=room
            ))

class Bridge(commands.Cog, name=':link: Bridge'):
    """Bridge is the heart of Unifier, it's the extension that handles the bridging and everything chat related.

    Developed by Green and ItsAsheer"""
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self.bot, 'bridged'):
            self.bot.bridged = []
        if not hasattr(self.bot, 'bridged_external'):
            self.bot.bridged_external = {}
        if not hasattr(self.bot, 'bridged_obe'):
            # OBE = Owned By External
            # Message wasn't sent from Discord.
            self.bot.bridged_obe = {}
        if not hasattr(self.bot, 'bridged_urls'):
            self.bot.bridged_urls = {}
        if not hasattr(self.bot, 'bridged_urls_external'):
            self.bot.bridged_urls_external = {}
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
        msgs = []
        if hasattr(self.bot, 'bridge'):
            msgs = self.bot.bridge.bridged
        del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot)
        self.bot.bridge.bridged = msgs

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
                                    try:
                                        msg_url = self.bot.bridged_urls_external[f'{msg_resp.id}']
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

        files = []
        cogs = list(self.bot.extensions)
        if 'revolt' in externals and 'cogs.bridge_revolt' in cogs:
            ids = {}

            try:
                if f'{ctx.author.id}' in self.bot.db['avatars']:
                    url = self.bot.db['avatars'][f'{ctx.author.id}']
                else:
                    url = ctx.author.avatar.url
            except:
                url = None

            for guild in self.bot.db['rooms_revolt'][roomname]:
                try:
                    guild = self.bot.revolt_client.get_server(guild)
                except:
                    continue
                try:
                    if str(ctx.author.id) in str(self.bot.db["blocked"][f'{guild.id}']) or str(
                            ctx.server.id) in str(
                            self.bot.db["blocked"][f'{guild.id}']):
                        continue
                except:
                    pass
                ch = guild.get_channel(self.bot.db['rooms_revolt'][roomname][guild.id][0])
                identifier = ' (' + user_hash + guild_hash + ')'
                author = ctx.author.global_name
                if f'{ctx.author.id}' in list(self.bot.db['nicknames'].keys()):
                    author = self.bot.db['nicknames'][f'{ctx.author.id}']
                author_rvt = author
                rvtcolor = None
                if len(author) > 23:
                    author_rvt = author_rvt[:-(len(author) - 23)]
                if f'{ctx.author.id}' in list(self.bot.db['colors'].keys()):
                    color = self.bot.db['colors'][f'{ctx.author.id}']
                    if color == 'inherit':
                        rvtcolor = f'rgb({ctx.author.color.r},{ctx.author.color.g},{ctx.author.color.b})'
                    else:
                        rgbtuple = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                        rvtcolor = f'rgb{rgbtuple}'
                try:
                    if f'{ctx.author.id}' in list(self.bot.db['avatars'].keys()):
                        persona = revolt.Masquerade(name=author_rvt + identifier, avatar=self.bot.db['avatars'][f'{ctx.author.id}'], colour=rvtcolor)
                    else:
                        persona = revolt.Masquerade(name=author_rvt + identifier, avatar=url,
                                                    colour=rvtcolor)
                except:
                    persona = revolt.Masquerade(name=author_rvt + identifier, avatar=None, colour=rvtcolor)
                msg_data = None
                origin_id = None
                try:
                    try:
                        msg_data = self.bot.bridged_external[f'{msg_resp.id}']['revolt']
                    except:
                        for key in self.bot.bridged_obe:
                            if f'{msg_resp.id}' in f'{self.bot.bridged_obe[key]}':
                                msg_data = self.bot.bridged_obe[f'{key}']
                                origin_id = key
                                break
                        if not msg_data:
                            raise ValueError()
                except:
                    for key in self.bot.bridged_external:
                        if f'{msg_resp.id}' in str(self.bot.bridged_external[key]['revolt']):
                            msg_data = self.bot.bridged_external[f'{key}']['revolt']
                            break
                if not msg_data:
                    replies = []
                else:
                    try:
                        msg = await ch.fetch_message(msg_data[guild.id])
                    except:
                        msg = await ch.fetch_message(origin_id)
                    replies = [revolt.MessageReply(message=msg)]
                msg = await ch.send(attachments=[revolt.File("cached/"+filename)], replies=replies, masquerade=persona)
                ids.update({guild.id: msg.id})

            self.bot.bridged_external.update({f'{sameguild_id}': {'revolt': ids}})

        for thread in threads:
            await self.bot.loop.run_in_executor(None, lambda: thread.join())
        self.bot.bridged.update({f'{sameguild_id}': hookmsg_ids})
        self.bot.bridged_urls.update({f'{sameguild_id}': msg_urls})
        try:
            os.remove("cached/"+filename)
        except:
            traceback.print_exc()

    @commands.context_command(name='Reaction image')
    async def reaction(self, ctx, message: discord.Message):
        return await ctx.send("Reaction images are currently disabled.",ephemeral=True)
        # hooks = await ctx.guild.webhooks()
        # webhook = None
        # origin_room = 0
        # found = False
        # for hook in hooks:
        #     if hook.channel_id == ctx.channel.id and hook.user.id == self.bot.user.id:
        #         webhook = hook
        #         index = 0
        #         for key in self.bot.db['rooms']:
        #             data = self.bot.db['rooms'][key]
        #             if f'{ctx.guild.id}' in list(data.keys()):
        #                 hook_ids = data[f'{ctx.guild.id}']
        #             else:
        #                 hook_ids = []
        #             if webhook.id in hook_ids:
        #                 origin_room = index
        #                 found = True
        #                 if key in self.bot.db['locked'] and not ctx.author.id in self.bot.admins:
        #                     return
        #                 break
        #             index += 1
        #         break
        #
        # if not found:
        #     return await ctx.send('I couldn\'t identify the UniChat room of this channel.',ephemeral=True)
        # try:
        #     roomname = list(self.bot.db['rooms'].keys())[origin_room]
        #     if roomname in self.bot.db['locked'] and not ctx.author.id in self.bot.admins:
        #         return await ctx.send('This room is locked!',ephemeral=True)
        # except:
        #     return await ctx.send('I couldn\'t identify the UniChat room of this channel.',ephemeral=True)
        # if not ctx.channel.permissions_for(ctx.author).send_messages:
        #     return await ctx.send('You can\'t type in here!',ephemeral=True)
        # if not webhook or not f'{webhook.id}' in f'{self.bot.db["rooms"]}':
        #     return await ctx.send('This isn\'t a UniChat room!', ephemeral=True)
        # components = discord.ui.MessageComponents(
        #     discord.ui.ActionRow(
        #         discord.ui.Button(style=discord.ButtonStyle.blurple,label='Clueless',custom_id='clueless'),
        #         discord.ui.Button(style=discord.ButtonStyle.blurple, label='THINK, MARK, THINK!', custom_id='think'),
        #     ),
        #     discord.ui.ActionRow(
        #         discord.ui.Button(style=discord.ButtonStyle.green, label='THICC, MARK, THICC!', custom_id='thicc'),
        #     )
        # )
        # msg = await ctx.send('Choose a reaction image to generate!\n\n**Blue**: Static images\n**Green**: GIFs', ephemeral=True, components=components)
        #
        # def check(interaction):
        #     return interaction.user.id == ctx.author.id and interaction.message.id == msg.id
        #
        # try:
        #     interaction = await self.bot.wait_for('component_interaction', check=check, timeout=60)
        # except:
        #     try:
        #         return await msg.edit(content='Timed out.', components=None)
        #     except:
        #         return
        #
        # await interaction.response.edit_message(content='Generating...', components=None)
        # msgid = msg.id
        # filename = ''
        # try:
        #     if interaction.custom_id=='clueless':
        #         link1 = message.author.avatar.url
        #         filename = await self.bot.loop.run_in_executor(None, lambda: self.clueless_gen(link1, msgid))
        #     elif interaction.custom_id=='think':
        #         link1 = ctx.author.avatar.url
        #         link2 = message.author.avatar.url
        #         filename = await self.bot.loop.run_in_executor(None, lambda: self.think(link1, link2, message.author.global_name, msgid))
        #     elif interaction.custom_id=='thicc':
        #         link1 = ctx.author.avatar.url
        #         link2 = message.author.avatar.url
        #         filename = await self.bot.loop.run_in_executor(None, lambda: self.omniman(link1, link2, msgid))
        # except:
        #     await msg.edit('**oh no**\nAn unexpected error occurred generating the image. Please contact the developers.')
        #     raise
        # try:
        #     await self.image_forward(ctx,message,filename)
        # except:
        #     await msg.edit('**oh no**\nAn unexpected error occurred sending the image. Please contact the developers.')
        #     raise
        # await msg.edit('Sent reaction image!')

    @commands.command(aliases=['colour'])
    async def color(self,ctx,*,color=''):
        if color=='':
            try:
                current_color = self.bot.db['colors'][f'{ctx.author.id}']
                if current_color=='':
                    current_color = 'Default'
                    embed_color = self.bot.colors.unifier
                elif current_color=='inherit':
                    current_color = 'Inherit from role'
                    embed_color = ctx.author.color.value
                else:
                    embed_color = ast.literal_eval('0x'+current_color)
            except:
                current_color = 'Default'
                embed_color = self.bot.colors.unifier
            embed = discord.Embed(title='Your Revolt color',description=current_color,color=embed_color)
            await ctx.send(embed=embed)
        elif color=='inherit':
            self.bot.db['colors'].update({f'{ctx.author.id}':'inherit'})
            self.bot.db.save_data()
            await ctx.send('Your Revolt messages will now inherit your Discord role color.')
        else:
            try:
                tuple(int(color.replace('#','',1)[i:i + 2], 16) for i in (0, 2, 4))
            except:
                return await ctx.send('Invalid hex code!')
            self.bot.db['colors'].update({f'{ctx.author.id}':color})
            self.bot.db.save_data()
            await ctx.send('Your Revolt messages will now inherit the custom color.')


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
                        f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id}, Discord)\nOriginal ID {origin_msg_id}')
                except:
                    await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})\nCould not find origin message ID')
                    raise
            else:
                await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})')
        else:
            for guild in self.bot.revolt_client.servers:
                hashed = encrypt_string(f'{guild.id}')
                guildhash = identifier[3:]
                if hashed.startswith(guildhash):
                    for member in guild.members:
                        hashed = encrypt_string(f'{member.id}')
                        userhash = identifier[:-3]
                        if hashed.startswith(userhash):
                            return await ctx.send(f'{member.name} ({member.id}) via {guild.name} ({guild.id}, Revolt)')

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
    async def delete(self, ctx, *, msg_id=None):
        """Deletes all bridged messages. Does not delete the original."""
        gbans = self.bot.db['banned']
        ct = time.time()
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
        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            return await ctx.send('Your account or your guild is currently **global restricted**.')

        try:
            msg_id = ctx.message.reference.message_id
        except:
            if not msg_id:
                return await ctx.send('No message!')

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await ctx.send('Could not find message in cache!')

        if not ctx.author.id==msg.author_id and not ctx.author.id in self.bot.moderators:
            return await ctx.send('You didn\'t send this message!')

        try:
            await self.bot.bridge.delete_parent(msg_id)
            if not msg.webhook:
                return await ctx.send('Deleted message (parent deleted, copies will follow)')
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(msg_id)
                return await ctx.send(f'Deleted message ({deleted} copies deleted)')
            except:
                traceback.print_exc()
                await ctx.send('Something went wrong.')

    @commands.context_command(name='Delete message')
    async def delete_ctx(self, ctx, msg: discord.Message):
        gbans = self.bot.db['banned']
        ct = time.time()
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
        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            return await ctx.send('Your account or your guild is currently **global restricted**.', ephemeral=True)
        msg_id = msg.id

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await ctx.send('Could not find message in cache!',ephemeral=True)

        if not ctx.author.id == msg.author_id and not ctx.author.id in self.bot.moderators:
            return await ctx.send('You didn\'t send this message!',ephemeral=True)

        msgconf = await ctx.send('Deleting...', ephemeral=True)

        try:
            await self.bot.bridge.delete_parent(msg_id)
            if not msg.webhook:
                return await msgconf.edit('Deleted message (parent deleted, copies will follow)',ephemeral=True)
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(msg_id)
                await msgconf.edit(f'Deleted message ({deleted} copies deleted)',ephemeral=True)
            except:
                traceback.print_exc()
                await msgconf.edit('Something went wrong.')

    @commands.context_command(name='Report message')
    async def report(self, ctx, msg: discord.Message):
        gbans = self.bot.db['banned']
        ct = time.time()
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
        if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
            return await ctx.send('You or your guild is currently **global restricted**.', ephemeral=True)

        try:
            msgdata = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await ctx.send('Could not find message in cache!')

        roomname = msgdata.room
        userid = msgdata.author_id
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
        self.bot.reports.update({f'{ctx.author.id}_{userid}_{msg.id}': [cat, cat2, content, roomname, msgdata.id]})
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
        msgid = report[4]
        msgdata = await self.bot.bridge.fetch_message(msgid)
        userid = int(interaction.custom_id.split('_')[0])
        if len(content) > 2048:
            content = content[:-(len(content) - 2048)]
        embed = discord.Embed(title='Message report - content is as follows', description=content, color=0xffbb00)
        embed.add_field(name="Reason", value=f'{cat} => {cat2}', inline=False)
        embed.add_field(name='Context', value=context, inline=False)
        embed.add_field(name="Sender ID", value=str(msgdata.author_id), inline=False)
        embed.add_field(name="Message room", value=roomname, inline=False)
        embed.add_field(name="Message ID", value=str(msgid), inline=False)
        embed.add_field(name="Reporter ID", value=str(interaction.user.id), inline=False)
        try:
            embed.set_footer(text=f'Submitted by {author} - please do not disclose actions taken against the user.', icon_url=interaction.user.avatar.url)
        except:
            embed.set_footer(text=f'Submitted by {author} - please do not disclose actions taken against the user.')
        try:
            user = self.bot.get_user(userid)
            if not user:
                user = self.bot.revolt_client.get_user(userid)
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
            discord.ui.Button(style=discord.ButtonStyle.red, label='Delete message', custom_id=f'rpdelete_{msgid}',
                              disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.green, label='Mark as reviewed',
                              custom_id=f'rpreview_{msgid}',
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

            try:
                msg: UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
            except:
                return await interaction.response.send_message('Could not find message in cache!',ephemeral=True)

            if not interaction.user.id in self.bot.moderators:
                return await interaction.response.send_message('go away',ephemeral=True)

            msg_orig = await interaction.response.send_message("Deleting...",ephemeral=True)

            try:
                await self.bot.bridge.delete_parent(msg_id)
                if not msg.webhook:
                    await interaction.message.edit(components=components)
                    return await msg_orig.edit('Deleted message (parent deleted, copies will follow)')
            except:
                try:
                    deleted = await self.bot.bridge.delete_copies(msg_id)
                    await interaction.message.edit(components=components)
                    return await msg_orig.edit(f'Deleted message ({deleted} copies deleted)')
                except:
                    traceback.print_exc()
                    await msg_orig.edit(content=f'Something went wrong.')
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

    @commands.command(hidden=True)
    async def viewmsg(self,ctx):
        if not ctx.author.id == 356456393491873795:
            return
        try:
            msgid = ctx.message.reference.message_id
        except:
            return await ctx.send('No message detected')
        msg: UnifierMessage = await self.bot.bridge.fetch_message(msgid)
        text = f'Author: {msg.author_id}\nGuild: {msg.guild_id}\nSource: {msg.source}\nParent is webhook: {msg.webhook}\n\nCopies (samesource):'
        for key in msg.copies:
            info = msg.copies[key]
            text = f'{text}\n{key}: {info[1]}, sent in {info[0]}'
        for platform in msg.external_copies:
            text = f'{text}\n\nCopies ({platform}):'
            for key in msg.external_copies[platform]:
                info = msg.external_copies[platform][key]
                text = f'{text}\n{key}: {info[1]}, sent in {info[0]}'
        text = f'{text}\n\nURLs (discord):'
        for key in msg.urls:
            text = f'{text}\n{key}: [link](<{msg.urls[key]}>)'
        await ctx.send(text)

    @commands.command(hidden=True)
    async def initbridge(self, ctx, *, args=''):
        if not ctx.author.id == 356456393491873795:
            return
        msgs = None
        if 'preserve' in args:
            msgs = self.bot.bridge.bridged
        del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot)
        if 'preserve' in args and msgs:
            self.bot.bridge.bridged = msgs
        await ctx.send('Bridge initialized')

    @commands.Cog.listener()
    async def on_message(self, message):
        author_rp = message.author
        content_rp = message.content
        if not message.webhook_id == None:
            # webhook msg
            return

        if message.guild == None:
            return

        if len(message.content)==0 and len(message.embeds)==0 and len(message.attachments)==0:
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

        await self.bot.bridge.send(room=roomname,message=message,platform='discord')

        if 'cogs.bridge_revolt' in self.bot.extensions:
            await self.bot.bridge.send(room=roomname, message=message, platform='revolt')

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

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not str(msg.id)==str(message.id):
                raise ValueError()
        except:
            return

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
                        msgid = await msg.fetch_id(key)
                        await webhook.edit_message(msgid,content=message.content, allowed_mentions=mentions)
                    except:
                        # likely deleted msg
                        pass

        if 'revolt' in externals and 'cogs.bridge_revolt' in list(self.bot.extensions):
            data2 = msg.external_copies['revolt']

            components = message.content.split('<@')
            offset = 0
            if message.content.startswith('<@'):
                offset = 1

            while offset < len(components):
                if len(components) == 1 and offset == 0:
                    break
                try:
                    userid = int(components[offset].split('>', 1)[0])
                except:
                    userid = components[offset].split('>', 1)[0]
                user = self.bot.get_user(userid)
                if user:
                    message.content = message.content.replace(f'<@{userid}>',
                                                              f'@{user.global_name or user.name}').replace(
                        f'<@!{userid}>', f'@{user.global_name}')
                offset += 1
            revoltfriendly = message.content

            for key in data2:
                try:
                    try:
                        guild = self.bot.revolt_client.get_server(key)
                    except:
                        continue
                    try:
                        if str(message.author.id) in str(self.bot.db["blocked"][f'{guild.id}']) or str(
                                message.server.id) in str(
                                self.bot.db["blocked"][f'{guild.id}']):
                            continue
                    except:
                        pass
                    ch = guild.get_channel(self.bot.db['rooms_revolt'][roomname][key][0])
                    msg_revolt = await ch.fetch_message(data2[key])
                    await msg_revolt.edit(content=revoltfriendly)
                except:
                    traceback.print_exc()
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

        roomname = list(self.bot.db['rooms'].keys())[origin_room]

        try:
            guild = self.bot.get_guild(home_guild)
            ch = guild.get_channel(logs_channel)

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
        except:
            pass

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not msg.id == message.id:
                raise ValueError()
        except:
            return

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
                        if msg.source=='discord':
                            msgid = await msg.fetch_id(key)
                        else:
                            msgid = await msg.fetch_external('discord',key)
                        await webhook.delete_message(msgid)
                    except:
                        # likely deleted msg
                        pass

        if 'revolt' in externals and 'cogs.bridge_revolt' in list(self.bot.extensions):
            try:
                data = msg.external_copies['revolt']
            except:
                pass
            else:
                for key in data:
                    try:
                        try:
                            guild = self.bot.revolt_client.get_server(key)
                        except:
                            continue
                        try:
                            if str(message.author.id) in str(self.bot.db["blocked"][f'{guild.id}']) or str(
                                    message.server.id) in str(
                                    self.bot.db["blocked"][f'{guild.id}']):
                                continue
                        except:
                            pass
                        ch = guild.get_channel(self.bot.db['rooms_revolt'][roomname][key][0])
                        msg_revolt = await ch.fetch_message(data[key])
                        await msg_revolt.delete()
                    except:
                        pass

def setup(bot):
    bot.add_cog(Bridge(bot))
