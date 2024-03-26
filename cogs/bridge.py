"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

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
import asyncio
import guilded
import revolt
from discord.ext import commands
import traceback
import time
from datetime import datetime
import random
import string
import copy
import json
import compress_json
import re
import ast
from io import BytesIO
from tld import get_tld
from utils import rapidphish

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
compress_cache = data["compress_cache"]

mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)

multisend_logs = []

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

def log(type='???',status='ok',content='None'):
    from time import gmtime, strftime
    time1 = strftime("%Y.%m.%d %H:%M:%S", gmtime())
    if status=='ok':
        status = ' OK  '
    elif status=='error':
        status = 'ERROR'
    elif status=='warn':
        status = 'WARN '
    elif status=='info':
        status = 'INFO '
    else:
        raise ValueError('Invalid status type provided')
    print(f'[{type} | {time1} | {status}] {content}')

class ExternalReference:
    def __init__(self, guild_id, channel_id, message_id):
        self.guild = guild_id
        self.channel = channel_id
        self.id = message_id

class SelfDeleteException(Exception):
    pass

class UnifierMessage:
    def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room,
                 external_urls=None, webhook=False, prehook=None, reply=False):
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
        self.prehook = prehook
        self.reply = reply

    def to_dict(self):
        return self.__dict__

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
        return ExternalReference(guild_id, self.external_copies[platform][str(guild_id)][0], self.external_copies[platform][str(guild_id)][1])

class UnifierBridge:

    def __init__(self, bot, webhook_cache=None):
        self.bot = bot
        self.bridged = []
        self.prs = {}
        self.webhook_cache = webhook_cache or {}
        self.restored = False

    async def backup(self,filename='bridge.json',limit=10000):
        data = {'messages':{},'posts':{}}
        og_limit = limit

        if limit<=0:
            raise ValueError('limit must be a positive integer')
        if len(self.bridged) < limit:
            limit = len(self.bridged)
        for index in range(len(self.bridged)):
            if index==limit:
                break
            msg = self.bridged[limit-index-1]
            data['messages'].update({f'{limit-index-1}':msg.to_dict()})

        pr_ids = list(self.prs.keys())
        if len(pr_ids) < og_limit:
            limit = len(pr_ids)
        for index in range(len(pr_ids)):
            if index==limit:
                break
            code = self.prs[pr_ids[limit - index - 1]]
            data['posts'].update({pr_ids[limit - index - 1]: code})

        if compress_cache:
            compress_json.dump(data,filename+'.lzma')
        else:
            with open(filename, "w+") as file:
                json.dump(data, file)
        del data
        return

    async def restore(self,filename='bridge.json'):
        if self.restored:
            raise RuntimeError('Already restored from backup')
        if compress_cache:
            data = compress_json.load(filename+'.lzma')
        else:
            with open(filename, "r") as file:
                data = json.load(file)

        for x in range(len(data['messages'])):
            msg = UnifierMessage(
                author_id=data['messages'][f'{x}']['author_id'],
                guild_id=data['messages'][f'{x}']['guild_id'],
                channel_id=data['messages'][f'{x}']['channel_id'],
                original=data['messages'][f'{x}']['id'],
                copies=data['messages'][f'{x}']['copies'],
                external_copies=data['messages'][f'{x}']['external_copies'],
                urls=data['messages'][f'{x}']['urls'],
                source=data['messages'][f'{x}']['source'],
                room=data['messages'][f'{x}']['room'],
                external_urls=data['messages'][f'{x}']['external_urls'],
                webhook=data['messages'][f'{x}']['webhook'],
                prehook=data['messages'][f'{x}']['prehook']
            )
            self.bridged.append(msg)
        
        self.prs = data['posts']
        del data
        self.restored = True
        return

    async def fetch_message(self,message_id,prehook=False,not_prehook=False):
        if prehook and not_prehook:
            raise ValueError('Conflicting arguments')
        for message in self.bridged:
            if (str(message.id)==str(message_id) or str(message_id) in str(message.copies) or
                    str(message_id) in str(message.external_copies) or str(message.prehook)==str(message_id)):
                if prehook and str(message.prehook)==str(message_id) and not str(message.id) == str(message_id):
                    return message
                elif not_prehook and not str(message.prehook) == str(message_id):
                    return message
                elif not prehook:
                    return message
        raise ValueError("No message found")

    async def indexof(self,message_id,prehook=False,not_prehook=False):
        if prehook and not_prehook:
            raise ValueError('Conflicting arguments')
        index = 0
        for message in self.bridged:
            if (str(message.id)==str(message_id) or str(message_id) in str(message.copies) or
                    str(message_id) in str(message.external_copies) or str(message.prehook)==str(message_id)):
                if prehook and str(message.prehook) == str(message_id) and not str(message.id) == str(message_id):
                    return index
                elif not_prehook and not str(message.prehook) == str(message_id):
                    return index
                elif not prehook:
                    return index
            index += 1
        raise ValueError("No message found")

    async def merge_prehook(self,message_id):
        index = await self.indexof(message_id,prehook=True)
        index_tomerge = await self.indexof(message_id, not_prehook=True)
        msg_tomerge: UnifierMessage = await self.fetch_message(message_id,not_prehook=True)
        self.bridged[index]['copies'] = self.bridged[index]['copies'] | msg_tomerge.copies
        self.bridged[index]['external_copies'] = self.bridged[index]['external_copies'] | msg_tomerge.external_copies
        self.bridged[index]['urls'] = self.bridged[index]['urls'] | msg_tomerge.urls
        self.bridged.pop(index_tomerge)

    async def delete_parent(self, message):
        msg: UnifierMessage = await self.fetch_message(message)
        if msg.source=='discord':
            guild = self.bot.get_guild(int(msg.guild_id))
            ch = guild.get_channel(int(msg.channel_id))
            todelete = await ch.fetch_message(int(msg.id))
            await todelete.delete()
        elif msg.source=='guilded':
            guild = self.bot.guilded_client.get_server(msg.guild_id)
            ch = guild.get_channel(msg.channel_id)
            todelete = await ch.fetch_message(msg.id)
            await todelete.delete()
        elif msg.source=='revolt':
            ch = await self.bot.revolt_client.fetch_channel(msg.channel_id)
            todelete = await ch.fetch_message(msg.id)
            await todelete.delete()

    async def delete_copies(self, message):
        msg: UnifierMessage = await self.fetch_message(message)
        count = 0

        async def delete_discord(msgs):
            count = 0
            for key in list(self.bot.db['rooms'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.bot.get_guild(int(key))
                try:
                    hooks = await guild.webhooks()
                except:
                    continue
                webhook = None

                # Fetch webhook
                for hook in hooks:
                    if int(self.bot.db['rooms'][msg.room][key][0])==hook.id:
                        webhook = hook
                        break

                if not webhook:
                    # No webhook found
                    continue

                try:
                    await webhook.delete_message(int(msgs[key][1]))
                    count += 1
                except:
                    traceback.print_exc()
                    pass
            return count

        async def delete_guilded(msgs):
            if not 'cogs.bridge_guilded' in list(self.bot.extensions.keys()):
                return
            count = 0
            for key in list(self.bot.db['rooms_guilded'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.bot.guilded_client.get_server(key)

                # Fetch webhook
                try:
                    webhook = await guild.fetch_webhook(self.bot.db['rooms_guilded'][msg.room][key][0])
                except:
                    continue

                try:
                    await webhook.delete_message(msgs[key][1])
                    count += 1
                except:
                    traceback.print_exc()
                    pass
            return count

        async def delete_revolt(msgs):
            if not 'cogs.bridge_revolt' in list(self.bot.extensions.keys()):
                return
            count = 0
            for key in list(self.bot.db['rooms_revolt'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                try:
                    ch = await self.bot.revolt_client.fetch_channel(msgs[key][0])
                    todelete = await ch.fetch_message(msgs[key][1])
                    await todelete.delete()
                    count += 1
                except:
                    traceback.print_exc()
                    continue
            return count

        if msg.source=='discord':
            count += await delete_discord(msg.copies)
        elif msg.source=='revolt':
            count += await delete_revolt(msg.copies)
        elif msg.source=='guilded':
            count += await delete_guilded(msg.copies)

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                count += await delete_discord(msg.external_copies['discord'])
            elif platform=='revolt':
                count += await delete_revolt(msg.external_copies['revolt'])
            elif platform=='guilded':
                count += await delete_guilded(msg.external_copies['guilded'])

        return count

    async def edit(self, message, content):
        msg: UnifierMessage = await self.fetch_message(message)

        async def make_friendly(text):
            components = text.split('<@')
            offset = 0
            if text.startswith('<@'):
                offset = 1

            while offset < len(components):
                if len(components) == 1 and offset == 0:
                    break
                try:
                    userid = int(components[offset].split('>', 1)[0])
                except:
                    userid = components[offset].split('>', 1)[0]
                try:
                    if msg.source=='revolt':
                        user = self.bot.revolt_client.get_user(userid)
                    elif msg.source=='guilded':
                        user = self.bot.guilded_client.get_user(userid)
                    else:
                        user = self.bot.get_user(userid)
                    if not user:
                        raise ValueError()
                except:
                    offset += 1
                    continue
                text = text.replace(f'<@{userid}>',f'@{user.display_name or user.name}').replace(
                    f'<@!{userid}>', f'@{user.display_name or user.name}')
                offset += 1
            return text

        async def edit_discord(msgs,friendly=False):
            if friendly:
                text = await make_friendly(content)
            else:
                text = content

            for key in list(self.bot.db['rooms'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.bot.get_guild(int(key))
                try:
                    hooks = await guild.webhooks()
                except:
                    continue
                webhook = None

                # Fetch webhook
                for hook in hooks:
                    if int(self.bot.db['rooms'][msg.room][key][0])==hook.id:
                        webhook = hook
                        break

                if not webhook:
                    # No webhook found
                    continue

                try:
                    await webhook.edit_message(int(msgs[key][1]),content=text,allowed_mentions=mentions)
                except:
                    traceback.print_exc()
                    pass

        async def edit_revolt(msgs,friendly=False):
            if not 'cogs.bridge_revolt' in list(self.bot.extensions.keys()):
                return
            if friendly:
                text = await make_friendly(content)
            else:
                text = content

            for key in list(self.bot.db['rooms_revolt'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                try:
                    ch = await self.bot.revolt_client.fetch_channel(msgs[key][0])
                    toedit = await ch.fetch_message(msgs[key][1])
                    await toedit.edit(content=text)
                except:
                    traceback.print_exc()
                    continue

        async def edit_guilded(msgs,friendly=False):
            if friendly:
                text = await make_friendly(content)
            else:
                text = content

            for key in list(self.bot.db['rooms_guilded'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.bot.guilded_client.get_server(key)
                try:
                    hooks = await guild.webhooks()
                except:
                    continue
                webhook = None

                # Fetch webhook
                for hook in hooks:
                    if self.bot.db['rooms_guilded'][msg.room][key][0]==hook.id:
                        webhook = hook
                        break

                if not webhook:
                    # No webhook found
                    continue

                try:
                    toedit = await webhook.fetch_message(msgs[key][1])
                    if msg.reply:
                        text = toedit.content.split('\n',1)[0]+'\n'+text
                    await toedit.edit(content=text)
                except:
                    traceback.print_exc()
                    pass

        if msg.source=='discord':
            await edit_discord(msg.copies)
        elif msg.source=='revolt':
            await edit_revolt(msg.copies)

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                await edit_discord(msg.external_copies['discord'],friendly=True)
            elif platform=='revolt':
                await edit_revolt(msg.external_copies['revolt'],friendly=True)

    async def send(self, room: str, message: discord.Message or revolt.Message,
                   platform: str = 'discord', system: bool = False, multisend_debug=False):
        source = 'discord'
        pt = time.time()
        extlist = list(self.bot.extensions)
        if type(message) is revolt.Message:
            if not 'cogs.bridge_revolt' in extlist:
                raise RuntimeError('Revolt Support not initialized')
            source = 'revolt'
        if type(message) is guilded.ChatMessage:
            if not 'cogs.bridge_guilded' in extlist:
                raise RuntimeError('Guilded Support not initialized')
            source = 'guilded'

        if platform=='revolt':
            if not 'cogs.bridge_revolt' in list(self.bot.extensions.keys()):
                return
        elif platform=='guilded':
            if not 'cogs.bridge_guilded' in list(self.bot.extensions.keys()):
                return
        elif not platform=='discord':
            raise ValueError("Unsupported platform")

        guilds = self.bot.db['rooms'][room]
        if platform=='revolt':
            guilds = self.bot.db['rooms_revolt'][room]
        elif platform=='guilded':
            guilds = self.bot.db['rooms_guilded'][room]

        try:
            roomindex = list(self.bot.db['rooms'].keys()).index(room)
        except:
            raise ValueError('Invalid room')

        is_pr = roomindex == pr_room_index and allow_prs
        is_pr_ref = False
        pr_id = ""

        # PR ID generation
        if is_pr:
            if source==platform:
                pr_id = genid()
            else:
                for pr in self.prs:
                    msgid = self.prs[pr]
                    if str(msgid)==str(message.id):
                        pr_id = pr
                        break
                if len(pr_id)==0:
                    is_pr = False

        # PR ID identification
        if roomindex == pr_ref_room_index and message.content.startswith('[') and source==platform=='discord' and allow_prs:
            pr_id = None
            components = message.content.replace('[','',1).split(']')
            if len(components) >= 2:
                if len(components[1]) > 0 and len(components[0])==6:
                    if (components[0].lower()=='latest' or components[0].lower() == 'recent' or
                            components[0].lower() == 'newest'):
                        is_pr_ref = True
                        if len(self.prs) > 0:
                            pr_id = list(self.prs.keys())[len(self.prs)-1]
                            message.content = message.content.replace(f'[{components[0]}]','',1)
                        else:
                            is_pr_ref = False
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

        should_resend = (is_pr or is_pr_ref or emojified) and source==platform=='discord'

        # Try to delete message if it should be resent as a webhook message
        if should_resend:
            try:
                await message.delete()
            except:
                if emojified or is_pr_ref:
                    await message.channel.send('Parent message could not be deleted. I may be missing the `Manage Messages` permission.')
                    raise SelfDeleteException('Could not delete parent message')
                elif is_pr:
                    await message.channel.send(f'Post ID assigned: `{pr_id}`',reference=message)
                should_resend = False
        elif is_pr and source==platform:
            if source == 'revolt':
                await message.channel.send(f'Post ID assigned: `{pr_id}`', replies=[revolt.MessageReply(message)])
            elif source == 'guilded':
                await message.channel.send(f'Post ID assigned: `{pr_id}`', reply_to=[message])

        message_ids = {}
        urls = {}
        limit_notified = False
        trimmed = ''
        replying = False

        # Threading
        thread_sameguild = []
        thread_urls = {}
        threads = []
        tb_v2 = False

        # Broadcast message
        for guild in list(guilds.keys()):
            if source=='revolt' or source=='guilded':
                sameguild = guild == str(message.server.id)
            else:
                sameguild = guild == str(message.guild.id)

            try:
                bans = self.bot.db['blocked'][str(guild)]
                if message.author.id in bans and not sameguild:
                    continue
            except:
                pass

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
            elif platform == 'guilded':
                try:
                    destguild = self.bot.guilded_client.get_server(guild)
                except:
                    continue

            if sameguild and not system:
                if not should_resend or not platform=='discord':
                    if platform=='discord':
                        urls.update({f'{message.guild.id}':f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'})
                    elif platform=='guilded':
                        urls.update({f'{message.server.id}': message.share_url})
                    continue

            # Reply processing
            reply_msg = None
            components = None
            pr_actionrow = None

            try:
                if source=='revolt':
                    msgid = message.replies[0].id
                elif source=='guilded':
                    msgid = message.replied_to[0].id
                else:
                    msgid = message.reference.message_id
                reply_msg = await self.fetch_message(msgid)
            except:
                pass
            if platform=='discord':
                if is_pr or is_pr_ref:
                    if source == 'discord':
                        button_style = discord.ButtonStyle.blurple
                    elif source == 'revolt':
                        button_style = discord.ButtonStyle.red
                    else:
                        button_style = discord.ButtonStyle.gray
                    if is_pr:
                        pr_actionrow = discord.ui.ActionRow(
                            discord.ui.Button(style=button_style, label=f'Post ID: {pr_id}',
                                              emoji='\U0001F4AC', disabled=True)
                        )
                    else:
                        try:
                            msg = await self.fetch_message(self.prs[pr_id])
                        except:
                            traceback.print_exc()
                            # Hide PR reference to avoid issues
                            is_pr_ref = False
                        else:
                            try:
                                pr_actionrow = discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.url, label=f'Referencing Post #{pr_id}',
                                                      emoji='\U0001F517',url=await msg.fetch_url(guild))
                                )
                            except:
                                pr_actionrow = discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.gray, label=f'Referencing Post #{pr_id}',
                                                      emoji='\U0001F517', disabled=True)
                                )
                    if pr_actionrow:
                        components = discord.ui.MessageComponents(
                            pr_actionrow
                        )
                if reply_msg:
                    if not trimmed:
                        is_copy = False
                        try:
                            content = message.reference.cached_message.content
                        except:
                            if source=='revolt':
                                msg = await message.channel.fetch_message(message.replies[0].id)
                            elif source=='guilded':
                                msg = await message.channel.fetch_message(message.replied_to[0].id)
                                if msg.webhook_id:
                                    is_copy = True
                            else:
                                msg = await message.channel.fetch_message(message.reference.message_id)
                            content = msg.content
                        clean_content = discord.utils.remove_markdown(content)

                        if reply_msg.reply and source=='guilded' and is_copy:
                            clean_content = clean_content.split('\n',1)[1]

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

                    author_text = '[unknown]'
                    if source == 'discord':
                        button_style = discord.ButtonStyle.blurple
                    elif source == 'revolt':
                        button_style = discord.ButtonStyle.red
                    else:
                        button_style = discord.ButtonStyle.gray

                    try:
                        if reply_msg.source=='revolt':
                            user = self.bot.revolt_client.get_user(reply_msg.author_id)
                            if not user.display_name:
                                author_text = f'@{user.name}'
                            else:
                                author_text = f'@{user.display_name}'
                        elif reply_msg.source=='guilded':
                            user = self.bot.guilded_client.get_user(reply_msg.author_id)
                            author_text = f'@{user.name}'
                        else:
                            user = self.bot.get_user(int(reply_msg.author_id))
                            author_text = f'@{user.global_name}'
                        if f'{reply_msg.author_id}' in list(self.bot.db['nicknames'].keys()):
                            author_text = '@'+self.bot.db['nicknames'][f'{reply_msg.author_id}']
                    except:
                        pass

                    # Prevent empty buttons
                    try:
                        count = len(message.reference.cached_message.embeds) + len(message.reference.cached_message.attachments)
                    except:
                        if source == 'revolt':
                            msg = await message.channel.fetch_message(message.replies[0].id)
                        elif source == 'guilded':
                            msg = await message.channel.fetch_message(message.replied_to[0].id)
                        else:
                            msg = await message.channel.fetch_message(message.reference.message_id)
                        count = len(msg.embeds) + len(msg.attachments)

                    if len(trimmed)==0:
                        content_btn = discord.ui.Button(style=button_style,
                                                        label=f'x{count}', emoji='\U0001F3DE', disabled=True)
                    else:
                        content_btn = discord.ui.Button(style=button_style, label=trimmed, disabled=True)

                    # Add PR buttons too.
                    if is_pr or is_pr_ref:
                        try:
                            components = discord.ui.MessageComponents(
                                pr_actionrow,
                                discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.url,label='Replying to '+author_text,
                                                      url=await reply_msg.fetch_url(guild))
                                ),
                                discord.ui.ActionRow(
                                    content_btn
                                )
                            )
                        except:
                            components = discord.ui.MessageComponents(
                                pr_actionrow,
                                discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.gray, label='Replying to [unknown]',
                                                      disabled=True)
                                )
                            )
                    else:
                        try:
                            components = discord.ui.MessageComponents(
                                discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.url, label='Replying to '+author_text,
                                                      url=await reply_msg.fetch_url(guild))
                                ),
                                discord.ui.ActionRow(
                                    content_btn
                                )
                            )
                        except:
                            components = discord.ui.MessageComponents(
                                discord.ui.ActionRow(
                                    discord.ui.Button(style=discord.ButtonStyle.gray, label='Replying to [unknown]',
                                                      disabled=True)
                                ),
                                discord.ui.ActionRow(
                                    content_btn
                                )
                            )

                    replying = True

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
                    elif source=='guilded':
                        tempfile = await source_file.to_file()
                        return discord.File(fp=tempfile.fp, filename=source_file.filename)
                elif platform=='revolt':
                    if source=='discord':
                        f = await source_file.to_file(use_cached=True)
                        return revolt.File(f.fp.read(), filename=f.filename)
                    elif source=='guilded':
                        f = await source_file.to_file()
                        return revolt.File(f.fp.read(), filename=f.filename)
                    elif source=='revolt':
                        filebytes = await source_file.read()
                        return revolt.File(filebytes, filename=source_file.filename)
                elif platform=='guilded':
                    if source=='guilded':
                        try:
                            return await source_file.to_file()
                        except:
                            return await source_file.to_file()
                    elif source=='revolt':
                        filebytes = await source_file.read()
                        return guilded.File(fp=BytesIO(filebytes), filename=source_file.filename)
                    elif source=='discord':
                        tempfile = await source_file.to_file(use_cached=True)
                        return guilded.File(fp=tempfile.fp, filename=source_file.filename)

            for attachment in message.attachments:
                if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                        not 'image' in attachment.content_type) or attachment.size > 25000000:
                    continue
                size_total += attachment.size
                if size_total > 25000000:
                    if not limit_notified:
                        limit_notified = True
                        if source==platform=='revolt':
                            await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                                       replies=[revolt.MessageReply(message)])
                        elif source==platform=='guilded':
                            await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                                       reply_to=message)
                        elif source==platform:
                            await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                                       reference=message)
                    break
                files.append(await to_file(attachment))

            # Username
            if source == 'revolt':
                if not message.author.display_name:
                    author = message.author.name
                else:
                    author = message.author.display_name
            elif source=='guilded':
                author = message.author.name
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

            if system:
                try:
                    url = self.bot.user.avatar.url
                except:
                    url = None

            # Add system identifier
            msg_author = author
            if system:
                msg_author = self.bot.user.global_name + ' (system)'

            # Send message
            embeds = message.embeds
            if not message.author.bot and not system:
                embeds = []

            if platform=='discord':
                msg_author_dc = msg_author
                if len(msg_author) > 35:
                    msg_author_dc = msg_author[:-(len(msg_author) - 35)]
                try:
                    tb_v2 = str(message.guild.id) in str(
                        self.bot.db['experiments']['threaded_bridge_v2']) and source == 'discord'
                except:
                    pass

                webhook = None
                try:
                    webhook = self.bot.webhook_cache[f'{guild}'][f'{self.bot.db["rooms"][room][guild][0]}']
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

                async def tbsend(webhook,url,msg_author_dc,embeds,message,files,mentions,components,sameguild,
                                 thread_sameguild,destguild):
                    try:
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=message.content, files=files, allowed_mentions=mentions,
                                                 components=components, wait=True)
                    except:
                        return None
                    tbresult = []
                    if sameguild:
                        if len(thread_sameguild) > 0:
                            thread_sameguild.clear()
                            thread_sameguild.append(msg.id)
                    else:
                        tbresult.append({f'{destguild.id}': [webhook.channel.id, msg.id]})
                    tbresult.append({
                                    f'{destguild.id}': f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'})
                    return tbresult

                if tb_v2:
                    threads.append(asyncio.create_task(tbsend(webhook,url,msg_author_dc,embeds,message,files,
                                                              mentions,components,sameguild,thread_sameguild,
                                                              destguild)))
                else:
                    try:
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=message.content, files=files, allowed_mentions=mentions,
                                                 components=components, wait=True)
                    except:
                        continue
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
                if str(message.author.id) in list(self.bot.db['colors'].keys()):
                    color = self.bot.db['colors'][str(message.author.id)]
                    if color == 'inherit':
                        if source=='revolt':
                            try:
                                color = message.author.roles[len(message.author.roles) - 1].colour.replace('#', '')
                                rgbtuple = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                                rvtcolor = f'rgb{rgbtuple}'
                            except:
                                pass
                        else:
                            rvtcolor = f'rgb({message.author.color.r},{message.author.color.g},{message.author.color.b})'
                    else:
                        try:
                            rgbtuple = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                            rvtcolor = f'rgb{rgbtuple}'
                        except:
                            pass

                msg_author_rv = msg_author
                if len(msg_author) > 32:
                    msg_author_rv = msg_author[:-(len(msg_author)-32)]

                try:
                    persona = revolt.Masquerade(name=msg_author_rv, avatar=url, colour=rvtcolor)
                except:
                    persona = revolt.Masquerade(name=msg_author_rv, avatar=None, colour=rvtcolor)
                try:
                    msg = await ch.send(
                        content=message.content, embeds=message.embeds, attachments=files, replies=replies,
                        masquerade=persona
                    )
                except:
                    continue

                message_ids.update({destguild.id:[ch.id,msg.id]})
            elif platform=='guilded':
                try:
                    tb_v2 = str(message.guild.id) in str(
                        self.bot.db['experiments']['threaded_bridge_v2']) and source == 'discord'
                except:
                    pass
                try:
                    webhook = self.bot.webhook_cache[f'{guild}'][f'{self.bot.db["rooms_guilded"][room][guild][0]}']
                except:
                    try:
                        webhook = await destguild.fetch_webhook(self.bot.db["rooms_guilded"][room][guild][0])
                        if f'{guild}' in list(self.bot.webhook_cache.keys()):
                            self.bot.webhook_cache[f'{guild}'].update({f'{webhook.id}':webhook})
                        else:
                            self.bot.webhook_cache.update({f'{guild}':{f'{webhook.id}':webhook}})
                    except:
                        continue

                # Processing replies for Revolt here for efficiency
                replytext = ''

                if not trimmed and reply_msg:
                    is_copy = False
                    try:
                        content = message.reference.cached_message.content
                    except:
                        if source == 'revolt':
                            msg = await message.channel.fetch_message(message.replies[0].id)
                        elif source == 'guilded':
                            msg = await message.channel.fetch_message(message.replied_to[0].id)
                            if msg.webhook_id:
                                is_copy = True
                        else:
                            msg = await message.channel.fetch_message(message.reference.message_id)
                        content = msg.content
                    clean_content = discord.utils.remove_markdown(content)

                    if reply_msg.reply and source == 'guilded' and is_copy:
                        clean_content = clean_content.split('\n', 1)[1]

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

                if reply_msg:
                    author_text = '[unknown]'

                    try:
                        if reply_msg.source == 'revolt':
                            user = self.bot.revolt_client.get_user(reply_msg.author_id)
                            if not user.display_name:
                                author_text = f'@{user.name}'
                            else:
                                author_text = f'@{user.display_name}'
                        elif reply_msg.source == 'guilded':
                            user = self.bot.guilded_client.get_user(reply_msg.author_id)
                            author_text = f'@{user.name}'
                        else:
                            user = self.bot.get_user(int(reply_msg.author_id))
                            author_text = f'@{user.global_name}'
                        if f'{reply_msg.author_id}' in list(self.bot.db['nicknames'].keys()):
                            author_text = '@' + self.bot.db['nicknames'][f'{reply_msg.author_id}']
                    except:
                        pass

                    try:
                        replytext = f'**[Replying to {author_text}]({reply_msg.urls[destguild.id]})** - *{trimmed}*\n'
                    except:
                        replytext = f'**Replying to [unknown]**\n'

                if len(replytext+message.content)==0:
                    replytext = '[empty message]'

                msg_author_gd = msg_author
                if len(msg_author) > 25:
                    msg_author_gd = msg_author[:-(len(msg_author) - 25)]

                async def tbsend(webhook, url, msg_author_gd, embeds, message, replytext, files, sameguild, destguild,
                                 thread_sameguild):
                    try:
                        msg = await webhook.send(avatar_url=url,
                                                 username=msg_author_gd.encode("ascii", errors="ignore").decode(),
                                                 embeds=embeds, content=replytext + message.content, files=files)
                    except:
                        return None

                    gdresult = []
                    if sameguild:
                        if len(thread_sameguild) > 0:
                            thread_sameguild.clear()
                            thread_sameguild.append(msg.id)
                    else:
                        gdresult.append({f'{destguild.id}': [msg.channel.id, msg.id]})
                    gdresult.append({f'{destguild.id}': msg.share_url})
                    return gdresult

                if tb_v2:
                    threads.append(asyncio.create_task(tbsend(webhook, url, msg_author_gd, embeds, message, replytext,
                                                              files, sameguild, destguild, thread_sameguild)))
                else:
                    try:
                        msg = await webhook.send(avatar_url=url, username=msg_author_gd.encode("ascii", errors="ignore").decode(),
                                                 embeds=embeds,content=replytext+message.content,files=files)
                    except:
                        continue
                    if sameguild:
                        thread_sameguild = [msg.id]
                    else:
                        message_ids.update({f'{destguild.id}':[msg.channel.id,msg.id]})
                    urls.update({f'{destguild.id}':msg.share_url})

        # Update cache
        tbv2_results = []
        if tb_v2:
            tbv2_results = await asyncio.gather(*threads)
        urls = urls | thread_urls

        if tb_v2:
            for result in tbv2_results:
                if not result:
                    continue
                if len(result)==1:
                    urls.update(result[0])
                else:
                    message_ids.update(result[0])
                    urls.update(result[1])

        if len(thread_sameguild) > 0 and platform=='discord' and source=='discord':
            parent_id = thread_sameguild[0]
        else:
            parent_id = message.id
        if is_pr and not pr_id in list(self.prs.keys()) and platform==source:
            self.prs.update({pr_id:parent_id})
        try:
            index = await self.indexof(parent_id)
            msg_object = await self.fetch_message(parent_id)
            if msg_object.source==platform:
                self.bridged[index].copies = msg_object.copies | message_ids
            else:
                try:
                    self.bridged[index].external_copies[platform] = self.bridged[index].external_copies[platform] | message_ids
                except:
                    self.bridged[index].external_copies.update({platform:message_ids})
            self.bridged[index].urls = self.bridged[index].urls | urls
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
                webhook=should_resend or system,
                prehook=message.id,
                room=room,
                reply=replying
            ))
        if multisend_debug:
            ct = time.time()
            diff = round(ct-pt,3)
            return [platform,diff,len(message_ids),tb_v2]

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
        msgs = []
        prs = {}
        restored = False
        if hasattr(self.bot, 'bridge'):
            msgs = self.bot.bridge.bridged
            prs = self.bot.bridge.prs
            restored = self.bot.bridge.restored
            del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot)
        self.bot.bridge.bridged = msgs
        self.bot.bridge.prs = prs
        self.bot.bridge.restored = restored

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
        text = f'THINK, {username.upper()}, THINK!'
        text_width = im_draw.textlength(text, font)
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

    @commands.context_command(name='Reaction image')
    async def reaction(self, ctx, message: discord.Message):
        return await ctx.send('Reaction Images are currently disabled.',ephemeral=True)
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
        #
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
        #
        try:
            interaction = await self.bot.wait_for('component_interaction', check=check, timeout=60)
        except:
            try:
                return await msg.edit(content='Timed out.', components=None)
            except:
                return
        #
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
        try:
            msg_obj: UnifierMessage = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await ctx.send('Could not find message in cache!')
        if msg_obj.source=='discord':
            try:
                username = self.bot.get_user(int(msg_obj.author_id)).name
            except:
                username = '[unknown]'
            try:
                guildname = self.bot.get_guild(int(msg_obj.guild_id)).name
            except:
                guildname = '[unknown]'
        elif msg_obj.source=='revolt':
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
        await ctx.send(f'Sent by @{username} ({msg_obj.author_id}) in {guildname} ({msg_obj.guild_id}, {msg_obj.source})\n\nParent ID: {msg_obj.id}')

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
            if msg.webhook:
                raise ValueError()
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
            if msg.webhook:
                raise ValueError()
            return await msgconf.edit('Deleted message (parent deleted, copies will follow)')
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(msg_id)
                await msgconf.edit(f'Deleted message ({deleted} copies deleted)')
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
                if msg.webhook:
                    raise ValueError()
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
    async def viewmsg(self,ctx,*,msgid=None):
        if not ctx.author.id == 356456393491873795:
            return
        try:
            msgid = ctx.message.reference.message_id
        except:
            if not msgid:
                return await ctx.send('No message detected')
        msg: UnifierMessage = await self.bot.bridge.fetch_message(msgid)
        embed = discord.Embed(title=f'Viewing message {msg.id}',
                              description=f'Guild: {msg.guild_id}\nSource: {msg.source}\nParent is webhook: {msg.webhook}',
                              color=self.bot.colors.unifier)
        text = ''
        for key in msg.copies:
            info = msg.copies[key]
            if len(text)==0:
                text = f'{key}: {info[1]}, sent in {info[0]}'
            else:
                text = f'{text}\n{key}: {info[1]}, sent in {info[0]}'
        embed.add_field(name='Copies (samesource)',value=text,inline=False)
        for platform in msg.external_copies:
            text = ''
            for key in msg.external_copies[platform]:
                info = msg.external_copies[platform][key]
                if len(text) == 0:
                    text = f'{key}: {info[1]}, sent in {info[0]}'
                else:
                    text = f'{text}\n{key}: {info[1]}, sent in {info[0]}'
            embed.add_field(name=f'Copies ({platform})', value=text, inline=False)
        text = ''
        for key in msg.urls:
            if len(text) == 0:
                text = f'{key}: [link](<{msg.urls[key]}>)'
            else:
                text = f'{text}\n{key}: [link](<{msg.urls[key]}>)'
        embed.add_field(name=f'URLs', value=text, inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def mstiming(self,ctx,*,index):
        if not ctx.author.id == 356456393491873795:
            return
        index = int(index)
        await ctx.send(f'{multisend_logs[index]}')

    @commands.command(hidden=True)
    async def initbridge(self, ctx, *, args=''):
        if not ctx.author.id == 356456393491873795:
            return
        msgs = []
        prs = {}
        if 'preserve' in args:
            msgs = self.bot.bridge.bridged
            prs = self.bot.bridge.prs
        del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot)
        if 'preserve' in args:
            self.bot.bridge.bridged = msgs
            self.bot.bridge.prs = prs
        await ctx.send('Bridge initialized')

    @commands.command(hidden=True)
    async def system(self, ctx, room):
        if not ctx.author.id == 356456393491873795:
            return
        ctx.message.content = ctx.message.content.replace(f'{self.bot.command_prefix}system {room}','',1)
        await self.bot.bridge.send(room,ctx.message,'discord',system=True)
        for platform in externals:
            await self.bot.bridge.send(room, ctx.message, platform, system=True)
        await ctx.send('Sent as system')

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

        multisend_exp = False
        try:
            multisend_exp = str(message.guild.id) in str(self.bot.db['experiments']['multisend'])
        except:
            pass

        if multisend_exp:
            if message.content.startswith('['):
                parts = message.content.replace('[','',1).replace('\n',' ').split('] ',1)
                if len(parts) > 1 and len(parts[0])==6:
                    if (parts[0].lower()=='newest' or parts[0].lower()=='recent' or
                            parts[0].lower() == 'latest'):
                        multisend_exp = False
                    elif parts[0].lower() in list(self.bot.bridge.prs.keys()):
                        multisend_exp = False
            if '[emoji:' in message.content:
                multisend_exp = False

        tasks = []

        if multisend_exp:
            # Multisend experiment
            # Sends Discord message along with other platforms to minimize
            # latency on external platforms.
            self.bot.bridge.bridged.append(UnifierMessage(
                    author_id=message.author.id,
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    original=message.id,
                    copies={},
                    external_copies={},
                    urls={},
                    source='discord',
                    room=roomname,
                    external_urls={}
                )
            )
            tasks.append(self.bot.bridge.send(room=roomname,message=message,platform='discord',multisend_debug=True))
        else:
            await self.bot.bridge.send(room=roomname, message=message, platform='discord')

        for platform in externals:
            tasks.append(self.bot.loop.create_task(self.bot.bridge.send(room=roomname, message=message, platform=platform,multisend_debug=multisend_exp)))

        pt = time.time()
        results = None
        try:
            results = await asyncio.gather(*tasks)
        except:
            pass

        if multisend_exp:
            try:
                await self.bot.bridge.merge_prehook(message.id)
            except:
                pass

        if multisend_exp and results:
            ct = time.time()
            msg = await self.bot.bridge.fetch_message(message.id)
            count = len(msg.copies)
            for platform in externals:
                count += len(msg.external_copies[platform])
            diff = round(ct - pt, 3)
            mslog = {'duration':diff}
            for result in results:
                mslog.update({result[0]:{'duration':result[1],'copies':result[2],'tb2':result[3]}})
            multisend_logs.append(mslog)

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
        origin_room = 0 # keeping this in case i decide to log this

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

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not str(msg.id)==str(message.id):
                raise ValueError()
        except:
            return

        await self.bot.bridge.edit(msg.id,message.content)

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

        await self.bot.bridge.delete_copies(msg.id)

def setup(bot):
    bot.add_cog(Bridge(bot))
