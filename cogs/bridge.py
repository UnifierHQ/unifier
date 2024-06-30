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
import datetime
import random
import string
import copy
import ujson as json
import compress_json
import re
import ast
import math
from io import BytesIO
import os
from utils import log, langmgr, ui, restrictions as r
import importlib
import emoji as pymoji

mentions = nextcord.AllowedMentions(everyone=False, roles=False, users=False)
restrictions = r.Restrictions()
language = langmgr.placeholder()

multisend_logs = []
plugin_data = {}
level_cooldown = {}

dedupe_emojis = [
    '\U0001F7E5',
    '\U0001F7E7',
    '\U0001F7E8',
    '\U0001F7E9',
    '\U0001F7E6',
    '\U0001F7EA',
    '\U0001F7EB',
    '\U00002B1C',
    '\U00002B1B'
]

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
        self.webhook_cache = webhook_cache or WebhookCacheStore(self.bot)
        self.restored = False
        self.raidbans = {}
        self.possible_raid = {}
        self.logger = logger
        self.secbans = {}
        self.restricted = {}
        self.backup_running = False
        self.backup_lock = False
        self.msg_stats = {}
        self.msg_stats_reset = datetime.datetime.now().day
        self.dedupe = {}

    class UnifierMessage:
        def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room,
                     external_urls=None, webhook=False, prehook=None, reply=False, external_bridged=False,
                     reactions=None,
                     thread=None):
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
            self.external_bridged = external_bridged,
            self.thread = thread
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
            if guild_id == self.guild_id:
                return f'https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.id}'

            return self.urls[guild_id]

        async def add_reaction(self, emoji, userid, platform=None):
            userid = str(userid)
            platform = ('revolt' if emoji.startswith('<r:') else 'discord') if not platform else platform
            if not emoji in list(self.reactions.keys()):
                self.reactions.update({emoji: {}})
            if not userid in list(self.reactions[emoji].keys()):
                self.reactions[emoji].update({userid: [0, platform]})
            self.reactions[emoji][userid][0] += 1
            return self.reactions[emoji][userid][0]

        async def remove_reaction(self, emoji, userid):
            try:
                userid = str(userid)
                self.reactions[emoji][userid][0] -= 1
            except:
                return 0
            if self.reactions[emoji][userid][0] <= 0:
                self.reactions[emoji].pop(userid)

                total = 0
                for user in self.reactions[emoji]:
                    total += self.reactions[emoji][user][0]

                if total == 0:
                    self.reactions.pop(emoji)

                return 0
            else:
                return self.reactions[emoji][userid][0]

        async def fetch_external_url(self, source, guild_id):
            return self.external_urls[source][guild_id]

        async def fetch_external(self, platform: str, guild_id: str):
            return ExternalReference(guild_id, self.external_copies[platform][str(guild_id)][0],
                                     self.external_copies[platform][str(guild_id)][1])

    def add_modlog(self, action_type, user, reason, moderator):
        t = time.time()
        try:
            self.bot.db['modlogs'][f'{user}'].append({
                'type': action_type,
                'reason': reason,
                'time': t,
                'mod': moderator
            })
        except:
            self.bot.db['modlogs'].update({
                f'{user}': [{
                    'type': action_type,
                    'reason': reason,
                    'time': t,
                    'mod': moderator
                }]
            })
        self.bot.db.save_data()

    def get_modlogs(self, user):
        t = time.time()

        if not f'{user}' in list(self.bot.db['modlogs'].keys()):
            return {
                'warns': [],
                'bans': []
            }, {
                'warns': [],
                'bans': []
            }

        actions = {
            'warns': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 0],
            'bans': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 1]
        }
        actions_recent = {
            'warns': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 0 and t - log['time'] <= 2592000],
            'bans': [log for log in self.bot.db['modlogs'][f'{user}'] if log['type'] == 1 and t - log['time'] <= 2592000]
        }

        return actions, actions_recent

    def get_modlogs_count(self, user):
        actions, actions_recent = self.get_modlogs(user)
        return {
            'warns': len(actions['warns']), 'bans': len(actions['bans'])
        }, {
            'warns': len(actions_recent['warns']), 'bans': len(actions_recent['bans'])
        }

    async def optimize(self):
        """Optimizes data to avoid having to fetch webhooks.
        This decreases latency incuded by message bridging prep."""
        for room in self.bot.db['rooms']:
            for guild in self.bot.db['rooms'][room]:
                if len(self.bot.db['rooms'][room][guild])==1:
                    try:
                        hook = await self.bot.fetch_webhook(self.bot.db['rooms'][room][guild][0])
                    except:
                        continue
                    self.bot.db['rooms'][room][guild].append(hook.channel_id)
        self.bot.db.save_data()

    def is_raidban(self,userid):
        try:
            ban: UnifierRaidBan = self.raidbans[f'{userid}']
        except:
            return False
        return ban.is_banned()

    def raidban(self,userid):
        self.raidbans.update({f'{userid}':UnifierRaidBan()})

    async def backup(self,filename='bridge.json',limit=10000):
        if self.backup_lock:
            return

        self.backup_running = True

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
            await self.bot.loop.run_in_executor(None, lambda: compress_json.dump(data,filename+'.lzma'))
        else:
            with open(filename, "w+") as file:
                await self.bot.loop.run_in_executor(None, lambda: json.dump(data, file))
        del data
        self.backup_running = False
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
            msg = UnifierBridge.UnifierMessage(
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

    async def find_thread(self,thread_id):
        for thread in self.bot.db['threads']:
            if int(thread)==thread_id or int(thread_id) in self.bot.db['threads'][thread].values():
                return {thread: self.bot.db['threads'][thread]}
        return None

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
        msg_tomerge: UnifierBridge.UnifierMessage = await self.fetch_message(message_id,not_prehook=True)
        self.bridged[index]['copies'] = self.bridged[index]['copies'] | msg_tomerge.copies
        self.bridged[index]['external_copies'] = self.bridged[index]['external_copies'] | msg_tomerge.external_copies
        self.bridged[index]['urls'] = self.bridged[index]['urls'] | msg_tomerge.urls
        self.bridged.pop(index_tomerge)

    async def add_exp(self, user_id):
        if not self.bot.config['enable_exp'] or user_id==self.bot.user.id:
            return 0, False
        if not f'{user_id}' in self.bot.db['exp'].keys():
            self.bot.db['exp'].update({f'{user_id}':{'experience':0,'level':1,'progress':0}})
        t = time.time()
        if f'{user_id}' in level_cooldown.keys():
            if t < level_cooldown[f'{user_id}']:
                return self.bot.db['exp'][f'{user_id}']['experience'], self.bot.db['exp'][f'{user_id}']['progress'] >= 1
            else:
                level_cooldown[f'{user_id}'] = round(time.time()) + self.bot.config['exp_cooldown']
        else:
            level_cooldown.update({f'{user_id}': round(time.time()) + self.bot.config['exp_cooldown']})
        self.bot.db['exp'][f'{user_id}']['experience'] += random.randint(80,120)
        ratio, remaining = await self.progression(user_id)
        if ratio >= 1:
            self.bot.db['exp'][f'{user_id}']['experience'] = -remaining
            self.bot.db['exp'][f'{user_id}']['level'] += 1
            newratio, _remaining = await self.progression(user_id)
        else:
            newratio = ratio
        self.bot.db['exp'][f'{user_id}']['progress'] = newratio
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        return self.bot.db['exp'][f'{user_id}']['experience'], ratio >= 1

    async def progression(self, user_id):
        base = 1000
        rate = 1.4
        target = base * (rate ** self.bot.db['exp'][f'{user_id}']['level'])
        return (
            self.bot.db['exp'][f'{user_id}']['experience']/target, target-self.bot.db['exp'][f'{user_id}']['experience']
        )

    async def roomstats(self, roomname):
        online = 0
        members = 0
        guilds = 0
        for guild_id in self.bot.db['rooms'][roomname]:
            try:
                guild = self.bot.get_guild(int(guild_id))
                online += len(list(
                    filter(lambda x: (x.status != nextcord.Status.offline and x.status != nextcord.Status.invisible),
                           guild.members)))
                members += len(guild.members)
                guilds += 1
            except:
                pass
        try:
            messages = self.msg_stats[roomname]
        except:
            messages = 0
        return {
            'online': online, 'members': members, 'guilds': guilds, 'messages': messages
        }

    async def dedupe_name(self, username, userid):
        if not username in self.dedupe.keys():
            self.dedupe.update({username:[userid]})
            return -1
        if not userid in self.dedupe[username]:
            self.dedupe[username].append(userid)
        if self.dedupe[username].index(userid)-1 >= len(dedupe_emojis):
            return len(self.dedupe[username])-1
        return self.dedupe[username].index(userid)-1

    async def delete_parent(self, message):
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message)
        if msg.source=='discord':
            ch = self.bot.get_channel(int(msg.channel_id))
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
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message)
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
                        webhook = self.bot.bridge.webhook_cache.get_webhook([
                            f'{self.bot.db["rooms"][msg.room][f"{guild.id}"][0]}'
                        ])
                    except:
                        try:
                            webhook = await self.bot.fetch_webhook(self.bot.db['rooms'][msg.room][key][0])
                            self.bot.bridge.webhook_cache.store_webhook(webhook)
                        except:
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

    async def make_friendly(self, text, source):
        if source=='discord':
            if (text.startswith('<:') or text.startswith('<a:')) and text.endswith('>'):
                try:
                    emoji_name = text.split(':')[1]
                    emoji_id = int(text.split(':')[2].replace('>','',1))
                    return f'[emoji ({emoji_name})](https://cdn.discordapp.com/emojis/{emoji_id}.webp?size=48&quality=lossless)'
                except:
                    pass
        elif source=='revolt':
            if text.startswith(':') and text.endswith(':'):
                try:
                    emoji_id = text.replace(':','',1)[:-1]
                    if len(emoji_id) == 26:
                        return f'[emoji](https://autumn.revolt.chat/emojis/{emoji_id}?size=48)'
                except:
                    pass

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
                if source == 'revolt':
                    user = self.bot.revolt_client.get_user(userid)
                    display_name = user.display_name
                elif source == 'guilded':
                    user = self.bot.guilded_client.get_user(userid)
                    display_name = user.display_name
                else:
                    user = self.bot.get_user(userid)
                    display_name = user.global_name
                if not user:
                    raise ValueError()
            except:
                offset += 1
                continue
            text = text.replace(f'<@{userid}>', f'@{display_name or user.name}').replace(
                f'<@!{userid}>', f'@{display_name or user.name}')
            offset += 1

        components = text.split('<#')
        offset = 0
        if text.startswith('<#'):
            offset = 1

        while offset < len(components):
            if len(components) == 1 and offset == 0:
                break
            try:
                channelid = int(components[offset].split('>', 1)[0])
            except:
                channelid = components[offset].split('>', 1)[0]
            try:
                if source == 'revolt':
                    try:
                        channel = self.bot.revolt_client.get_channel(channelid)
                    except:
                        channel = await self.bot.revolt_client.fetch_channel(channelid)
                elif source == 'guilded':
                    channel = self.bot.guilded_client.get_channel(channelid)
                else:
                    channel = self.bot.get_channel(channelid)
                if not channel:
                    raise ValueError()
            except:
                offset += 1
                continue
            text = text.replace(f'<#{channelid}>', f'#{channel.name}').replace(
                f'<#!{channelid}>', f'#{channel.name}')
            offset += 1

        components = text.split('<:')
        offset = 0
        if text.startswith('<:'):
            offset = 1

        while offset < len(components):
            if len(components) == 1 and offset == 0:
                break
            emojiname = components[offset].split(':', 1)[0]
            emojiafter = components[offset].split(':', 1)[1].split('>')[0]+'>'
            text = text.replace(f'<:{emojiname}:{emojiafter}', f':{emojiname}\\:')
            offset += 1

        components = text.split('<a:')
        offset = 0
        if text.startswith('<a:'):
            offset = 1

        while offset < len(components):
            if len(components) == 1 and offset == 0:
                break
            emojiname = components[offset].split(':', 1)[0]
            emojiafter = components[offset].split(':', 1)[1].split('>')[0] + '>'
            text = text.replace(f'<a:{emojiname}:{emojiafter}', f':{emojiname}\\:')
            offset += 1

        return text

    async def edit(self, message, content):
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message)
        threads = []

        async def edit_discord(msgs,friendly=False):
            threads = []

            if friendly:
                text = await self.make_friendly(content, msg.source)
            else:
                text = content

            for key in list(self.bot.db['rooms'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                # Fetch webhook
                try:
                    webhook = await self.bot.fetch_webhook(self.bot.db['rooms'][msg.room][key][0])
                except:
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
                text = await self.make_friendly(content, msg.source)
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
            """Guilded does not support editing via webhooks at the moment.
            We're just keeping this in case they change this at some point."""

            threads = []
            if friendly:
                text = await self.make_friendly(content, msg.source)
            else:
                text = content

            for key in list(self.bot.db['rooms_guilded'][msg.room].keys()):
                if not key in list(msgs.keys()):
                    continue

                # Fetch webhook
                try:
                    webhook = await self.bot.guilded_client.fetch_webhook(self.bot.db['rooms_guilded'][msg.room][key][0])
                except:
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

        # Check if message can be deleted
        if should_resend:
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                if emojified or is_pr_ref:
                    await message.channel.send(
                        'Parent message could not be deleted. I may be missing the `Manage Messages` permission.')
                    raise SelfDeleteException('Could not delete parent message')
                elif is_pr:
                    await message.channel.send(f'Post ID assigned: `{pr_id}`', reference=message)
                should_resend = False
        elif is_pr and source == platform:
            if source == 'revolt':
                await message.channel.send(f'Post ID assigned: `{pr_id}`', replies=[revolt.MessageReply(message)])
            elif source == 'guilded':
                await message.channel.send(f'Post ID assigned: `{pr_id}`', reply_to=[message])

        # Username
        if source == 'revolt':
            if not message.author.display_name:
                author = message.author.name
            else:
                author = message.author.display_name
        elif source == 'guilded':
            author = message.author.name
        else:
            author = message.author.global_name if message.author.global_name else message.author.name
        if f'{message.author.id}' in list(self.bot.db['nicknames'].keys()):
            author = self.bot.db['nicknames'][f'{message.author.id}']

        # Get dedupe
        dedupe = await self.dedupe_name(author, message.author.id)
        should_dedupe = dedupe > -1

        # Emoji time
        useremoji = None
        if self.bot.config['enable_emoji_tags'] and not system:
            while True:
                author_split = [*author]
                if len(author_split) == 1:
                    if source == 'guilded':
                        author = 'Moderated username'
                    else:
                        author = message.author.name
                    break
                if pymoji.is_emoji(author_split[len(author_split)-1]):
                    author_split.pop(len(author_split)-1)
                    author = ''.join(author_split)
                    while author.endswith(' '):
                        author = author[:-1]
                else:
                    break
            if (
                    message.author.id == self.bot.config['owner'] or (
                            message.author.id == self.bot.config['owner_external'][source]
                            if source in self.bot.config['owner_external'].keys() else False
                    )
            ):
                useremoji = '\U0001F451'
            elif message.author.id in self.bot.admins:
                useremoji = '\U0001F510'
            elif message.author.id in self.bot.moderators:
                useremoji = '\U0001F6E1'
            elif message.author.id in self.bot.db['trusted']:
                useremoji = '\U0001F31F'
            elif message.author.bot:
                useremoji = '\U0001F916'
            elif should_dedupe:
                useremoji = dedupe_emojis[dedupe]

        friendlified = False
        friendly_content = None
        if not source == platform:
            friendlified = True
            friendly_content = await self.make_friendly(message.content, source)

        message_ids = {}
        urls = {}
        trimmed = ''
        replying = False

        # Threading
        thread_urls = {}
        threads = []
        tb_v2 = source=='discord'
        size_total = 0
        max_files = 0

        # Check attachments size
        for attachment in message.attachments:
            if system:
                break
            size_total += attachment.size
            if size_total > 25000000:
                if source == platform == 'revolt':
                    await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                               replies=[revolt.MessageReply(message)])
                elif source == platform == 'guilded':
                    await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                               reply_to=message)
                elif source == platform:
                    await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                               reference=message)
                break
            max_files += 1

        # Broadcast message
        for guild in list(guilds.keys()):
            if source=='revolt' or source=='guilded':
                sameguild = (guild == str(message.server.id)) if message.server else False
            else:
                sameguild = (guild == str(message.guild.id)) if message.guild else False

            try:
                bans = self.bot.db['blocked'][str(guild)]
                if source=='discord':
                    guildban = message.guild.id in bans
                else:
                    guildban = message.server.id in bans
                if (message.author.id in bans or guildban) and not sameguild:
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
                    if True: # message.thread:
                        # i probably want to research how nextcord threads work first, will come back to this
                        pass
                    if not trimmed:
                        is_copy = False
                        try:
                            if source=='revolt':
                                content = message.replies[0].content
                            else:
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
                            author_text = f'@{user.display_name or user.name}'
                        elif reply_msg.source=='guilded':
                            user = self.bot.guilded_client.get_user(reply_msg.author_id)
                            author_text = f'@{user.name}'
                        else:
                            user = self.bot.get_user(int(reply_msg.author_id))
                            author_text = f'@{user.global_name or user.name}'
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
            async def get_files(attachments):
                files = []

                async def to_file(source_file):
                    if platform == 'discord':
                        if source == 'discord':
                            try:
                                return await source_file.to_file(use_cached=True, spoiler=source_file.is_spoiler())
                            except:
                                try:
                                    return await source_file.to_file(use_cached=True, spoiler=False)
                                except:
                                    return await source_file.to_file(use_cached=False, spoiler=False)
                        elif source == 'revolt':
                            filebytes = await source_file.read()
                            return nextcord.File(fp=BytesIO(filebytes), filename=source_file.filename)
                        elif source == 'guilded':
                            tempfile = await source_file.to_file()
                            return nextcord.File(fp=tempfile.fp, filename=source_file.filename)
                    elif platform == 'revolt':
                        if source == 'discord':
                            f = await source_file.to_file(use_cached=True)
                            return revolt.File(f.fp.read(), filename=f.filename)
                        elif source == 'guilded':
                            f = await source_file.to_file()
                            return revolt.File(f.fp.read(), filename=f.filename)
                        elif source == 'revolt':
                            filebytes = await source_file.read()
                            return revolt.File(filebytes, filename=source_file.filename)
                    elif platform == 'guilded':
                        if source == 'guilded':
                            try:
                                return await source_file.to_file()
                            except:
                                return await source_file.to_file()
                        elif source == 'revolt':
                            filebytes = await source_file.read()
                            return guilded.File(fp=BytesIO(filebytes), filename=source_file.filename)
                        elif source == 'discord':
                            tempfile = await source_file.to_file(use_cached=True)
                            return guilded.File(fp=tempfile.fp, filename=source_file.filename)

                index = 0
                for attachment in attachments:
                    if system:
                        break
                    if source == 'guilded':
                        if not attachment.file_type.image and not attachment.file_type.video:
                            continue
                    else:
                        if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                                not 'image' in attachment.content_type and not 'text/plain' in attachment.content_type and
                                self.bot.config['safe_filetypes']) or attachment.size > 25000000:
                            continue
                    files.append(await to_file(attachment))
                    index += 1
                    if index >= max_files:
                        break

                return files

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
                msg_author = self.bot.user.global_name if self.bot.user.global_name else self.bot.user.name + ' (system)'

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
                    if useremoji:
                        msg_author_dc = msg_author[:-2]

                if useremoji:
                    msg_author_dc = msg_author_dc + ' ' + useremoji

                webhook = None
                try:
                    webhook = self.bot.bridge.webhook_cache.get_webhook(
                        f'{self.bot.db["rooms"][room][guild][0]}'
                    )
                except:
                    # It'd be better to fetch all instead of individual webhooks here, so they can all be cached
                    hooks = await destguild.webhooks()
                    self.bot.bridge.webhook_cache.store_webhooks(hooks)
                    for hook in hooks:
                        if hook.id in self.bot.db['rooms'][room][guild]:
                            webhook = hook
                            break
                if not webhook:
                    continue

                async def tbsend(webhook,url,msg_author_dc,embeds,message,mentions,components,sameguild,
                                 destguild):
                    try:
                        files = await get_files(message.attachments)
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=friendly_content if friendlified else message.content,
                                                 files=files, allowed_mentions=mentions, view=(
                                                     components if components and not system else ui.MessageComponents()
                                                 ), wait=True)
                    except:
                        return None
                    tbresult = [
                        {f'{destguild.id}': [webhook.channel.id, msg.id]},
                        {f'{destguild.id}': f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'},
                        [sameguild, msg.id]
                    ]
                    return tbresult

                if tb_v2:
                    threads.append(asyncio.create_task(tbsend(webhook,url,msg_author_dc,embeds,message,
                                                              mentions,components,sameguild,
                                                              destguild)))
                else:
                    try:
                        files = await get_files(message.attachments)
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=friendly_content if friendlified else message.content,
                                                 files=files, allowed_mentions=mentions, view=(
                                                     components if components and not system else ui.MessageComponents()
                                                 ), wait=True)
                    except:
                        continue
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
                    if useremoji:
                        msg_author_rv = msg_author[:-2]

                if useremoji:
                    msg_author_rv = msg_author_rv + ' ' + useremoji

                try:
                    persona = revolt.Masquerade(name=msg_author_rv, avatar=url, colour=rvtcolor)
                except:
                    persona = revolt.Masquerade(name=msg_author_rv, avatar=None, colour=rvtcolor)
                try:
                    files = await get_files(message.attachments)
                    msg = await ch.send(
                        content=friendly_content if friendlified else message.content, embeds=message.embeds,
                        attachments=files, replies=replies, masquerade=persona
                    )
                except:
                    continue

                message_ids.update({destguild.id:[ch.id,msg.id]})
            elif platform=='guilded':
                try:
                    webhook = self.bot.bridge.webhook_cache.get_webhook([f'{self.bot.db["rooms_guilded"][room][guild][0]}'])
                except:
                    try:
                        webhook = await destguild.fetch_webhook(self.bot.db["rooms_guilded"][room][guild][0])
                        self.bot.bridge.webhook_cache.store_webhook(webhook)
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

                async def tbsend(webhook, url, msg_author_gd, embeds, message, replytext, sameguild, destguild):
                    files = await get_files(message.attachments)
                    try:
                        msg = await webhook.send(avatar_url=url,
                                                 username=msg_author_gd.encode("ascii", errors="ignore").decode(),
                                                 embeds=embeds,
                                                 content=replytext + (friendly_content if friendlified else message.content),
                                                 files=files)
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
                                                              sameguild, destguild)))
                else:
                    try:
                        files = await get_files(message.attachments)
                        msg = await webhook.send(avatar_url=url,
                                                 username=msg_author_gd.encode("ascii", errors="ignore").decode(),
                                                 embeds=embeds,
                                                 content=replytext+(friendly_content if friendlified else message.content),
                                                 files=files)
                    except:
                        continue
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

        if is_pr and not pr_id in list(self.prs.keys()) and platform == source:
            self.prs.update({pr_id: parent_id})

        if system:
            msg_author = self.bot.user.id
        else:
            msg_author = message.author.id

        if id_override:
            parent_id = id_override

        try:
            index = await self.indexof(parent_id)
            msg_object = await self.fetch_message(parent_id)
            if msg_object.source == platform:
                self.bridged[index].copies = msg_object.copies | message_ids
            else:
                try:
                    self.bridged[index].external_copies[platform] = self.bridged[index].external_copies[
                                                                        platform] | message_ids
                except:
                    self.bridged[index].external_copies.update({platform: message_ids})
            self.bridged[index].urls = self.bridged[index].urls | urls
        except:
            copies = {}
            external_copies = {}
            if source == platform:
                copies = message_ids
            else:
                external_copies = {platform: message_ids}
            if source == 'revolt':
                server_id = message.server.id
            else:
                server_id = message.guild.id
            if extbridge:
                try:
                    hook = await self.bot.fetch_webhook(message.webhook_id)
                    msg_author = hook.user.id
                except:
                    pass
            self.bridged.append(UnifierBridge.UnifierMessage(
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
            if datetime.datetime.now().day != self.msg_stats_reset:
                self.msg_stats = {}
            try:
                self.msg_stats[room] += 1
            except:
                self.msg_stats.update({room: 1})
        return parent_id

class WebhookCacheStore:
    def __init__(self, bot):
        self.bot = bot
        self.__webhooks = {}

    def store_webhook(self, webhook: nextcord.Webhook or guilded.Webhook):
        if not webhook.guild.id in self.__webhooks.keys():
            self.__webhooks.update({webhook.guild.id: {webhook.id: webhook}})
        self.__webhooks[webhook.guild.id].update({webhook.id: webhook})
        return len(self.__webhooks[webhook.guild.id])

    def store_webhooks(self, webhooks: list):
        for webhook in webhooks:
            if not webhook.guild.id in self.__webhooks.keys():
                self.__webhooks.update({webhook.guild.id: {webhook.id: webhook}})
            self.__webhooks[webhook.guild.id].update({webhook.id: webhook})
        return len(self.__webhooks)

    def get_webhooks(self, guild: int or str):
        try:
            guild = int(guild)
        except:
            pass
        if len(self.__webhooks[guild].values())==0:
            raise ValueError('no webhooks')
        return list(self.__webhooks[guild].values())

    def get_webhook(self, webhook: int or str):
        try:
            webhook = int(webhook)
        except:
            pass
        for guild in self.__webhooks.keys():
            if webhook in self.__webhooks[guild].keys():
                return self.__webhooks[guild][webhook]
        raise ValueError('invalid webhook')

    def clear(self, guild: int or str = None):
        if not guild:
            self.__webhooks = {}
        else:
            self.__webhooks[guild] = {}
        return

class Bridge(commands.Cog, name=':link: Bridge'):
    """Bridge is the heart of Unifier, it's the extension that handles the bridging and everything chat related.

    Developed by Green and ItsAsheer"""

    def __init__(self, bot):
        global language
        self.bot = bot
        language = self.bot.langmgr
        restrictions.attach_bot(self.bot)
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
        self.logger = log.buildlogger(self.bot.package, 'bridge', self.bot.loglevel)
        msgs = []
        prs = {}
        msg_stats = {}
        msg_stats_reset = datetime.datetime.now().day
        restored = False
        webhook_cache = None
        if hasattr(self.bot, 'bridge'):
            if self.bot.bridge: # Avoid restoring if bridge is None
                msgs = self.bot.bridge.bridged
                prs = self.bot.bridge.prs
                restored = self.bot.bridge.restored
                msg_stats = self.bot.bridge.msg_stats
                msg_stats_reset = self.bot.bridge.msg_stats_reset
                webhook_cache = self.bot.bridge.webhook_cache
                del self.bot.bridge
        self.bot.bridge = UnifierBridge(self.bot,self.logger)
        self.bot.bridge.bridged = msgs
        self.bot.bridge.prs = prs
        self.bot.bridge.restored = restored
        self.bot.bridge.msg_stats = msg_stats
        self.bot.bridge.msg_stats_reset = msg_stats_reset
        if webhook_cache:
            self.bot.bridge.webhook_cache = webhook_cache

    @commands.command(aliases=['colour'],description=language.desc('bridge.color'))
    async def color(self,ctx,*,color=''):
        selector = language.get_selector(ctx)
        if color=='':
            try:
                current_color = self.bot.db['colors'][f'{ctx.author.id}']
                if current_color=='':
                    current_color = selector.get('default')
                    embed_color = self.bot.colors.unifier
                elif current_color=='inherit':
                    current_color = selector.get('inherit')
                    embed_color = ctx.author.color.value
                else:
                    embed_color = ast.literal_eval('0x'+current_color)
            except:
                current_color = 'Default'
                embed_color = self.bot.colors.unifier
            embed = nextcord.Embed(title=selector.get('title'),description=current_color,color=embed_color)
            await ctx.send(embed=embed)
        elif color=='inherit':
            self.bot.db['colors'].update({f'{ctx.author.id}':'inherit'})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} '+selector.get('success_inherit'))
        else:
            try:
                tuple(int(color.replace('#','',1)[i:i + 2], 16) for i in (0, 2, 4))
            except:
                return await ctx.send(selector.get('invalid'))
            self.bot.db['colors'].update({f'{ctx.author.id}':color})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} '+selector.get('success_custom'))

    @commands.command(description=language.desc('bridge.nickname'))
    async def nickname(self, ctx, *, nickname=''):
        selector = language.get_selector(ctx)
        if len(nickname) > 33:
            return await ctx.send(selector.get('exceed'))
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(f'{ctx.author.id}', None)
        else:
            self.bot.db['nicknames'].update({f'{ctx.author.id}': nickname})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(selector.get('success'))

    @commands.command(description=language.desc('bridge.ping'))
    async def ping(self, ctx):
        selector = language.get_selector(ctx)
        t = time.time()
        msg = await ctx.send(selector.get('ping'))
        diff = round((time.time() - t) * 1000, 1)
        text = selector.get('pong')+' :ping_pong:'
        if diff <= 300 and self.bot.latency <= 0.2:
            embed = nextcord.Embed(title=selector.get('normal_title'),
                                   description=f'Roundtrip: {diff}ms\nHeartbeat: {round(self.bot.latency * 1000, 1)}ms\n\n'+selector.get('normal_body'),
                                   color=self.bot.colors.success)
        elif diff <= 600 and self.bot.latency <= 0.5:
            embed = nextcord.Embed(title=selector.get('fair_title'),
                                   description=f'Roundtrip: {diff}ms\nHeartbeat: {round(self.bot.latency * 1000, 1)}ms\n\n'+selector.get('fair_body'),
                                   color=self.bot.colors.warning)
        elif diff <= 2000 and self.bot.latency <= 1.0:
            embed = nextcord.Embed(title=selector.get('slow_title'),
                                   description=f'Roundtrip: {diff}ms\nHeartbeat: {round(self.bot.latency * 1000, 1)}ms\n\n'+selector.get('slow_body'),
                                   color=self.bot.colors.error)
        else:
            text = selector.get('what')
            embed = nextcord.Embed(title=selector.get('tooslow_title'),
                                   description=f'Roundtrip: {diff}ms\nHeartbeat: {round(self.bot.latency * 1000, 1)}ms\n\n'+selector.get('tooslow_body'),
                                   color=self.bot.colors.critical)
        await msg.edit(content=text, embed=embed)

    @commands.command(description=language.desc('bridge.emojis'))
    async def emojis(self,ctx):
        selector = language.get_selector(ctx)
        panel = 0
        limit = 8
        page = 0
        was_searching = False
        emojiname = None
        query = ''
        msg = None
        interaction = None

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel == 0:
                was_searching = False
                emojis = await self.bot.loop.run_in_executor(None, lambda: sorted(
                    self.bot.emojis,
                    key=lambda x: x.name.lower()
                ))
                offset = 0
                for x in range(len(emojis)):
                    if not emojis[x-offset].guild_id in self.bot.db['emojis']:
                        emojis.pop(x-offset)
                        offset += 1

                maxpage = math.ceil(len(emojis) / limit) - 1
                if interaction:
                    if page > maxpage:
                        page = maxpage
                embed.title = f'{self.bot.ui_emojis.emoji} '+selector.fget("title",values={"botname": self.bot.user.global_name or self.bot.user.name})
                embed.description = selector.get('body')
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder=selector.get('selection_emoji')
                )

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(emojis):
                        break
                    name = emojis[index].name
                    guild = emojis[index].guild
                    emoji = (
                        f'<a:{name}:{emojis[index].id}>' if emojis[index].animated else f'<:{name}:{emojis[index].id}>'
                    )

                    embed.add_field(
                        name=f'`:{name}:`',
                        value=emoji,
                        inline=False
                    )
                    selection.add_option(
                        label=name,
                        value=name,
                        emoji=emoji,
                        description=guild.name
                    )
                if len(embed.fields)==0:
                    embed.add_field(
                        name=selector.get('noresults_title'),
                        value=selector.get('noresults_body_emoji'),
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
                            label=language.get('prev','commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0 or selection.disabled,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=language.get('next','commons.navigation'),
                            custom_id='next',
                            disabled=page >= maxpage or selection.disabled,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=language.get('search','commons.navigation'),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search,
                            disabled=selection.disabled
                        )
                    )
                )
            elif panel == 1:
                was_searching = True
                emojis = self.bot.emojis

                def search_filter(query, query_cmd):
                    return query.lower() in query_cmd.name.lower()

                offset = 0
                for x in range(len(emojis)):
                    emoji = emojis[x - offset]
                    if not emojis[x-offset].guild_id in self.bot.db['emojis'] or not search_filter(query,emoji):
                        emojis.pop(x - offset)
                        offset += 1

                embed.title = f'{self.bot.ui_emojis.emoji} {self.bot.user.global_name or self.bot.user.name} emojis / search'
                embed.description = selector.get('body')

                if len(emojis) == 0:
                    maxpage = 0
                    embed.add_field(
                        name=selector.get('noresults_title'),
                        value=selector.get('noresults_body_search'),
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get('selection_emoji'), disabled=True
                    )
                    selection.add_option(
                        label=selector.get('noresults_title')
                    )
                else:
                    maxpage = math.ceil(len(emojis) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get('selection_emoji')
                    )

                    emojis = await self.bot.loop.run_in_executor(None, lambda: sorted(
                        emojis,
                        key=lambda x: x.name
                    ))

                    for x in range(limit):
                        index = (page * limit) + x
                        if index >= len(emojis):
                            break
                        name = emojis[index].name
                        guild = emojis[index].guild
                        emoji = (
                            f'<a:{name}:{emojis[index].id}>' if emojis[index].animated else
                            f'<:{name}:{emojis[index].id}>'
                        )
                        embed.add_field(
                            name=f'`:{name}:`',
                            value=emoji,
                            inline=False
                        )
                        selection.add_option(
                            label=name,
                            value=name,
                            emoji=emoji,
                            description=guild.name
                        )

                embed.description = language.fget(
                    'search_results','commons.search',
                    values={'query': query, 'results': len(emojis)}
                )
                maxcount = (page + 1) * limit
                if maxcount > len(emojis):
                    maxcount = len(emojis)
                embed.set_footer(
                    text=(
                        language.fget('page','commons.search',values={'page': page+1, 'maxpage': maxpage+1})
                        + ' | ' + language.fget('result_count','commons.search',values={
                            'lower':page*limit+1,'upper':maxcount
                        })
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
                            label=language.get('prev','commons.navigation'),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=language.get('next','commons.navigation'),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=language.get('search','commons.navigation'),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search
                        )
                    )
                ),
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=language.get('back','commons.navigation'),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 2:
                emoji_obj = nextcord.utils.get(self.bot.emojis, name=emojiname)
                embed.title = (
                    f'{self.bot.ui_emojis.emoji} '+selector.fget("title",values={"botname": self.bot.user.global_name or self.bot.user.name})+f' / {selector.get("search").lower()} / {emojiname}'
                    if was_searching else
                    f'{self.bot.ui_emojis.emoji} '+selector.fget("title",values={"botname": self.bot.user.global_name or self.bot.user.name})+f' / {emojiname}'
                )
                emoji = (
                    f'<a:{emojiname}:{emoji_obj.id}>' if emoji_obj.animated else f'<:{emojiname}:{emoji_obj.id}>'
                )
                embed.description = f'# **{emoji} `:{emojiname}:`**\n'+f'{selector.get("from")} {emoji_obj.guild.name}'
                embed.add_field(
                    name=selector.get('instructions_title'),
                    value=selector.fget('instructions_body',values={'emojiname':emojiname}),
                    inline=False
                )
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=language.get('back','commons.navigation'),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if panel == 0:
                embed.set_footer(text=language.get('page','commons.search',values={'page':page+1,'maxpage':maxpage+1 if maxpage >= 0 else 1}))
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
                    emojiname = interaction.data['values'][0]
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
                    modal = nextcord.ui.Modal(title=language.get('search_title','commons.search'), auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label=language.get('query','commons.search'),
                            style=nextcord.TextInputStyle.short,
                            placeholder=language.get('query_prompt','commons.search')
                        )
                    )
                    await interaction.response.send_modal(modal)
            elif interaction.type == nextcord.InteractionType.modal_submit:
                panel = 1
                query = interaction.data['components'][0]['components'][0]['value']
                page = 0

    @commands.command(
        aliases=['modcall'],
        description=language.desc('bridge.modping')
    )
    @commands.cooldown(rate=1, per=1800, type=commands.BucketType.user)
    async def modping(self,ctx):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_logging']:
            return await ctx.send(selector.get('disabled'))

        found = False
        room = None

        # Optimized logic
        for key in self.bot.db['rooms']:
            data = self.bot.db['rooms'][key]
            if f'{ctx.guild.id}' in list(data.keys()):
                guilddata = data[f'{ctx.guild.id}']
                if len(guilddata) == 1:
                    continue
                if guilddata[1] == ctx.channel.id:
                    room = key
                    found = True
                    break

        # Unoptimized logic, in case channel ID is missing. Adds about 300-500ms extra latency
        if not found:
            try:
                hooks = await ctx.channel.webhooks()
            except:
                try:
                    hooks = await ctx.guild.webhooks()
                except:
                    return

            for webhook in hooks:
                index = 0
                for key in self.bot.db['rooms']:
                    data = self.bot.db['rooms'][key]
                    if f'{ctx.guild.id}' in list(data.keys()):
                        hook_ids = data[f'{ctx.guild.id}']
                    else:
                        hook_ids = []
                    if webhook.id in hook_ids:
                        found = True
                        room = list(self.bot.db['rooms'].keys())[index]
                    index += 1
                if found:
                    break

        if not found:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}')

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
                    role = self.bot.config["moderator_role"]
                except:
                    return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_moderator")}')
                await ch.send(f'<@&{role}> {selector.fget("needhelp",values={"username":author,"userid":ctx.author.id})}',allowed_mentions=nextcord.AllowedMentions(roles=True,everyone=False,users=False))
                return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

        await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("bad_config")}')

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
            return await interaction.response.send_message('Your account or your guild is currently **global banned**.', ephemeral=True)
        msg_id = msg.id

        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await interaction.response.send_message('Could not find message in cache!', ephemeral=True)

        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.emoji} Reactions',color=self.bot.colors.unifier)

        index = 0
        page = 0
        limit = 25

        maxpage = math.ceil(len(msg.reactions.keys()) / limit) - 1
        author_id = interaction.user.id
        respmsg = None
        interaction_resp = None

        while True:
            selection = nextcord.ui.StringSelect(
                max_values=1, min_values=1, custom_id='selection', placeholder='Emoji...'
            )

            for x in range(limit):
                if x + (page * limit) >= len(msg.reactions.keys()):
                    break
                if x==0 and index < x + (page * limit) or x==limit-1 and index > x + (page * limit):
                    index = x + (page * limit)
                platform = 'discord'
                if list(msg.reactions.keys())[x + (page * limit)].startswith('<r:'):
                    platform = 'revolt'
                if platform=='discord':
                    emoji = nextcord.PartialEmoji.from_str(list(msg.reactions.keys())[x + (page * limit)])
                    if emoji.is_unicode_emoji():
                        name = pymoji.demojize(emoji.name, delimiters=('',''))
                        if type(name) is list:
                            name = name[0] if len(name) > 0 else 'unknown'
                    else:
                        name = emoji.name
                else:
                    name = list(msg.reactions.keys())[x + (page * limit)].split(':')[1]
                if not name:
                    name = 'unknown'
                selection.add_option(
                    label=f':{name}:',
                    emoji=list(msg.reactions.keys())[x + (page * limit)] if not name=='unknown' and platform=='discord' else None,
                    value=f'{x}',
                    default=x + (page * limit)==index,
                    description=f'{len(msg.reactions[list(msg.reactions.keys())[x + (page * limit)]].keys())} reactions'
                )
            users = []

            if len(msg.reactions.keys()) == 0:
                embed.description = f'No reactions yet!'
            else:
                platform = 'discord'
                for user in list(msg.reactions[list(msg.reactions.keys())[index]].keys()):
                    platform = msg.reactions[list(msg.reactions.keys())[index]][user][1]
                    userobj = None
                    if platform=='discord':
                        userobj = self.bot.get_user(int(user))
                    elif platform=='revolt':
                        try:
                            userobj = self.bot.revolt_client.get_user(user)
                        except:
                            pass
                    if userobj:
                        if platform=='discord':
                            users.append(f'@{userobj.global_name if userobj.global_name else userobj.name}')
                        elif platform=='revolt':
                            users.append(f'@{userobj.display_name if userobj.display_name else userobj.name} (Revolt)')
                    else:
                        users.append('@[unknown]')
                embed.description = (
                    f'# {list(msg.reactions.keys())[index]}\n' if platform=='discord' else
                    f'# :{list(msg.reactions.keys())[index].split(":")[1]}:\n'
                ) + '\n'.join(users)

            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    selection
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        label=f'{(page-1)*limit+1}-{page*limit}' if page > 0 else '-',
                        style=nextcord.ButtonStyle.blurple,
                        custom_id='prev',
                        disabled=page <= 0
                    ),
                    nextcord.ui.Button(
                        label=(
                            f'{(page+1)*limit+1}-{limit*(page+2)}' if len(msg.reactions.keys()) >= limit*(page+2) else
                            f'{limit*(page+1)+1}-{len(msg.reactions.keys())}'
                        ) if page < maxpage else '-',
                        style=nextcord.ButtonStyle.blurple,
                        custom_id='next',
                        disabled=page >= maxpage
                    )
                )
            )

            if respmsg:
                await interaction_resp.response.edit_message(embed=embed,view=components)
            else:
                if len(msg.reactions.keys()) == 0:
                    return await interaction.response.send_message(embed=embed,ephemeral=True)
                respmsg = await interaction.response.send_message(embed=embed,view=components,ephemeral=True)
                respmsg = await respmsg.fetch()

            def check(interaction):
                return interaction.message.id==respmsg.id and interaction.user.id==author_id

            try:
                interaction_resp = await self.bot.wait_for('interaction',check=check,timeout=60)
            except:
                return await respmsg.edit(view=None)

            if interaction_resp.data['custom_id'] == 'selection':
                index = int(interaction_resp.data['values'][0]) + (page * 25)
            elif interaction_resp.data['custom_id'] == 'next':
                page += 1
            elif interaction_resp.data['custom_id'] == 'prev':
                page -= 1

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
            return await interaction.response.send_message('You or your guild is currently **global banned**.', ephemeral=True)

        if not self.bot.config['enable_logging']:
            return await interaction.response.send_message('Reporting and logging are disabled, contact your instance\'s owner.', ephemeral=True)

        try:
            msgdata = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await interaction.response.send_message('Could not find message in cache!')

        roomname = msgdata.room
        userid = msgdata.author_id
        content = copy.deepcopy(msg.content)  # Prevent tampering w/ original content

        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.blurple, label='Spam', custom_id=f'spam', disabled=False),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Abuse or harassment', custom_id=f'abuse', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Explicit or dangerous content', custom_id=f'explicit', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Violates other room rules', custom_id=f'other', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Something else', custom_id=f'misc', disabled=False
            )
        )
        btns_abuse = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Impersonation', custom_id=f'abuse_1', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Harassment', custom_id=f'abuse_2', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Intentional misinformation', custom_id=f'abuse_3', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Derogatory language', custom_id=f'abuse_4', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Other', custom_id=f'abuse_5', disabled=False
            )
        )
        btns_explicit = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Adult content', custom_id=f'explicit_1', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Graphic/gory content', custom_id=f'explicit_2', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Encouraging real-world harm', custom_id=f'explicit_3', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Illegal content', custom_id=f'explicit_4', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label='Other', custom_id=f'explicit_5', disabled=False
            )
        )
        btns2 = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label='Cancel', custom_id=f'cancel', disabled=False)
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
            color=self.bot.colors.success
        )
        if f'{ctx.guild.id}' in self.bot.bridge.restricted:
            embed.description = 'Your server is currently limited by a plugin.'
            embed.colour = self.bot.colors.warning
        await ctx.send(embed=embed)

    @commands.command(aliases=['exp','lvl','experience'], description='Shows you or someone else\'s level and EXP.')
    async def level(self,ctx,*,user=None):
        if not self.bot.config['enable_exp']:
            return await ctx.send('Leveling system is disabled on this instance.')
        if not user:
            user = ctx.author
        else:
            try:
                user = self.bot.get_user(int(user.replace('<@','',1).replace('>','',1).replace('!','',1)))
            except:
                user = ctx.author
        try:
            data = self.bot.db['exp'][f'{user.id}']
        except:
            data = {'experience':0,'level':1,'progress':0}
        bars = round(data['progress']*20)
        empty = 20-bars
        progressbar = '['+(bars*'|')+(empty*' ')+']'
        embed = nextcord.Embed(
            title=(
                'Your level' if user.id==ctx.author.id else
                f'{user.global_name if user.global_name else user.name}\'s level'
             ),
            description=(
                f'Level {data["level"]} | {round(data["experience"],2)} EXP\n\n'+
                f'`{progressbar}`\n{round(data["progress"]*100)}% towards next level'
            ),
            color=self.bot.colors.unifier
        )
        embed.set_author(
            name=f'@{user.name}',
            icon_url=user.avatar.url if user.avatar else None
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['lb'],description='Shows EXP leaderboard.')
    async def leaderboard(self,ctx):
        if not self.bot.config['enable_exp']:
            return await ctx.send('Leveling system is disabled on this instance.')
        expdata = copy.copy(self.bot.db['exp'])
        lb_data = await self.bot.loop.run_in_executor(None, lambda: sorted(
                expdata.items(),
                key=lambda x: x[1]['level']+x[1]['progress'],
                reverse=True
            )
        )
        msg = None
        interaction = None
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.leaderboard} {self.bot.user.global_name or self.bot.user.name} leaderboard',
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
                    f'{placement_emoji[rank]} **{username}**: Level {lb_data[index][1]["level"]}' if rank <= 3 else
                    f'`{rank}.` **{username}**: Level {lb_data[index][1]["level"]}'
                )

            lb_text = '\n'.join(lb)

            embed.description = lb_text

            btns = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji=self.bot.ui_emojis.first,
                    custom_id='first',
                    disabled=page==1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji=self.bot.ui_emojis.prev,
                    custom_id='prev',
                    disabled=page==1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji=self.bot.ui_emojis.next,
                    custom_id='next',
                    disabled=page==max_page
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji=self.bot.ui_emojis.last,
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

    @commands.command(description='Makes a Squad.')
    async def makesquad(self,ctx,*,squadname):
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send('Only those with Manage Server permissions can manage their Squad.')
        if not self.bot.config['enable_squads']:
            return await ctx.send('Squads aren\'t enabled on this instance.')
        if str(ctx.guild.id) in self.bot.db['squads'].keys():
            return await ctx.send('Your server already has a Squad! Disband it first to make a new one.')

        embed = nextcord.Embed(
            title=f'Creating {squadname}',
            description='First, your Squad must have a HQ channel so your members can receive updates on Squad events.',
            color=self.bot.colors.unifier
        )

        components = ui.MessageComponents()
        components.add_rows(
            ui.ActionRow(
                nextcord.ui.ChannelSelect(
                    max_values=1,
                    min_values=1,
                    placeholder='Channel...'
                )
            ),
            ui.ActionRow(
                nextcord.ui.Button(
                    custom_id='cancel',
                    label='Cancel',
                    style=nextcord.ButtonStyle.gray
                )
            )
        )

        msg = await ctx.send(embed=embed,view=components)

        def check(interaction):
            return interaction.message.id==msg.id and interaction.user.id==ctx.author.id

        try:
            interaction = await self.bot.wait_for('interaction',check=check,timeout=60)
        except:
            return await msg.edit(view=None)

        if interaction.data['component_type']==2:
            return await interaction.response.edit_message(view=None)

        hq_id = int(interaction.data['values'][0])
        squad = {
            'name': squadname,
            'suspended': False,
            'suspended_expire': 0,
            'members': [],
            'leader': ctx.author.id,
            'captains': [],
            'invited': [],
            'joinreqs': [],
            'points': 0,
            'hq': hq_id,
            'icon': None
        }

        self.bot.db['squads'].update({f'{ctx.guild.id}': squad})
        self.bot.db.save()

        added = 0
        while True:
            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.UserSelect(
                        max_values=1,
                        min_values=1,
                        placeholder='Select users...'
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        custom_id='cancel',
                        label='Add later',
                        style=nextcord.ButtonStyle.gray
                    )
                )
            )

            embed.description = (
                'Your squad was created, now you need your Squad captains! You\'re already a Squad captain, but you '+
                'should add two more. They\'ll be sent an invitation if they aren\'t in a Squad yet.'+
                '\n\n**You need 2 more Squad captains.**' if added==0 else '\n\n**You need 1 more Squad captain.**'
            )

            await msg.edit(embed=embed,view=components)

            try:
                interaction = await self.bot.wait_for('interaction',check=check,timeout=300)
            except:
                return await msg.edit(view=None)

            if interaction.data['component_type']==2:
                return await interaction.response.edit_message(view=None)

            if added==2:
                break

            user = self.bot.get_user(int(interaction.data['values'][0]))

            fail_msg = (
                'The bot could not send a Squad invitation! This is either because:\n- The user has their DMs with '+
                'the bot off\n- The user is ignoring Squad invitations from your server'
            )

            try:
                if f'{user.id}' in self.bot.db['squads_optout'].keys():
                    optout = self.bot.db['squads_optout'][f'{user.id}']
                    if optout['all']:
                        fail_msg = f'{user.global_name or user.name} has opted out of receiving Squad invitations.'
                        raise ValueError()
                    elif ctx.guild.id in optout['guilds']:
                        raise ValueError()
                if f'{user.id}' in self.bot.db['squads_joined'].keys():
                    if self.bot.db['squads_optout'][f'{user.id}'] is None:
                        fail_msg = f'{user.global_name or user.name} is already in a Squad!'
                        raise ValueError()
                embed = nextcord.Embed(
                    title=(
                        f'{ctx.author.global_name or ctx.author.name} has invited you to join {ctx.guild.name}\'s '+
                        f'**{squadname}** Squad!'
                    ),
                    description=(
                        'You\'ve been invited to join as a **Squad Captain**!\nAs a captain, you may:\n'+
                        '- Make submissions for events on your Squad\'s behalf\n'+
                        '- Accept and deny join requests for your Squad\n\n'+
                        f'To join this squad, run `{self.bot.command_prefix}joinsquad {ctx.guild.id}`!'
                    )
                )
                embed.set_footer(
                    text=(
                        f'Reminder - you can always run {self.bot.command_prefix}ignoresquad {ctx.guild.id} to stop receiving invites from '+
                        'this server\'s Squad.'
                    )
                )
                await user.send(embed=embed)
                added += 1
                if added == 2:
                    break
                else:
                    embed.description = (
                        'Your squad was created, now you need your Squad captains! You\'re already a Squad captain, but you ' +
                        'should add two more. They\'ll be sent an invitation if they aren\'t in a Squad yet.' +
                        '\n\n**You need 1 more Squad captain.**'
                    )

                    await msg.edit(embed=embed, view=components)
                    self.bot.db['squads'][f'{ctx.guild.id}']['invited'].append(user.id)
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                    await interaction.response.send_message('Invite sent!', ephemeral=True)
            except:
                await interaction.response.send_message(fail_msg,ephemeral=True)

        await interaction.response.edit_message(embed=embed,view=None)
        pass

    @commands.command(description='Disbands your squad.')
    async def disbandsquad(self,ctx):
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send('Only those with Manage Server permissions can manage their Squad.')
        if not self.bot.config['enable_squads']:
            return await ctx.send('Squads aren\'t enabled on this instance.')

    @commands.command(name='squad-leaderboard', aliases=['squadlb'], description='Shows Squad points leaderboard.')
    async def squad_leaderboard(self, ctx):
        if not self.bot.config['enable_squads']:
            return await ctx.send('Squads aren\'t enabled on this instance.')
        expdata = copy.copy(self.bot.db['squads'])
        lb_data = await self.bot.loop.run_in_executor(None, lambda: sorted(
                expdata.items(),
                key=lambda x: x[1]['points'],
                reverse=True
            )
        )
        msg = None
        interaction = None
        embed = nextcord.Embed(
            title=f'{self.bot.user.global_name or self.bot.user.name} Squads leaderboard',
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
                index = (page - 1) * limit + x
                rank = index + 1
                if index >= len(lb_data):
                    break
                username = lb_data[index][1]['name']
                lb.append(
                    f'{placement_emoji[rank]} **{username}**: {lb_data[index][1]["points"]} points' if rank <= 3 else
                    f'`{rank}.` **{username}**: {lb_data[index][1]["level"]} points'
                )

            lb_text = '\n'.join(lb)

            embed.description = lb_text

            btns = ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji='\U000023EE',
                    custom_id='first',
                    disabled=page == 1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji='\U000025C0',
                    custom_id='prev',
                    disabled=page == 1
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    emoji='\U000025B6',
                    custom_id='next',
                    disabled=page == max_page
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.blurple,
                    emoji='\U000023ED',
                    custom_id='last',
                    disabled=page == max_page
                )
            )

            components = ui.MessageComponents()
            components.add_row(btns)

            if not msg:
                msg = await ctx.send(embed=embed, view=components)
            else:
                await interaction.response.edit_message(embed=embed, view=components)

            def check(interaction):
                return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
            except:
                for x in range(len(btns.items)):
                    btns.items[x].disabled = True

                components = ui.MessageComponents()
                components.add_row(btns)
                await msg.edit(view=components)
                break

            if interaction.data['custom_id'] == 'first':
                page = 1
            elif interaction.data['custom_id'] == 'prev':
                page -= 1
            elif interaction.data['custom_id'] == 'next':
                page += 1
            elif interaction.data['custom_id'] == 'last':
                page = max_page

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type==nextcord.InteractionType.component:
            if not 'custom_id' in interaction.data.keys():
                return
            if (interaction.data["custom_id"].startswith('rp') or interaction.data["custom_id"].startswith('ap')) and not interaction.user.id in self.bot.moderators:
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
                    msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
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
                embed.color = self.bot.colors.success
                author = f'@{interaction.user.name}'
                if not interaction.user.discriminator == '0':
                    author = f'{interaction.user.name}#{interaction.user.discriminator}'
                embed.title = f'This report has been reviewed by {author}!'
                await interaction.response.defer(ephemeral=True, with_message=True)
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
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content='Marked report as reviewed!')
            elif interaction.data["custom_id"].startswith('apaccept_') or interaction.data["custom_id"].startswith('apreject_'):
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=(
                            nextcord.ButtonStyle.gray if interaction.data["custom_id"].startswith('apaccept_')
                            else nextcord.ButtonStyle.red
                        ),
                        label='Reject',
                        disabled=True,
                        emoji=self.bot.ui_emojis.error
                    ),
                    nextcord.ui.Button(
                        style=(
                            nextcord.ButtonStyle.gray if interaction.data["custom_id"].startswith('apreject_')
                            else nextcord.ButtonStyle.green
                        ),
                        label='Accept & unban',
                        disabled=True,
                        emoji=self.bot.ui_emojis.success
                    )
                )
                components = ui.MessageComponents()
                components.add_row(btns)
                embed = interaction.message.embeds[0]
                embed.color = self.bot.colors.success
                author = f'@{interaction.user.name}'
                if not interaction.user.discriminator == '0':
                    author = f'{interaction.user.name}#{interaction.user.discriminator}'
                embed.title = (
                    'This appeal was ' +
                    ('accepted' if interaction.data["custom_id"].startswith('apaccept_') else 'rejected') +
                    f' by {author}!'
                )
                await interaction.response.defer(ephemeral=True, with_message=True)
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
                            await thread.send('This appeal has been closed.')
                        except:
                            pass
                    self.bot.db['report_threads'].pop(str(interaction.message.id))
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                userid = int(interaction.data["custom_id"][9:])
                if interaction.data["custom_id"].startswith('apaccept_'):
                    try:
                        self.bot.db['banned'].pop(str(userid))
                        for i in range(len(self.bot.db['modlogs'][f'{userid}'])):
                            if self.bot.db['modlogs'][f'{userid}'][len(self.bot.db['modlogs'][f'{userid}']) - i - 1][
                                    'type'] == 1:
                                self.bot.db['modlogs'][f'{userid}'].pop(
                                    len(self.bot.db['modlogs'][f'{userid}']) - i - 1)
                                break
                        self.bot.db.save_data()
                    except:
                        pass
                    results_embed = nextcord.Embed(
                        title='Your ban appeal was accepted!',
                        description=(
                            'This ban has been removed from your account and will no longer impact your standing.\n'+
                            'You may now continue chatting!'
                        ),
                        color=self.bot.colors.success
                    )
                else:
                    results_embed = nextcord.Embed(
                        title='Your ban appeal was denied.',
                        description='You may continue chatting once the current ban expires.',
                        color=self.bot.colors.error
                    )
                user = self.bot.get_user(userid)
                if user:
                    await user.send(embed=results_embed)
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content='Marked appeal as reviewed!')
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

            await interaction.response.defer(ephemeral=True,with_message=False)
            cat = report[0]
            cat2 = report[1]
            content = report[2]
            roomname = report[3]
            msgid = report[4]
            msgdata = await self.bot.bridge.fetch_message(msgid)
            userid = int(interaction.data["custom_id"].split('_')[0])
            if len(content) > 4096:
                content = content[:-(len(content) - 4096)]
            embed = nextcord.Embed(
                title='Message report - content is as follows',
                description=content,
                color=self.bot.colors.warning,
                timestamp=datetime.datetime.now(datetime.UTC)
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
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            except:
                pass
            self.bot.reports.pop(f'{interaction.user.id}_{interaction.data["custom_id"]}')
            return await interaction.edit_original_message(
                content="# :white_check_mark: Your report was submitted!\nThanks for your report! Our moderators will have a look at it, then decide what to do.\nFor privacy reasons, we will not disclose actions taken against the user.",
                view=None
            )

    @commands.command(hidden=True,description='Initializes new UnifierBridge object.')
    @restrictions.owner()
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
    @restrictions.owner()
    async def system(self, ctx, room):
        ctx.message.content = ctx.message.content.replace(f'{self.bot.command_prefix}system {room}','',1)
        await self.bot.bridge.send(room,ctx.message,'discord',system=True)
        for platform in self.bot.config['external']:
            await self.bot.bridge.send(room, ctx.message, platform, system=True)
        await ctx.send('Sent as system')

    @commands.Cog.listener()
    async def on_message(self, message):
        if not type(message.channel) is nextcord.TextChannel:
            return
        if message.content.startswith(f'{self.bot.command_prefix}system'):
            return
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
            if f'{message.author.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.author.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.author.id}')
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    return

        if message.author.id == self.bot.user.id:
            return

        found = False
        roomname = None

        # Optimized logic
        for key in self.bot.db['rooms']:
            data = self.bot.db['rooms'][key]
            if f'{message.guild.id}' in list(data.keys()):
                guilddata = data[f'{message.guild.id}']
                if len(guilddata) == 1:
                    continue
                if guilddata[1]==message.channel.id:
                    roomname = key
                    found = True
                    break

        # Unoptimized logic, in case channel ID is missing. Adds about 300-500ms extra latency
        if not found:
            try:
                hooks = await message.channel.webhooks()
            except:
                try:
                    hooks = await message.guild.webhooks()
                except:
                    return

            for webhook in hooks:
                index = 0
                for key in self.bot.db['rooms']:
                    data = self.bot.db['rooms'][key]
                    if f'{message.guild.id}' in list(data.keys()):
                        hook_ids = data[f'{message.guild.id}']
                    else:
                        hook_ids = []
                    if webhook.id in hook_ids:
                        found = True
                        roomname = list(self.bot.db['rooms'].keys())[index]
                    index += 1
                if found:
                    break

        if not found:
            return

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
                            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
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
                color=self.bot.colors.error
            )

            if public:
                embed.add_field(name='Reason',value=public_reason if public_reason else '[unknown]',inline=False)

            await message.channel.send(embed=embed)

            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.warning} Content blocked - content is as follows',
                description=message.content[:-(len(message.content)-4096)] if len(message.content) > 4096 else message.content,
                color=self.bot.colors.error,
                timestamp=datetime.datetime.now(datetime.UTC)
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
                ch = self.bot.get_channel(self.bot.config['reports_channel'])
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
                    title=f'You\'ve been __banned__ by @Unifier (system)!',
                    description='Automatic action carried out by security plugins',
                    color=self.bot.colors.warning,
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.set_author(
                    name='@Unifier (system)',
                    icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                )
                if banned[user]==0:
                    embed.colour = self.bot.colors.critical
                    embed.add_field(
                        name='Actions taken',
                        value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',
                        inline=False
                    )
                    embed.add_field(name='Did we make a mistake?',
                                    value=f'If you think we didn\'t make the right call, you can always appeal your ban using `{self.bot.command_prefix}!appeal`.',
                                    inline=False)
                    await self.bot.loop.run_in_executor(None,lambda: self.bot.bridge.add_modlog(0, user_obj.id, 'Automatic action carried out by security plugins', self.bot.user.id))
                else:
                    embed.add_field(
                        name='Actions taken',
                        value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{round(nt)}:f>. This will expire <t:{round(nt)}:R>.',
                        inline=False
                    )
                    embed.add_field(name='Did we make a mistake?',
                                    value=f'Unfortunately, this ban cannot be appealed using `{self.bot.command_prefix}appeal`. You will need to ask moderators for help.',
                                    inline=False)
                try:
                    await user_obj.send(embed=embed)
                except:
                    pass

            return

        if f'{message.author.id}' in list(self.bot.bridge.secbans.keys()):
            if self.bot.bridge.secbans[f'{message.author.id}'] < time.time():
                self.bot.bridge.secbans.pop(f'{message.author.id}')
            else:
                return

        if f'{message.guild.id}' in list(self.bot.bridge.restricted.keys()):
            if self.bot.bridge.restricted[f'{message.guild.id}'] < time.time():
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
        emojified = False

        if '[emoji:' in message.content or is_pr or is_pr_ref:
            multisend = False
            should_resend = True
            emojified = True

        tasks = []
        parent_id = None

        if not message.channel.permissions_for(message.guild.me).manage_messages:
            if emojified or is_pr_ref:
                return await message.channel.send(
                    'Parent message could not be deleted. I may be missing the `Manage Messages` permission.'
                )

        if (message.content.lower().startswith('is unifier down') or
                message.content.lower().startswith('unifier not working')):
            await message.channel.send('no',reference=message)

        if multisend:
            # Multisend
            # Sends Discord message along with other platforms to minimize
            # latency on external platforms.
            self.bot.bridge.bridged.append(UnifierBridge.UnifierMessage(
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
            if datetime.datetime.now().day != self.bot.bridge.msg_stats_reset:
                self.bot.bridge.msg_stats_reset = datetime.datetime.now().day
                self.bot.bridge.msg_stats = {}
            try:
                self.bot.bridge.msg_stats[roomname] += 1
            except:
                self.bot.bridge.msg_stats.update({roomname: 1})
            tasks.append(self.bot.loop.create_task(
                self.bot.bridge.send(room=roomname,message=message,platform='discord', extbridge=extbridge))
            )
        else:
            parent_id = await self.bot.bridge.send(room=roomname, message=message, platform='discord', extbridge=extbridge)

        for platform in self.bot.config['external']:
            if should_resend and parent_id==message.id:
                tasks.append(self.bot.loop.create_task(self.bot.bridge.send(
                    room=roomname, message=message, platform=platform, extbridge=extbridge, id_override=parent_id
                )))
            else:
                tasks.append(self.bot.loop.create_task(
                    self.bot.bridge.send(room=roomname, message=message, platform=platform, extbridge=extbridge)
                ))

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

        if should_resend:
            await message.delete()

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

        if not message.author.bot and self.bot.config['enable_exp']:
            _newexp, levelup = await self.bot.bridge.add_exp(message.author.id)

            if levelup:
                level = self.bot.db['exp'][f'{message.author.id}']['level']
                embed = nextcord.Embed(
                    title=f'Level {level-1} => __Level {level}__',
                    color=self.bot.colors.blurple
                )
                embed.set_author(
                    name=(
                        f'@{message.author.global_name if message.author.global_name else message.author.name} leveled'+
                        ' up!'
                    ),
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
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    return
            if f'{message.guild.id}' in list(gbans.keys()):
                banuntil = gbans[f'{message.guild.id}']
                if ct >= banuntil and not banuntil == 0:
                    self.bot.db['banned'].pop(f'{message.guild.id}')
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                else:
                    return

        if not message.webhook_id == None:
            # webhook msg, dont bother
            return

        if message.author.id == self.bot.user.id:
            return

        found = False
        roomname = None

        # Optimized logic
        for key in self.bot.db['rooms']:
            data = self.bot.db['rooms'][key]
            if f'{message.guild.id}' in list(data.keys()):
                guilddata = data[f'{message.guild.id}']
                if len(guilddata) == 1:
                    continue
                if guilddata[1] == message.channel.id:
                    roomname = key
                    found = True
                    break

        # Unoptimized logic, in case channel ID is missing. Adds about 300-500ms extra latency
        if not found:
            try:
                hooks = await message.channel.webhooks()
            except:
                try:
                    hooks = await message.guild.webhooks()
                except:
                    return

            for webhook in hooks:
                index = 0
                for key in self.bot.db['rooms']:
                    data = self.bot.db['rooms'][key]
                    if f'{message.guild.id}' in list(data.keys()):
                        hook_ids = data[f'{message.guild.id}']
                    else:
                        hook_ids = []
                    if webhook.id in hook_ids:
                        found = True
                        roomname = list(self.bot.db['rooms'].keys())[index]
                    index += 1
                if found:
                    break

        if not found:
            return

        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not str(msg.id)==str(message.id):
                raise ValueError()
        except:
            return

        await self.bot.bridge.edit(msg.id,message.content)

    @commands.Cog.listener()
    async def on_raw_message_edit(self,payload):
        if payload.cached_message:
            # on_message_edit should handle this, as it's already firing
            return
        else:
            ch = self.bot.get_channel(payload.channel_id)
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
                        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                    else:
                        return
                if f'{message.guild.id}' in list(gbans.keys()):
                    banuntil = gbans[f'{message.guild.id}']
                    if ct >= banuntil and not banuntil == 0:
                        self.bot.db['banned'].pop(f'{message.guild.id}')
                        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                    else:
                        return

            if not message.webhook_id == None:
                # webhook msg, dont bother
                return

            if message.author.id == self.bot.user.id:
                return

            found = False
            roomname = None

            # Optimized logic
            for key in self.bot.db['rooms']:
                data = self.bot.db['rooms'][key]
                if f'{message.guild.id}' in list(data.keys()):
                    guilddata = data[f'{message.guild.id}']
                    if len(guilddata) == 1:
                        continue
                    if guilddata[1] == message.channel.id:
                        roomname = key
                        found = True
                        break

            # Unoptimized logic, in case channel ID is missing. Adds about 300-500ms extra latency
            if not found:
                try:
                    hooks = await message.channel.webhooks()
                except:
                    return

                for webhook in hooks:
                    index = 0
                    for key in self.bot.db['rooms']:
                        data = self.bot.db['rooms'][key]
                        if f'{message.guild.id}' in list(data.keys()):
                            hook_ids = data[f'{message.guild.id}']
                        else:
                            hook_ids = []
                        if webhook.id in hook_ids:
                            found = True
                            roomname = list(self.bot.db['rooms'].keys())[index]
                        index += 1
                    if found:
                        break

            if not found:
                return

            if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
                return

            try:
                msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(message.id)
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

        found = False
        roomname = None

        # Optimized logic
        for key in self.bot.db['rooms']:
            data = self.bot.db['rooms'][key]
            if f'{message.guild.id}' in list(data.keys()):
                guilddata = data[f'{message.guild.id}']
                if len(guilddata) == 1:
                    continue
                if guilddata[1] == message.channel.id:
                    roomname = key
                    found = True
                    break

        # Unoptimized logic, in case channel ID is missing. Adds about 300-500ms extra latency
        if not found:
            try:
                hooks = await message.channel.webhooks()
            except:
                try:
                    hooks = await message.guild.webhooks()
                except:
                    return

            for webhook in hooks:
                index = 0
                for key in self.bot.db['rooms']:
                    data = self.bot.db['rooms'][key]
                    if f'{message.guild.id}' in list(data.keys()):
                        hook_ids = data[f'{message.guild.id}']
                    else:
                        hook_ids = []
                    if webhook.id in hook_ids:
                        found = True
                        roomname = list(self.bot.db['rooms'].keys())[index]
                    index += 1
                if found:
                    break

        if not found:
            return

        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not msg.id == message.id:
                raise ValueError()
        except:
            return

        await self.bot.bridge.delete_copies(msg.id)

        try:
            if not self.bot.config['enable_logging']:
                raise RuntimeError()
            ch = self.bot.get_channel(self.bot.config['logs_channel'])

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event):
        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(event.message_id)
        except:
            return

        if event.user_id in self.bot.db['fullbanned']:
            return

        emoji = event.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        else:
            emoji = f'<a:{emoji.name}:{emoji.id}>' if emoji.animated else f'<:{emoji.name}:{emoji.id}>'

        await msg.add_reaction(emoji, event.user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event):
        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(event.message_id)
        except:
            return

        if event.user_id in self.bot.db['fullbanned']:
            return

        emoji = event.emoji
        if emoji.is_unicode_emoji():
            emoji = emoji.name
        else:
            emoji = f'<a:{emoji.name}:{emoji.id}>' if emoji.animated else f'<:{emoji.name}:{emoji.id}>'

        await msg.remove_reaction(emoji, event.user_id)

    async def cog_command_error(self, ctx, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Bridge(bot))
