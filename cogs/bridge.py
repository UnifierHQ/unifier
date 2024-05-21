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
import hashlib
import asyncio
import guilded
import revolt
from nextcord.ext import commands
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
import math
from io import BytesIO
import os
from utils import log, ui
import importlib

with open('config.json', 'r') as file:
    data = json.load(file)

mentions = nextcord.AllowedMentions(everyone=False, roles=False, users=False)

multisend_logs = []
plugin_data = {}

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

class UnifierTranslator:
    def __init__(self,bot):
        self.bot = bot

    def identify(self,message: nextcord.Message or revolt.Message or guilded.Message):
        source = 'discord'
        extlist = list(self.bot.extensions)
        if type(message) is revolt.Message:
            if not 'cogs.bridge_revolt' in extlist:
                raise RuntimeError('Revolt Support not initialized')
            source = 'revolt'
        if type(message) is guilded.ChatMessage:
            if not 'cogs.bridge_guilded' in extlist:
                raise RuntimeError('Guilded Support not initialized')
            source = 'guilded'

        if message.webhook_id:
            return 'webhook'

        if len(message.embeds) > 0 and source=='discord':
            for embed in message.embeds:
                if not embed.type=='rich':
                    continue
                if (embed.footer.text.startswith('Message ID: ') and
                        embed.fields[0].value.startswith('\U0001F4CCSent From: ') and
                        embed.fields[0].value.endswith('[Bot-Invite](https://discord.com/api/oauth2/authorize?client_id=1051199485168066610&permissions=8&scope=bot%20applications.commands)')):
                    return 'embed_silly'

    def translate(self,message: nextcord.Message or revolt.Message or guilded.Message):
        source = 'discord'
        extlist = list(self.bot.extensions)
        if type(message) is revolt.Message:
            if not 'cogs.bridge_revolt' in extlist:
                raise RuntimeError('Revolt Support not initialized')
            source = 'revolt'
        if type(message) is guilded.ChatMessage:
            if not 'cogs.bridge_guilded' in extlist:
                raise RuntimeError('Guilded Support not initialized')
            source = 'guilded'

        msgtype = self.identify(message)
        if msgtype=='embed_silly':
            translated = {
                'author': message.embed
            }

class UnifierMessage:
    def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room,
                 external_urls=None, webhook=False, prehook=None, reply=False, external_bridged=False, reactions=None):
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
        self.external_bridged = external_bridged
        if not reactions or not type(reactions) is dict:
            self.reactions = {}
        else:
            self.reactions = reactions

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

    async def add_reaction(self, emoji, userid):
        userid = str(userid)
        if not emoji in list(self.reactions.keys()):
            self.reactions.update({emoji:{}})
        if not userid in list(self.reactions[emoji].keys()):
            self.reactions[emoji].update({userid:0})
        self.reactions[emoji][userid] += 1
        return self.reactions[emoji][userid]

    async def remove_reaction(self, emoji, userid):
        userid = str(userid)
        self.reactions[emoji][userid] -= 1
        if self.reactions[emoji][userid] <= 0:
            self.reactions[emoji].pop(userid)

            total = 0
            for user in self.reactions[emoji]:
                total += self.reactions[emoji][user]

            if total==0:
                self.reactions.pop(emoji)

            return 0
        else:
            return self.reactions[emoji][userid]

    async def fetch_external_url(self, source, guild_id):
        return self.external_urls[source][guild_id]

    async def fetch_external(self, platform: str, guild_id: str):
        return ExternalReference(guild_id, self.external_copies[platform][str(guild_id)][0], self.external_copies[platform][str(guild_id)][1])

class UnifierRaidBan:
    def __init__(self, debug=True, frequency=1):
        self.frequency = frequency # Frequency of content
        self.time = round(time.time()) # Time when ban occurred
        self.duration = 600 # Duration of ban in seconds. Base is 600
        self.expire = round(time.time()) + self.duration # Expire time
        self.debug = debug # Debug raidban
        self.banned = False

    def is_banned(self):
        if self.expire < time.time():
            return False or self.banned
        return True

    def increment(self,count=1):
        if self.banned:
            raise RuntimeError()
        self.frequency += count
        t = math.ceil((round(time.time())-self.time)/60)
        i = self.frequency
        threshold = round(9600*t/i) # Base is 160 minutes
        prevd = self.duration
        self.duration = self.duration * 2
        diff = self.duration - prevd
        self.expire += diff
        self.banned = self.duration > threshold
        return self.duration > threshold

class UnifierMessageRaidBan(UnifierRaidBan):
    def __init__(self, content_hash, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_hash = content_hash

class UnifierPossibleRaidEvent:
    def __init__(self,userid,content, frequency=1):
        self.userid = userid # User ID of possible raider
        self.hash = encrypt_string(content) # Hash of raid message string
        self.time = round(time.time())  # Time when ban occurred
        self.frequency = frequency
        self.impact_score = 100*frequency

    def increment(self,count=1):
        self.frequency += count
        t = math.ceil((round(time.time()) - self.time) / 60)
        i = self.frequency
        self.impact_score = round(100*i/t)
        return self.impact_score > 300

class UnifierBridge:
    def __init__(self, bot, logger, webhook_cache=None):
        self.bot = bot
        self.bridged = []
        self.prs = {}
        self.webhook_cache = webhook_cache or {}
        self.restored = False
        self.raidbans = {}
        self.possible_raid = {}
        self.logger = logger
        self.secbans = {}
        self.restricted = {}

    def is_raidban(self,userid):
        try:
            ban: UnifierRaidBan = self.raidbans[f'{userid}']
        except:
            return False
        return ban.is_banned()

    def raidban(self,userid):
        self.raidbans.update({f'{userid}':UnifierRaidBan()})

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

        if self.bot.config['compress_cache']:
            compress_json.dump(data,filename+'.lzma')
        else:
            with open(filename, "w+") as file:
                json.dump(data, file)
        del data
        return

    async def restore(self,filename='bridge.json'):
        if self.restored:
            raise RuntimeError('Already restored from backup')
        if self.bot.config['compress_cache']:
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
                prehook=data['messages'][f'{x}']['prehook'],
                reactions=data['messages'][f'{x}']['reactions'] if 'reactions' in list(data['messages'][f'{x}'].keys()) else {}
            )
            self.bridged.append(msg)

        self.prs = data['posts']
        del data
        self.restored = True
        return

    async def run_security(self, message):
        responses = {}
        unsafe = False

        for plugin in self.bot.loaded_plugins:
            script = self.bot.loaded_plugins[plugin]

            try:
                data = plugin_data[plugin]
            except:
                data = {}

            response = await script.scan(message,data)

            if response['unsafe']:
                unsafe = True

            responses.update({plugin: response})
            if len(response['data']) > 0:
                if not plugin in list(plugin_data.keys()):
                    plugin_data.update({plugin:{}})
                plugin_data[plugin].update(response['data'])

        return unsafe, responses

    async def run_stylizing(self, message):
        for plugin in os.listdir('plugins'):
            with open('plugins/' + plugin) as file:
                extinfo = json.load(file)
                try:
                    if not 'content_processing' in extinfo['services']:
                        continue
                except:
                    continue
            script = importlib.import_module('utils.' + plugin[:-5] + '_content_processing')
            importlib.reload(script)
            message = await script.process(message)
            del script

        return message


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

    async def add_exp(self, user_id):
        if not self.bot.config['enable_leveling']:
            return 0, False
        if not f'{user_id}' in self.bot.db['exp'].keys():
            self.bot.db['exp'].update({f'{user_id}':{'experience':0,'level':1,'progress':0}})
        self.bot.db['exp'][f'{user_id}']['experience'] += random.randint(80,120)
        ratio, remaining = await self.progression(user_id)
        if ratio >= 1:
            self.bot.db['exp'][f'{user_id}']['experience'] = -remaining
            self.bot.db['exp'][f'{user_id}']['level'] += 1
            newratio, _remaining = await self.progression(user_id)
        else:
            newratio = ratio
        self.bot.db['exp'][f'{user_id}']['progress'] = newratio
        self.bot.db.save_data()
        return self.bot.db['exp'][f'{user_id}']['experience'], ratio >= 1

    async def progression(self, user_id):
        base = 1000
        rate = 1.4
        target = base * (rate ** self.bot.db['exp'][f'{user_id}']['level'])
        return (
            self.bot.db['exp'][f'{user_id}']['experience']/target, target-self.bot.db['exp'][f'{user_id}']['experience']
        )

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
        threads = []

        async def delete_discord(msgs):
            count = 0
            threads = []
            for key in list(self.bot.db['rooms'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.bot.get_guild(int(key))
                try:
                    try:
                        webhook = self.bot.webhook_cache[f'{guild.id}'][
                            f'{self.bot.db["rooms"][msg.room][f"{guild.id}"][0]}'
                        ]
                    except:
                        webhook = None
                        hooks = await guild.webhooks()
                        for hook in hooks:
                            if int(self.bot.db['rooms'][msg.room][key][0]) == hook.id:
                                webhook = hook
                                break

                        if not webhook:
                            # No webhook found
                            continue
                except:
                    continue

                try:
                    threads.append(asyncio.create_task(
                        webhook.delete_message(int(msgs[key][1]))
                    ))
                    count += 1
                except:
                    # traceback.print_exc()
                    pass
            await asyncio.gather(*threads)
            return count

        async def delete_guilded(msgs):
            if not 'cogs.bridge_guilded' in list(self.bot.extensions.keys()):
                return
            count = 0
            threads = []
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
                    threads.append(asyncio.create_task(
                        webhook.delete_message(msgs[key][1])
                    ))
                    count += 1
                except:
                    # traceback.print_exc()
                    pass
            await asyncio.gather(*threads)
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
                    # traceback.print_exc()
                    continue
            return count

        if msg.source=='discord':
            threads.append(asyncio.create_task(
                delete_discord(msg.copies)
            ))
        elif msg.source=='revolt':
            threads.append(asyncio.create_task(
                delete_revolt(msg.copies)
            ))
        elif msg.source=='guilded':
            threads.append(asyncio.create_task(
                delete_guilded(msg.copies)
            ))

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                threads.append(asyncio.create_task(
                    delete_discord(msg.external_copies['discord'])
                ))
            elif platform=='revolt':
                threads.append(asyncio.create_task(
                    delete_revolt(msg.external_copies['revolt'])
                ))
            elif platform=='guilded':
                threads.append(asyncio.create_task(
                    delete_guilded(msg.external_copies['guilded'])
                ))

        results = await asyncio.gather(*threads)
        return sum(results)

    async def edit(self, message, content):
        msg: UnifierMessage = await self.fetch_message(message)
        threads = []

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
            threads = []

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
                    threads.append(asyncio.create_task(
                        webhook.edit_message(int(msgs[key][1]),content=text,allowed_mentions=mentions)
                    ))
                except:
                    traceback.print_exc()
                    pass

            await asyncio.gather(*threads)

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
            threads = []
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
                    threads.append(asyncio.create_task(
                        toedit.edit(content=text)
                    ))
                except:
                    traceback.print_exc()
                    pass

                await asyncio.gather(*threads)

        if msg.source=='discord':
            threads.append(asyncio.create_task(
                edit_discord(msg.copies)
            ))
        elif msg.source=='revolt':
            threads.append(asyncio.create_task(
                edit_revolt(msg.copies)
            ))

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                threads.append(asyncio.create_task(
                    edit_discord(msg.external_copies['discord'],friendly=True)
                ))
            elif platform=='revolt':
                threads.append(asyncio.create_task(
                    edit_revolt(msg.external_copies['revolt'],friendly=True)
                ))

        await asyncio.gather(*threads)

    async def send(self, room: str, message: nextcord.Message or revolt.Message,
                   platform: str = 'discord', system: bool = False,
                   extbridge=False, id_override=None, ignore=None):
        if is_room_locked(room,self.bot.db) and not message.author.id in self.bot.admins:
            return
        if ignore is None:
            ignore = []
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

        is_pr = room == self.bot.config['posts_room'] and (
            self.bot.config['allow_prs'] if 'allow_prs' in list(self.bot.config.keys()) else False or
            self.bot.config['allow_posts'] if 'allow_posts' in list(self.bot.config.keys()) else False
        )
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
        temp_pr_ref = room == self.bot.config['posts_ref_room'] and (
            self.bot.config['allow_prs'] if 'allow_prs' in list(self.bot.config.keys()) else False or
            self.bot.config['allow_posts'] if 'allow_posts' in list(self.bot.config.keys()) else False
        )
        if temp_pr_ref and message.content.startswith('[') and source==platform=='discord' and (
                self.bot.config['allow_prs'] if 'allow_prs' in list(self.bot.config.keys()) else False or
                self.bot.config['allow_posts'] if 'allow_posts' in list(self.bot.config.keys()) else False
            ):
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
                emoji = nextcord.utils.find(
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
        tb_v2 = source=='discord'

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

            if destguild.id in ignore:
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
                replying = True
                reply_msg = await self.fetch_message(msgid)
            except:
                pass
            if platform=='discord':
                if is_pr or is_pr_ref:
                    if source == 'discord':
                        button_style = nextcord.ButtonStyle.blurple
                    elif source == 'revolt':
                        button_style = nextcord.ButtonStyle.red
                    else:
                        button_style = nextcord.ButtonStyle.gray
                    if is_pr:
                        pr_actionrow = ui.ActionRow(
                            nextcord.ui.Button(style=button_style, label=f'Post ID: {pr_id}',
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
                                pr_actionrow = ui.ActionRow(
                                    nextcord.ui.Button(style=nextcord.ButtonStyle.url, label=f'Referencing Post #{pr_id}',
                                                       emoji='\U0001F517',url=await msg.fetch_url(guild))
                                )
                            except:
                                pr_actionrow = ui.ActionRow(
                                    nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label=f'Referencing Post #{pr_id}',
                                                       emoji='\U0001F517', disabled=True)
                                )
                    if pr_actionrow:
                        components = ui.View()
                        components.add_row(pr_actionrow)
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
                        clean_content = nextcord.utils.remove_markdown(content)

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
                        button_style = nextcord.ButtonStyle.blurple
                    elif source == 'revolt':
                        button_style = nextcord.ButtonStyle.red
                    else:
                        button_style = nextcord.ButtonStyle.gray

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
                        content_btn = nextcord.ui.Button(
                            style=button_style,label=f'x{count}', emoji='\U0001F3DE', disabled=True
                        )
                    else:
                        content_btn = nextcord.ui.Button(
                            style=button_style, label=trimmed, disabled=True
                        )

                    # Add PR buttons too.
                    if is_pr or is_pr_ref:
                        try:
                            components = ui.View()
                            components.add_rows(
                                pr_actionrow,
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.url, label='Replying to ' + author_text,
                                        url=await reply_msg.fetch_url(guild)
                                    )
                                ),
                                ui.ActionRow(
                                    content_btn
                                )
                            )
                        except:
                            components = ui.View()
                            components.add_rows(
                                pr_actionrow,
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.gray, label='Replying to [unknown]', disabled=True
                                    )
                                )
                            )
                    else:
                        try:
                            components = ui.View()
                            components.add_rows(
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.url, label='Replying to '+author_text,
                                        url=await reply_msg.fetch_url(guild)
                                    )
                                ),
                                ui.ActionRow(
                                    content_btn
                                )
                            )
                        except:
                            components = ui.View(
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.gray, label='Replying to [unknown]', disabled=True
                                    )
                                ),
                                ui.ActionRow(
                                    content_btn
                                )
                            )
                elif replying:
                    try:
                        if source == 'revolt':
                            authid = message.replies[0].author.id
                        elif source == 'guilded':
                            authid = message.replied_to[0].author.id
                        else:
                            if message.reference.cached_message:
                                authid = message.reference.cached_message.author.id
                            else:
                                authmsg = await message.channel.fetch_message(message.reference.message_id)
                                authid = authmsg.author.id
                    except:
                        authid = None
                    try:
                        botrvt = authid==self.bot.revolt_client.user.id
                    except:
                        botrvt = False
                    try:
                        botgld = authid==self.bot.guilded_client.user.id
                    except:
                        botgld = False
                    if authid==self.bot.user.id or botrvt or botgld:
                        reply_row = ui.ActionRow(
                            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Replying to [system]',
                                              disabled=True)
                        )
                    else:
                        reply_row = ui.ActionRow(
                            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Replying to [unknown]',
                                              disabled=True)
                        )
                    if pr_actionrow:
                        components = ui.MessageComponents()
                        components.add_rows(
                            pr_actionrow,reply_row
                        )
                    else:
                        components = ui.MessageComponents()
                        components.add_rows(
                            reply_row
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
                            try:
                                return await source_file.to_file(use_cached=True, spoiler=False)
                            except:
                                return await source_file.to_file(use_cached=False, spoiler=False)
                    elif source=='revolt':
                        filebytes = await source_file.read()
                        return nextcord.File(fp=BytesIO(filebytes), filename=source_file.filename)
                    elif source=='guilded':
                        tempfile = await source_file.to_file()
                        return nextcord.File(fp=tempfile.fp, filename=source_file.filename)
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
                if source=='guilded':
                    if not attachment.file_type.image and not attachment.file_type.video:
                        continue
                else:
                    if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                            not 'image' in attachment.content_type and not 'text/plain' in attachment.content_type and
                            self.bot.config['safe_filetypes']) or attachment.size > 25000000:
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

            if msg_author.lower()==f'{self.bot.user.name} (system)'.lower() and not system:
                msg_author = '[hidden username]'

            if platform=='discord':
                msg_author_dc = msg_author
                if len(msg_author) > 35:
                    msg_author_dc = msg_author[:-(len(msg_author) - 35)]

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
                                                 view=components if not system else None, wait=True)
                    except:
                        return None
                    tbresult = [
                        {f'{destguild.id}': [webhook.channel.id, msg.id]},
                        {f'{destguild.id}': f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'},
                        [sameguild, msg.id]
                    ]
                    return tbresult

                if tb_v2:
                    threads.append(asyncio.create_task(tbsend(webhook,url,msg_author_dc,embeds,message,files,
                                                              mentions,components,sameguild,thread_sameguild,
                                                              destguild)))
                else:
                    try:
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=message.content, files=files, allowed_mentions=mentions,
                                                 view=components if not system else None, wait=True)
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
                    clean_content = nextcord.utils.remove_markdown(content)

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

                async def tbsend(webhook, url, msg_author_gd, embeds, message, replytext, files, sameguild, destguild):
                    try:
                        msg = await webhook.send(avatar_url=url,
                                                 username=msg_author_gd.encode("ascii", errors="ignore").decode(),
                                                 embeds=embeds, content=replytext + message.content, files=files)
                    except:
                        return None

                    gdresult = [
                        {f'{destguild.id}': [msg.channel.id, msg.id]},
                        {f'{destguild.id}': msg.share_url},
                        [sameguild, msg.id]
                    ]
                    return gdresult

                if tb_v2:
                    threads.append(asyncio.create_task(tbsend(webhook, url, msg_author_gd, embeds, message, replytext,
                                                              files, sameguild, destguild)))
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

        parent_id = None

        if tb_v2:
            for result in tbv2_results:
                if not result:
                    continue
                message_ids.update(result[0])
                urls.update(result[1])
                if result[2][0]:
                    parent_id = result[2][1]

        if not parent_id:
            parent_id = message.id

        if is_pr and not pr_id in list(self.prs.keys()) and platform==source:
            self.prs.update({pr_id:parent_id})

        if system:
            msg_author = self.bot.user.id
        else:
            msg_author = message.author.id

        if id_override:
            parent_id = id_override

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
            if extbridge:
                try:
                    hook = await self.bot.fetch_webhook(message.webhook_id)
                    msg_author = hook.user.id
                except:
                    pass
            self.bridged.append(UnifierMessage(
                author_id=msg_author,
                guild_id=server_id,
                channel_id=message.channel.id,
                original=parent_id,
                copies=copies,
                external_copies=external_copies,
                urls=urls,
                source=source,
                webhook=should_resend or system or extbridge,
                prehook=message.id,
                room=room,
                reply=replying,
                external_bridged=extbridge
            ))
        return parent_id

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
            # Message wasn't sent from nextcord.
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
        self.logger = log.buildlogger(self.bot.package, 'bridge', self.bot.loglevel)
        msgs = []
        prs = {}
        restored = False
        if hasattr(self.bot, 'bridge'):
            if self.bot.bridge: # Avoid restoring if bridge is None
                msgs = self.bot.bridge.bridged
                prs = self.bot.bridge.prs
                restored = self.bot.bridge.restored
                del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot,self.logger)
        self.bot.bridge.bridged = msgs
        self.bot.bridge.prs = prs
        self.bot.bridge.restored = restored

    @commands.command(aliases=['colour'],description='Sets Revolt color.')
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
            embed = nextcord.Embed(title='Your Revolt color',description=current_color,color=embed_color)
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

    @commands.command(aliases=['find'],description='Identifies the origin of a message.')
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

    @commands.command(description='Sets a nickname. An empty provided nickname will reset it.')
    async def nickname(self, ctx, *, nickname=''):
        if len(nickname) > 35:
            return await ctx.send('Please keep your nickname within 35 characters.')
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(f'{ctx.author.id}', None)
        else:
            self.bot.db['nicknames'].update({f'{ctx.author.id}': nickname})
        self.bot.db.save_data()
        await ctx.send('Nickname updated.')

    @commands.command(description='Shows a list of all global emojis available on the instance.')
    async def emojis(self, ctx, *, index=1):
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
        embed = nextcord.Embed(
            title='UniChat Emojis list',
            description=(
                    'To use an emoji, simply send `[emoji: emoji_name]`.\nIf there\'s emojis with '+
                    'duplicate names, use `[emoji2: emoji_name]` to send the 2nd emoji with that '+
                    'name.\n' + text
            ),
            color=self.bot.colors.unifier
        )
        embed.set_footer(text=f'Page {index + 1}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(description='Shows emoji info.')
    async def emoji(self, ctx, *, emoji=''):
        emojis = []
        for emoji in self.bot.emojis:
            if emoji.guild_id in self.bot.db['emojis']:
                emojis.append(emoji)

        emoji_preview = None
        for emoji1 in emojis:
            if f'<:{emoji1.name}:{emoji1.id}>'==emoji or emoji1.name==emoji or str(emoji1.id)==emoji:
                emoji_preview = emoji1
                break

        if not emoji_preview:
            return await ctx.send('Could not find this emoji!')

        embed = nextcord.Embed(
            title=emoji_preview.name,
            description=f'<:{emoji_preview.name}:{emoji_preview.id}>',
            color=self.bot.colors.unifier
        )
        embed.add_field(
            name='Origin guild',
            value=emoji_preview.guild.name
        )
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['modcall'],
        description='Ping all moderators to the chat! Use only when necessary, or else.'
    )
    @commands.cooldown(rate=1, per=1800, type=commands.BucketType.user)
    async def modping(self,ctx):
        if not self.bot.config['enable_logging']:
            return await ctx.send('Modping is disabled, contact your instance\'s owner.')

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

        hook_id = self.bot.db['rooms'][room][f'{self.bot.config["home_guild"]}'][0]
        guild = self.bot.get_guild(self.bot.config['home_guild'])
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
                await ch.send(f'<@&{role}> **{author}** ({ctx.author.id}) needs your help!\n\nSent from server **{ctx.guild.name}** ({ctx.guild.id})',allowed_mentions=nextcord.AllowedMentions(roles=True,everyone=False,users=False))
                return await ctx.send('Moderators called!')

        await ctx.send('It appears the home guild has configured Unifier wrong, and I cannot ping its UniChat moderators.')

    @modping.error
    async def modping_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            t = int(error.retry_after)
            await ctx.send(f'You\'ve recently pinged the moderators, try again in **{t//60}** minutes and **{t%60}** seconds.')
        else:
            await ctx.send('Something went wrong pinging moderators. Please contact the developers.')

    @commands.command(description='Deletes a message.')
    async def delete(self, ctx, *, msg_id=None):
        """Deletes all bridged messages. Does not delete the original."""

        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{ctx.author.id}' in list(gbans.keys()):
            banuntil = gbans[f'{ctx.author.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{ctx.author.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{ctx.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{ctx.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{ctx.guild.id}')
                self.bot.db.save_data()
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

        if not ctx.author.id == msg.author_id and not ctx.author.id in self.bot.moderators:
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

    @nextcord.message_command(name='View reactions')
    async def reactions_ctx(self, interaction, msg: nextcord.Message):
        if interaction.user.id in self.bot.db['fullbanned']:
            return
        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{interaction.user.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.user.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.user.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.guild.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.user.id}' in list(gbans.keys()) or f'{interaction.guild.id}' in list(gbans.keys()):
            return await interaction.response.send_message('Your account or your guild is currently **global restricted**.', ephemeral=True)
        msg_id = msg.id

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await interaction.response.send_message('Could not find message in cache!', ephemeral=True)
        text = ''
        for reaction in msg.reactions:
            text = f'{text}{reaction} x{len(msg.reactions[reaction].keys())} '

        if len(text)==0:
            return await interaction.response.send_message('No reactions yet!',ephemeral=True)

        await interaction.response.send_message(text,ephemeral=True)

    @nextcord.message_command(name='Delete message')
    async def delete_ctx(self, interaction, msg: nextcord.Message):
        if interaction.user.id in self.bot.db['fullbanned']:
            return
        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{interaction.user.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.user.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.user.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.guild.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.user.id}' in list(gbans.keys()) or f'{interaction.guild.id}' in list(gbans.keys()):
            return await interaction.response.send_message('Your account or your guild is currently **global restricted**.', ephemeral=True)
        msg_id = msg.id

        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await interaction.response.send_message('Could not find message in cache!',ephemeral=True)

        if not interaction.user.id == msg.author_id and not interaction.user.id in self.bot.moderators:
            return await interaction.response.send_message('You didn\'t send this message!',ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            await self.bot.bridge.delete_parent(msg_id)
            if msg.webhook:
                raise ValueError()
            return await interaction.edit_original_message(
                content='Deleted message (parent deleted, copies will follow)'
            )
        except:
            try:
                deleted = await self.bot.bridge.delete_copies(msg_id)
                return await interaction.edit_original_message(
                    content=f'Deleted message ({deleted} copies deleted)'
                )
            except:
                traceback.print_exc()
                return await interaction.edit_original_message(
                    content='Something went wrong.'
                )

    @nextcord.message_command(name='Report message')
    async def report(self, interaction, msg: nextcord.Message):
        if interaction.user.id in self.bot.db['fullbanned']:
            return
        gbans = self.bot.db['banned']
        ct = time.time()
        if f'{interaction.user.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.user.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.user.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.guild.id}' in list(gbans.keys()):
            banuntil = gbans[f'{interaction.guild.id}']
            if ct >= banuntil and not banuntil == 0:
                self.bot.db['banned'].pop(f'{interaction.guild.id}')
                self.bot.db.save_data()
            else:
                return
        if f'{interaction.user.id}' in list(gbans.keys()) or f'{interaction.guild.id}' in list(gbans.keys()):
            return await interaction.response.send_message('You or your guild is currently **global restricted**.', ephemeral=True)

        if not self.bot.config['enable_logging']:
            return await interaction.response.send_message('Reporting and logging are disabled, contact your instance\'s owner.', ephemeral=True)

        try:
            msgdata = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await interaction.response.send_message('Could not find message in cache!')

        roomname = msgdata.room
        userid = msgdata.author_id
        content = copy.deepcopy(msg.content)  # Prevent tampering w/ original content

        ButtonStyle = nextcord.ButtonStyle
        btns = ui.ActionRow(
            nextcord.ui.Button(style=ButtonStyle.blurple, label='Spam', custom_id=f'spam', disabled=False),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Abuse or harassment', custom_id=f'abuse', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Explicit or dangerous content', custom_id=f'explicit', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Violates other room rules', custom_id=f'other', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Something else', custom_id=f'misc', disabled=False
            )
        )
        btns_abuse = ui.ActionRow(
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Impersonation', custom_id=f'abuse_1', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Harassment', custom_id=f'abuse_2', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Intentional misinformation', custom_id=f'abuse_3', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Derogatory language', custom_id=f'abuse_4', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Other', custom_id=f'abuse_5', disabled=False
            )
        )
        btns_explicit = ui.ActionRow(
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Adult content', custom_id=f'explicit_1', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Graphic/gory content', custom_id=f'explicit_2', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Encouraging real-world harm', custom_id=f'explicit_3', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Illegal content', custom_id=f'explicit_4', disabled=False
            ),
            nextcord.ui.Button(
                style=ButtonStyle.blurple, label='Other', custom_id=f'explicit_5', disabled=False
            )
        )
        btns2 = ui.ActionRow(
            nextcord.ui.Button(style=ButtonStyle.gray, label='Cancel', custom_id=f'cancel', disabled=False)
        )
        components = ui.MessageComponents()
        components.add_rows(btns, btns2)
        msg = await interaction.response.send_message('How does this message violate our rules?', view=components, ephemeral=True)
        msg = await msg.fetch()

        def check(interaction):
            return interaction.user.id == interaction.user.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            try:
                return await interaction.edit_original_message(content='Timed out.', view=None)
            except:
                return

        buttons = msg.components[0].children
        cat = None
        for button in buttons:
            if button.custom_id==interaction.data["custom_id"]:
                cat = button.label
                break

        asked = True
        components = ui.MessageComponents()
        if interaction.data["custom_id"] == 'abuse':
            components.add_rows(btns_abuse, btns2)
            await interaction.response.edit_message(content='In what way?', view=components)
        elif interaction.data["custom_id"] == 'explicit':
            components.add_rows(btns_explicit, btns2)
            await interaction.response.edit_message(content='In what way?', view=components)
        elif interaction.data["custom_id"] == 'cancel':
            return await interaction.response.edit_message(content='Cancelled.', view=None)
        else:
            asked = False
        if asked:
            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
            except:
                try:
                    return await interaction.edit_original_message(content='Timed out.', view=None)
                except:
                    return
            buttons = msg.components[0].children
            cat2 = None
            for button in buttons:
                if button.custom_id == interaction.data["custom_id"]:
                    cat2 = button.label
                    break
            if interaction.data["custom_id"] == 'cancel':
                return await interaction.response.edit_message(content='Cancelled.', view=None)
        else:
            cat2 = 'none'
        self.bot.reports.update({f'{interaction.user.id}_{userid}_{msg.id}': [cat, cat2, content, roomname, msgdata.id]})
        reason = nextcord.ui.TextInput(
            style=nextcord.TextInputStyle.paragraph, label='Additional details',
            placeholder='Add additional context or information that we should know here.',
            required=False
        )
        signature = nextcord.ui.TextInput(
            style=nextcord.TextInputStyle.short, label='Sign with your username',
            placeholder='Sign this only if your report is truthful and in good faith.',
            required=True, min_length=len(interaction.user.name), max_length=len(interaction.user.name)
        )
        modal = nextcord.ui.Modal(title='Report message', custom_id=f'{userid}_{msg.id}', auto_defer=False)
        modal.add_item(reason)
        modal.add_item(signature)
        await interaction.response.send_modal(modal)

    @commands.command(description='Shows your server\'s plugin restriction status.')
    async def serverstatus(self,ctx):
        embed = nextcord.Embed(
            title='Server status',
            description='Your server is not restricted by plugins.',
            color=0x00ff00
        )
        if f'{ctx.guild.id}' in self.bot.bridge.restricted:
            embed.description = 'Your server is currently limited by a plugin.'
            embed.colour = 0xffce00
        await ctx.send(embed=embed)

    @commands.command(description='Shows EXP leaderboard.')
    async def leaderboard(self,ctx):
        expdata = copy.copy(self.bot.db['exp'])
        lb_data = sorted(
            expdata.items(),
            key=lambda x: x[1]['level']+x[1]['progress'],
            reverse=True
        )
        msg = None
        interaction = None
        embed = nextcord.Embed(
            title=f'{self.bot.user.display_name} leaderboard',
            color=self.bot.colors.unifier
        )
        page = 1
        limit = 10
        max_page = math.ceil(len(lb_data) / limit)

        placement_emoji = {
            1: ':first_place:',
            2: ':second_place:',
            3: ':third_place:'
        }

        while True:
            lb = []

            for x in range(limit):
                index = (page-1)*limit + x
                rank = index + 1
                if index >= len(lb_data):
                    break
                user = self.bot.get_user(int(lb_data[index][0]))
                if user:
                    username = user.name
                else:
                    username = '[unknown]'
                lb.append(
                    f'{placement_emoji[rank]} **{username}**: LVL {lb_data[index][1]["level"]}' if rank <= 3 else
                    f'`{rank}.` **{username}**: Level {lb_data[index][1]["level"]}'
                )

            lb_text = '\n'.join(lb)

            embed.description = lb_text

            btns = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji='\U000023EE',
                    custom_id='first',
                    disabled=page==1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji='\U000025C0',
                    custom_id='prev',
                    disabled=page==1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji='\U000025B6',
                    custom_id='next',
                    disabled=page==max_page
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji='\U000023ED',
                    custom_id='last',
                    disabled=page==max_page
                )
            )

            components = ui.MessageComponents()
            components.add_row(btns)

            if not msg:
                msg = await ctx.send(embed=embed,view=components)
            else:
                await interaction.response.edit_message(embed=embed,view=components)

            def check(interaction):
                return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

            try:
                interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
            except:
                for x in range(len(btns.items)):
                    btns.items[x].disabled = True

                components = ui.MessageComponents()
                components.add_row(btns)
                await msg.edit(view=components)
                break

            if interaction.data['custom_id']=='first':
                page = 1
            elif interaction.data['custom_id']=='prev':
                page -= 1
            elif interaction.data['custom_id']=='next':
                page += 1
            elif interaction.data['custom_id']=='last':
                page = max_page

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type==nextcord.InteractionType.component:
            if not 'custom_id' in interaction.data.keys():
                return
            if interaction.data["custom_id"].startswith('rp') and not interaction.user.id in self.bot.moderators:
                return await interaction.response.send_message('buddy you\'re not a global moderator :skull:',ephemeral=True)
            if interaction.data["custom_id"].startswith('rpdelete'):
                msg_id = int(interaction.data["custom_id"].replace('rpdelete_','',1))
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red, label='Delete message',
                        custom_id=f'rpdelete_{interaction.data["custom_id"].split("_")[1]}', disabled=True
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green, label='Mark as reviewed',
                        custom_id=f'rpreview_{interaction.data["custom_id"].split("_")[1]}', disabled=False
                    )
                )
                components = ui.MessageComponents()
                components.add_row(btns)

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
                    await interaction.message.edit(view=components)
                    return await msg_orig.edit('Deleted message (parent deleted, copies will follow)')
                except:
                    try:
                        deleted = await self.bot.bridge.delete_copies(msg_id)
                        await interaction.message.edit(view=components)
                        return await msg_orig.edit(f'Deleted message ({deleted} copies deleted)')
                    except:
                        traceback.print_exc()
                        await msg_orig.edit(content=f'Something went wrong.')
            elif interaction.data["custom_id"].startswith('rpreview_'):
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red, label='Delete message',
                        custom_id=f'rpdelete_{interaction.data["custom_id"].split("_")[1]}', disabled=True
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green, label='Mark as reviewed',
                        custom_id=f'rpreview_{interaction.data["custom_id"].split("_")[1]}', disabled=True
                    )
                )
                components = ui.MessageComponents()
                components.add_row(btns)
                embed = interaction.message.embeds[0]
                embed.color = 0x00ff00
                author = f'@{interaction.user.name}'
                if not interaction.user.discriminator == '0':
                    author = f'{interaction.user.name}#{interaction.user.discriminator}'
                embed.title = f'This report has been reviewed by {author}!'
                await interaction.response.defer(ephemeral=True)
                try:
                    thread = interaction.channel.get_thread(
                        self.bot.db['report_threads'][str(interaction.message.id)]
                    )
                except:
                    thread = None
                if thread:
                    try:
                        await thread.edit(
                            name=f'[DONE] {thread.name}',
                            archived=True
                        )
                    except:
                        try:
                            await thread.send('This report has been reviewed.')
                        except:
                            pass
                    self.bot.db['report_threads'].pop(str(interaction.message.id))
                    self.bot.db.save_data()
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content='Marked thread as reviewed!')
        elif interaction.type == nextcord.InteractionType.modal_submit:
            if not interaction.data['custom_id']==f'{interaction.user.id}_{interaction.message.id}':
                # not a report
                return
            context = interaction.data['components'][0]['components'][0]['value']
            if not interaction.data['components'][1]['components'][0]['value'].lower() == interaction.user.name.lower():
                return
            if context is None or context == '':
                context = 'no context given'
            author = f'@{interaction.user.name}'
            if not interaction.user.discriminator == '0':
                author = f'{interaction.user.name}#{interaction.user.discriminator}'
            try:
                report = self.bot.reports[f'{interaction.user.id}_{interaction.data["custom_id"]}']
            except:
                return await interaction.response.send_message('Something went wrong while submitting the report.',
                                                               ephemeral=True)
            cat = report[0]
            cat2 = report[1]
            content = report[2]
            roomname = report[3]
            msgid = report[4]
            msgdata = await self.bot.bridge.fetch_message(msgid)
            userid = int(interaction.data["custom_id"].split('_')[0])
            if len(content) > 2048:
                content = content[:-(len(content) - 2048)]
            embed = nextcord.Embed(
                title='Message report - content is as follows',
                description=content,
                color=0xffbb00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=f'{cat} => {cat2}', inline=False)
            embed.add_field(name='Context', value=context, inline=False)
            embed.add_field(name="Sender ID", value=str(msgdata.author_id), inline=False)
            embed.add_field(name="Message room", value=roomname, inline=False)
            embed.add_field(name="Message ID", value=str(msgid), inline=False)
            embed.add_field(name="Reporter ID", value=str(interaction.user.id), inline=False)
            try:
                embed.set_footer(text=f'Submitted by {author} - please do not disclose actions taken against the user.',
                                 icon_url=interaction.user.avatar.url)
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
            guild = self.bot.get_guild(self.bot.config['home_guild'])
            ch = guild.get_channel(self.bot.config['reports_channel'])
            btns = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red, label='Delete message', custom_id=f'rpdelete_{msgid}',
                    disabled=False),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green, label='Mark as reviewed', custom_id=f'rpreview_{msgid}',
                    disabled=False
                )
            )
            components = ui.MessageComponents()
            components.add_row(btns)
            msg: nextcord.Message = await ch.send(
                f'<@&{self.bot.config["moderator_role"]}>', embed=embed, view=components
            )
            try:
                thread = await msg.create_thread(
                    name=f'Discussion: #{msgid}',
                    auto_archive_duration=10080
                )
                self.bot.db['report_threads'].update({str(msg.id): thread.id})
                self.bot.db.save_data()
            except:
                pass
            self.bot.reports.pop(f'{interaction.user.id}_{interaction.data["custom_id"]}')
            return await interaction.response.send_message(
                "# :white_check_mark: Your report was submitted!\nThanks for your report! Our moderators will have a look at it, then decide what to do.\nFor privacy reasons, we will not disclose actions taken against the user.",
                ephemeral=True)

    @commands.command(hidden=True,description='Registers commands.')
    async def forcereg(self, ctx, *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return
        if 'dereg' in args:
            await self.bot.delete_application_commands(*self.bot.get_all_application_commands())
            return await ctx.send('gone, reduced to atoms (hopefully)')
        await self.bot.sync_application_commands()
        return await ctx.send(f'Registered commands to bot')

    @commands.command(hidden=True,description='Initializes new UnifierBridge object.')
    async def initbridge(self, ctx, *, args=''):
        if not ctx.author.id == self.bot.config['owner']:
            return
        msgs = []
        prs = {}
        if 'preserve' in args:
            msgs = self.bot.bridge.bridged
            prs = self.bot.bridge.prs
        del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot, self.logger)
        if 'preserve' in args:
            self.bot.bridge.bridged = msgs
            self.bot.bridge.prs = prs
        await ctx.send('Bridge initialized')

    @commands.command(hidden=True,description='Sends a message as system.')
    async def system(self, ctx, room):
        if not ctx.author.id == self.bot.config['owner']:
            return
        ctx.message.content = ctx.message.content.replace(f'{self.bot.command_prefix}system {room}','',1)
        await self.bot.bridge.send(room,ctx.message,'discord',system=True)
        for platform in self.bot.config['external']:
            await self.bot.bridge.send(room, ctx.message, platform, system=True)
        await ctx.send('Sent as system')

    @commands.Cog.listener()
    async def on_message(self, message):
        author_rp = message.author
        content_rp = message.content

        extbridge = False
        hook = None
        idmatch = False

        if message.author.id in self.bot.db['fullbanned']:
            return

        if message.author.id==self.bot.config['owner'] and message.content.startswith('--match '):
            message.content = message.content.replace('--match ','',1)
            idmatch = True

        if not message.webhook_id == None:
            # webhook msg
            try:
                hook = await self.bot.fetch_webhook(message.webhook_id)
                extbridge = True
                if not hook.user.id in self.bot.db['external_bridge'] or hook.user.id==self.bot.user.id:
                    raise ValueError()
            except:
                return

        if message.guild == None:
            return

        if len(message.content)==0 and len(message.embeds)==0 and len(message.attachments)==0:
            return

        if message.content.startswith(self.bot.command_prefix) and not message.author.bot:
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
                    self.bot.db.save_data()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.save_data()
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

        message = await self.bot.bridge.run_stylizing(message)
        unsafe, responses = await self.bot.bridge.run_security(message)
        if unsafe:
            if f'{message.author.id}' in list(self.bot.db['banned'].keys()):
                return

            banned = {}
            restricted = []
            public = False
            public_reason = None

            for plugin_name in responses:
                response = responses[plugin_name]
                for user in response['target']:
                    if user in banned.keys():
                        if response['target'][user] > 0 or banned[user]==0:
                            continue
                    if not int(user) == self.bot.config['owner']:
                        if response['target'][user]==0:
                            self.bot.db['banned'].update({user:0})
                            self.bot.db.save_data()
                        else:
                            self.bot.bridge.secbans.update(
                                {user:round(time.time())+response['target'][user]}
                            )
                    banned.update({user: response['target'][user]})
                for guild in response['restrict']:
                    if guild in restricted:
                        continue
                    self.bot.restricted.update({guild:round(time.time())+response['restrict'][guild]})
                    restricted.append(guild)
                if 'public' in responses.keys() and not public:
                    if response['public']:
                        public_reason = response['description']
                        public = True

            embed = nextcord.Embed(
                title='Content blocked',
                description='Your message was blocked. Moderators may be able to see the blocked content.',
                color=0xff0000
            )

            if public:
                embed.add_field(name='Reason',value=public_reason if public_reason else '[unknown]',inline=False)

            await message.channel.send(embed=embed)

            embed = nextcord.Embed(
                title='Content blocked - content is as follows',
                description=message.content[:-(len(message.content)-2000)] if len(message.content) > 2000 else message.content,
                color=0xff0000,
                timestamp=datetime.utcnow()
            )

            for plugin in responses:
                if not responses[plugin]['unsafe']:
                    continue
                try:
                    with open('plugins/' + plugin + '.json') as file:
                        extinfo = json.load(file)
                    plugname = extinfo['name']
                except:
                    plugname = plugin
                embed.add_field(
                    name=plugname + f' ({len(responses[plugin]["target"])} users involved)',
                    value=responses[plugin]['description'],
                    inline=False
                )
                if len(embed.fields) == 23:
                    break

            embed.add_field(name='Punished user IDs', value=' '.join(list(banned.keys())), inline=False)
            embed.add_field(name='Message room', value=roomname, inline=False)
            embed.set_footer(
                text='This is an automated action performed by a plugin, always double-check before taking action',
                icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )

            try:
                ch = self.bot.get_guild(self.bot.config['home_guild']).get_channel(self.bot.config['reports_channel'])
                await ch.send(f'<@&{self.bot.config["moderator_role"]}>',embed=embed)
            except:
                pass

            for user in banned:
                user_obj = self.bot.get_user(int(user))
                if int(user)==self.bot.config['owner']:
                    try:
                        await user_obj.send('just as a fyi: this would have banned you')
                    except:
                        pass
                    continue
                nt = time.time() + banned[user]
                embed = nextcord.Embed(
                    title=f'You\'ve been __global restricted__ by @Unifier (system)!',
                    description='Automatic action carried out by security plugins',
                    color=0xffcc00,
                    timestamp=datetime.utcnow()
                )
                embed.set_author(
                    name='@Unifier (system)',
                    icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                )
                if banned[user]==0:
                    embed.colour = 0xff0000
                    embed.add_field(
                        name='Actions taken',
                        value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',
                        inline=False
                    )
                else:
                    embed.add_field(
                        name='Actions taken',
                        value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{round(nt)}:f>. This will expire <t:{round(nt)}:R>.',
                        inline=False
                    )
                try:
                    await user_obj.send(embed=embed)
                except:
                    pass

            return

        if f'{message.author.id}' in list(self.bot.bridge.secbans.keys()):
            if self.bot.bridge.secbans[f'{message.author.id}'] > time.time():
                self.bot.bridge.secbans.pop(f'{message.author.id}')
            else:
                return

        if f'{message.guild.id}' in list(self.bot.bridge.restricted.keys()):
            if self.bot.bridge.restricted[f'{message.guild.id}'] > time.time():
                self.bot.bridge.restricted.pop(f'{message.guild.id}')
            else:
                if len(message.content) > self.bot.config['restriction_length']:
                    return await message.channel.send(
                        ('Your server is currently limited for security. The maximum character limit for now is **'+
                            self.bot.config["restriction_length"]+' characters**.')
                    )
                elif self.bot.bridge.cooldowned[f'{message.author.id}'] < time.time():
                    return await message.channel.send(
                        'Your server is currently limited for security. Please wait before sending another message.'
                    )

        multisend = True
        if message.content.startswith('['):
            parts = message.content.replace('[','',1).replace('\n',' ').split('] ',1)
            if len(parts) > 1 and len(parts[0])==6:
                if (parts[0].lower()=='newest' or parts[0].lower()=='recent' or
                        parts[0].lower() == 'latest'):
                    multisend = False
                elif parts[0].lower() in list(self.bot.bridge.prs.keys()):
                    multisend = False

        pr_roomname = self.bot.config['posts_room']
        pr_ref_roomname = self.bot.config['posts_ref_room']
        is_pr = roomname == pr_roomname and (
                self.bot.config['allow_prs'] if 'allow_prs' in list(self.bot.config.keys()) else False or
                self.bot.config['allow_posts'] if 'allow_posts' in list(self.bot.config.keys()) else False
        )
        is_pr_ref = roomname == pr_ref_roomname and (
            self.bot.config['allow_prs'] if 'allow_prs' in list(self.bot.config.keys()) else False or
            self.bot.config['allow_posts'] if 'allow_posts' in list(self.bot.config.keys()) else False
        )

        should_resend = False

        if '[emoji:' in message.content or is_pr or is_pr_ref:
            multisend = False
            should_resend = True

        tasks = []
        parent_id = None

        if (message.content.lower().startswith('is unifier down') or
                message.content.lower().startswith('unifier not working')):
            await message.channel.send('no',reference=message)

        if multisend:
            # Multisend
            # Sends Discord message along with other platforms to minimize
            # latency on external platforms.
            self.bot.bridge.bridged.append(UnifierMessage(
                    author_id=message.author.id if not extbridge else hook.user.id,
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    original=message.id,
                    copies={},
                    external_copies={},
                    urls={},
                    source='discord',
                    room=roomname,
                    external_urls={},
                    external_bridged=extbridge
                )
            )
            tasks.append(self.bot.bridge.send(room=roomname,message=message,platform='discord', extbridge=extbridge))
        else:
            parent_id = await self.bot.bridge.send(room=roomname, message=message, platform='discord', extbridge=extbridge)

        for platform in self.bot.config['external']:
            if should_resend and parent_id==message.id:
                tasks.append(self.bot.loop.create_task(self.bot.bridge.send(
                    room=roomname, message=message, platform=platform, extbridge=extbridge, id_override=parent_id
                )))
            else:
                tasks.append(self.bot.loop.create_task(
                    self.bot.bridge.send(room=roomname, message=message, platform=platform, extbridge=extbridge)))

        ids = []
        try:
            ids = await asyncio.gather(*tasks)
        except:
            self.logger.exception('Something went wrong!')
            experiments = []
            for experiment in self.bot.db['experiments']:
                if message.guild.id in self.bot.db['experiments'][experiment]:
                    experiments.append(experiment)
            self.logger.info(f'Experiments: {experiments}')
            pass

        if idmatch:
            if not ids:
                return await message.channel.send('Could not get message IDs.')
            if parent_id:
                ids.append(parent_id)
            if len(list(set(ids)))==1:
                await message.channel.send('All IDs match. ID: '+str(ids[0]))
            else:
                text = ''
                for msgid in ids:
                    text = text + f'\n{msgid}'
                await message.channel.send('Mismatch detected.'+text)

        _newexp, levelup = await self.bot.bridge.add_exp(message.author.id)

        if levelup:
            level = self.bot.db['exp'][f'{message.author.id}']['level']
            embed = nextcord.Embed(
                title=f'Level {level-1} => __Level {level}__',
                color=self.bot.colors.blurple
            )
            embed.set_author(
                name=f'@{message.author.global_name} leveled up!',
                icon_url=message.author.avatar.url if message.author.avatar else None
            )
            await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content == after.content:
            return

        message = after

        if message.author.id in self.bot.db['fullbanned']:
            return

        if message.guild == None:
            return

        gbans = self.bot.db['banned']

        if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
            ct = time.time()
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    self.bot.db.save_data()
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    self.bot.db.save_data()
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
    async def on_raw_message_edit(self,payload):
        if payload.cached_message:
            # on_message_edit should handle this
            return
        else:
            ch = self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
            message = await ch.fetch_message(payload.message_id)

            if message.author.id in self.bot.db['fullbanned']:
                return

            if message.guild == None:
                return

            gbans = self.bot.db['banned']

            if f'{message.author.id}' in list(gbans.keys()) or f'{message.guild.id}' in list(gbans.keys()):
                ct = time.time()
                if f'{message.author.id}' in list(gbans.keys()):
                    banuntil = gbans[f'{message.author.id}']
                    if ct >= banuntil and not banuntil == 0:
                        self.bot.db['banned'].pop(f'{message.author.id}')
                        self.bot.db.save_data()
                    else:
                        return
                if f'{message.guild.id}' in list(gbans.keys()):
                    banuntil = gbans[f'{message.guild.id}']
                    if ct >= banuntil and not banuntil == 0:
                        self.bot.db['banned'].pop(f'{message.guild.id}')
                        self.bot.db.save_data()
                    else:
                        return

            if not message.webhook_id == None:
                # webhook msg, dont bother
                return

            if message.author.id == self.bot.user.id:
                return

            hooks = await message.channel.webhooks()
            found = False
            origin_room = 0  # keeping this in case i decide to log this

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
                if not str(msg.id) == str(message.id):
                    raise ValueError()
            except:
                return

            await self.bot.bridge.edit(msg.id, message.content)

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
            if not self.bot.config['enable_logging']:
                raise RuntimeError()
            guild = self.bot.get_guild(self.bot.config['home_guild'])
            ch = guild.get_channel(self.bot.config['logs_channel'])

            content = message.content

            if len(message.content) == 0:
                content = '[no content]'
            embed = nextcord.Embed(title=f'Message deleted from `{roomname}`', description=content)
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event):
        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(event.message_id)
        except:
            return

        if event.user_id in self.bot.db['fullbanned']:
            return

        emoji = event.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        else:
            emoji = f'<:{emoji.name}:{emoji.id}>'

        await msg.add_reaction(emoji, event.user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event):
        try:
            msg: UnifierMessage = await self.bot.bridge.fetch_message(event.message_id)
        except:
            return

        if event.user_id in self.bot.db['fullbanned']:
            return

        emoji = event.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        else:
            emoji = f'<:{emoji.name}:{emoji.id}>'

        await msg.remove_reaction(emoji, event.user_id)

def setup(bot):
    bot.add_cog(Bridge(bot))
