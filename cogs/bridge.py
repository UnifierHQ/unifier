"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

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
from nextcord.ext import commands
import traceback
import time
import datetime
import random
import string
import copy
import json
import compress_json
import re
import ast
import math
import os
from utils import log, langmgr, ui, platform_base, restrictions as r
import importlib
import emoji as pymoji
import aiomultiprocess
import aiohttp
from aiomultiprocess import Worker

# import ujson if installed
try:
    import ujson as json
except:
    pass

aiomultiprocess.set_start_method("fork")

mentions = nextcord.AllowedMentions(everyone=False, roles=False, users=False)
emergency_mentions = nextcord.AllowedMentions(everyone=False, roles=True, users=True)
restrictions = r.Restrictions()
language = langmgr.partial()
language.load()

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
arrow_unicode = '\U0000250C'

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
        if db['rooms'][room]['meta']['locked']:
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

class UnifierAlert:
    titles = {
        'drill': {
            'emergency': 'Drill __**emergency**__ issued (this is only a test)',
            'warning': 'Drill __**warning**__ issued (this is only a test)',
            'advisory': 'Drill __**advisory**__ issued (this is only a test)',
            'clear': 'Drill __**all clear**__ issued (this is only a test)'
        },
        'raid': {
            'emergency': 'Raid __**emergency**__ issued',
            'warning': 'Raid __**warning**__ issued',
            'advisory': 'Raid __**advisory**__ issued',
            'clear': 'Raid __**all clear**__ issued'
        },
        'general': {
            'emergency': 'General __**emergency**__ issued',
            'warning': 'General __**warning**__ issued',
            'advisory': 'General __**advisory**__ issued',
            'clear': 'General __**all clear**__ issued'
        }
    }

    precautions = {
        'drill': {
            'emergency': [
                'How to address **real emergency alerts**:',
                '- If you see an **emergency**, a threat may be imminent. Immediate attention is required.',
                '- Countermeasures against the risk **should** be taken.',
                '- Take actions as described to protect your community.'
            ],
            'warning': [
                'How to address **real warning alerts**:',
                '- If you see a **warning**, a threat is likely. Attention is required.',
                '- Countermeasures against the risk **can** be taken.',
                '- Take actions as described to prepare for the threat.'
            ],
            'advisory': [
                'How to address **real advisory alerts**:',
                '- If you see an **advisory**, a threat is possible, but not imminent.',
                '- Countermeasures against the risk are not recommended at this stage.',
                '- Take actions as described to prepare for a possible risk elevation (to warning or emergency).'
            ],
            'clear': [
                'How to address **real all clear alerts**:',
                '- If you see an **all clear**, it means related alerts are no longer in effect.',
                '- You may remove any temporary countermeasures to restore normal functionality.'
            ]
        },
        'raid': {
            'emergency': [
                '- Notify members of a likely imminent raid in Unifier rooms.',
                '- Prepare to run `u!restrict` on servers being raided.',
                '- If your server is being raided, run `u!under-attack` to temporarily block messages from ' +
                'being sent from your server to Unifier rooms.'
            ],
            'warning': [
                '- Notify members of a possible raid in Unifier rooms.',
                '- Familiarize moderators with server-side moderation commands.',
                '- If your server is targeted, take countermeasures to protect your server.'
            ],
            'advisory': [
                '- Stay alert for unusual behavior from new members.',
                '- If your server is targeted, stay alert for any developments.'
            ],
            'clear': [
                '- Run `u!unrestrict` on affected servers to unblock them from your server.',
                '- If your server was being raided, run `u!under-attack` to disable Under Attack mode.'
            ]
        },
        'general': {
            'emergency': [
                '- Notify members of a likely imminent general threat.',
                '- Prepare to take appropriate action.',
                '- Prepare to run `u!restrict` on servers if needed.'
            ],
            'warning': [
                '- Notify members of a possible general threat.',
                '- Plan appropriate actions to be taken.',
                '- Familiarize moderators with server-side moderation commands.'
            ],
            'advisory': [
                '- Stay alert for unusual behavior.',
                '- Frequently check the alerts channel for any developments.'
            ],
            'clear': [
                '- Run `u!unrestrict` on affected servers to unblock them from your server.'
            ]
        }
    }

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
        self.__bot = bot
        self.bridged = []
        self.prs = {}
        self.webhook_cache = webhook_cache or WebhookCacheStore(self.__bot)
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
        self.__room_template = {
            'rules': [], 'restricted': False, 'locked': False, 'private': False,
            'private_meta': {
                'server': None,
                'allowed': [],
                'invites': [],
                'platform': 'discord'
            },
            'emoji': None, 'description': None, 'display_name': None, 'banned': []
        }
        self.alert = UnifierAlert

        # This is a developer-only value. Please leave this as is.
        self.moderator_override = True

    @property
    def room_template(self):
        return self.__room_template

    @property
    def rooms(self):
        return list(self.__bot.db['rooms'].keys())

    @property
    def public_rooms(self):
        return [room for room in self.rooms if not self.get_room(room)['meta']['private']]

    class UnifierMessage:
        def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room,
                     external_urls=None, webhook=False, prehook=None, reply=False, external_bridged=False,
                     reactions=None, thread=None, reply_v2=False):
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
            self.reply_v2 = reply_v2
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

    class RoomForbiddenError(Exception):
        pass

    class TooManyRooms(Exception):
        pass

    class RoomBannedError(Exception):
        pass

    class RoomNotFoundError(Exception):
        pass

    class RoomExistsError(Exception):
        pass

    class InviteNotFoundError(Exception):
        pass

    class InviteExistsError(Exception):
        pass

    def get_reply_style(self, guild_id):
        if str(guild_id) in self.__bot.db['settings'].keys():
            return self.__bot.db['settings'][f'{guild_id}'].get('reply_layout',0)
        return 0

    def set_reply_style(self, guild_id, reply_type):
        if not str(guild_id) in self.__bot.db['settings'].keys():
            self.__bot.db['settings'].update({f'{guild_id}': {}})

        self.__bot.db['settings'][f'{guild_id}'].update({'reply_layout': reply_type})

    def add_modlog(self, action_type, user, reason, moderator):
        t = time.time()
        try:
            self.__bot.db['modlogs'][f'{user}'].append({
                'type': action_type,
                'reason': reason,
                'time': t,
                'mod': moderator
            })
        except:
            self.__bot.db['modlogs'].update({
                f'{user}': [{
                    'type': action_type,
                    'reason': reason,
                    'time': t,
                    'mod': moderator
                }]
            })
        self.__bot.db.save_data()

    def get_modlogs(self, user):
        t = time.time()

        if not f'{user}' in list(self.__bot.db['modlogs'].keys()):
            return {
                'warns': [],
                'bans': []
            }, {
                'warns': [],
                'bans': []
            }

        actions = {
            'warns': [log for log in self.__bot.db['modlogs'][f'{user}'] if log['type'] == 0],
            'bans': [log for log in self.__bot.db['modlogs'][f'{user}'] if log['type'] == 1]
        }
        actions_recent = {
            'warns': [log for log in self.__bot.db['modlogs'][f'{user}'] if log['type'] == 0 and t - log['time'] <= 2592000],
            'bans': [log for log in self.__bot.db['modlogs'][f'{user}'] if log['type'] == 1 and t - log['time'] <= 2592000]
        }

        return actions, actions_recent

    def get_modlogs_count(self, user):
        actions, actions_recent = self.get_modlogs(user)
        return {
            'warns': len(actions['warns']), 'bans': len(actions['bans'])
        }, {
            'warns': len(actions_recent['warns']), 'bans': len(actions_recent['bans'])
        }

    def get_channel_room(self, channel, platform='discord'):
        """Alias for check_duplicate, except it returns None instead of False if no rooms are found"""
        room = self.check_duplicate(channel, platform=platform)

        if not room:
            return None

        return room

    def check_duplicate(self, channel, platform='discord'):
        support = None
        if not platform=='discord':
            support = self.__bot.platforms[platform]

        for room in self.rooms:
            roominfo = self.get_room(room)

            if not platform in roominfo.keys():
                continue

            if platform=='discord':
                if not f'{channel.guild.id}' in roominfo['discord'].keys():
                    continue
                if channel.id in roominfo['discord'][f'{channel.guild.id}']:
                    return room
            else:
                if not f'{support.get_id(support.server(channel))}' in roominfo[platform].keys():
                    continue
                if support.get_id(channel) in roominfo[platform][f'{support.get_id(support.server(channel))}']:
                    return room
        return False

    def get_room(self, room) -> dict or None:
        """Gets a Unifier room.
        This will be moved to UnifierBridge for a future update."""
        try:
            roominfo = self.__bot.db['rooms'][room]
            base = {'meta': dict(self.__room_template)}

            # add template keys and values to data
            for key in roominfo.keys():
                if key == 'meta':
                    for meta_key in roominfo['meta'].keys():
                        if meta_key == 'private_meta':
                            for pmeta_key in roominfo['meta']['private_meta'].keys():
                                base['meta']['private_meta'].update(
                                    {pmeta_key: roominfo['meta']['private_meta'][pmeta_key]}
                                )
                        else:
                            base['meta'].update({meta_key: roominfo['meta'][meta_key]})
                else:
                    base.update({key: roominfo[key]})

            return base
        except:
            return None

    def can_manage_room(self, room, user, platform='discord') -> bool:
        roominfo = self.get_room(room)

        if platform == 'discord':
            manage_guild = user.guild_permissions.manage_guild
        else:
            support = self.__bot.platforms[platform]
            manage_guild = support.permissions(user).manage_server

        if roominfo['meta']['private']:
            if user:
                if user.id in self.__bot.moderators and not self.moderator_override:
                    return True
            return user.guild.id == roominfo['meta']['private_meta']['server'] and manage_guild
        else:
            return user.id in self.__bot.admins

    def can_join_room(self, room, user, platform='discord') -> bool:
        roominfo = self.get_room(room)

        if platform == 'discord':
            manage_channels = user.guild_permissions.manage_channels
        else:
            support = self.__bot.platforms[platform]
            manage_channels = support.permissions(user).manage_channels

        if roominfo['meta']['private']:
            if user:
                if user.id in self.__bot.moderators and not self.moderator_override:
                    return True
            return (
                    user.guild.id == roominfo['meta']['private_meta']['server'] or
                    user.guild.id in roominfo['meta']['private_meta']['allowed']
            ) and manage_channels
        else:
            return manage_channels

    def can_access_room(self, room, user, ignore_mod=False) -> bool:
        roominfo = self.get_room(room)
        if roominfo['meta']['private']:
            if user:
                if user.id in self.__bot.moderators and not (self.moderator_override or ignore_mod):
                    return True
            return (
                    user.guild.id == roominfo['meta']['private_meta']['server'] or
                    user.guild.id in roominfo['meta']['private_meta']['allowed']
            )
        else:
            return True

    def update_room(self, room, roominfo):
        if not room in self.__bot.db['rooms'].keys():
            raise self.RoomNotFoundError('invalid room')

        self.__bot.db['rooms'][room] = roominfo
        self.__bot.db.save_data()

    def create_room(self, room, private=True, platform='discord', origin=None, dry_run=False) -> dict:
        if room in self.__bot.db['rooms'].keys():
            raise self.RoomExistsError('room already exists')
        if private and not origin:
            raise ValueError('origin must be provided')

        room_base = {'meta': dict(self.__room_template)}
        room_base['meta'].update({'private': private})

        if private:
            if not self.__bot.config['enable_private_rooms']:
                raise ValueError('private rooms are disabled')

            if not dry_run:
                if not f'{origin}' in self.__bot.db['rooms_count'].keys():
                    self.__bot.db['rooms_count'].update({f'{origin}': 0})
                if (
                        self.__bot.db['rooms_count'][f'{origin}'] >= self.__bot.config['private_rooms_limit'] and
                        not self.__bot.config['private_rooms_limit'] == 0
                ):
                    raise self.TooManyRooms('exceeded limit')
                self.__bot.db['rooms_count'][f'{origin}'] += 1
            room_base['meta']['private_meta'].update({'server': origin, 'platform': platform})

        if not dry_run:
            self.__bot.db['rooms'].update({room: room_base})
            self.__bot.db.save_data()

        return room_base

    def delete_room(self, room):
        if not room in self.rooms:
            raise self.RoomNotFoundError('invalid room')

        room = self.get_room(room)
        for invite in room['meta']['private_meta']['invites']:
            self.delete_invite(invite)

        try:
            if (
                    room['meta']['private_meta']['server'] and
                    self.__bot.db['rooms_count'][room['meta']['private_meta']['server']] > 0
            ):
                self.__bot.db['rooms_count'][room['meta']['private_meta']['server']] -= 1
        except:
            # not something to worry about
            pass

        self.__bot.db['rooms'].pop(room)
        self.__bot.db.save_data()

    def get_invite(self, invite) -> dict or None:
        try:
            invite = self.__bot.db['invites'][invite]

            if invite['expire'] < time.time() and not invite['expire'] == 0:
                self.delete_invite(invite)
                return None

            return invite
        except:
            return None

    def create_invite(self, room, max_usage, expire) -> str:
        if len(self.__bot.db['rooms'][room]['meta']['private_meta']['invites']) >= 20:
            raise RuntimeError('maximum invite limit reached')

        while True:
            # generate unique invite
            invite = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            if not invite in self.__bot.db['invites'].keys():
                break

        self.__bot.db['invites'].update({invite: {
            'remaining': max_usage, 'expire': expire, 'room': room
        }})
        self.__bot.db['rooms'][room]['meta']['private_meta']['invites'].append(invite)
        self.__bot.db.save_data()
        return invite

    def delete_invite(self, invite):
        if not invite in self.__bot.db['invites'].keys():
            raise self.InviteNotFoundError('invalid invite')

        room = self.__bot.db['invites'][invite]['room']
        self.__bot.db['invites'].pop(invite)
        try:
            self.__bot.db['rooms'][room]['meta']['private_meta']['invites'].remove(invite)
        except:
            # room prob deleted, ignore
            pass
        self.__bot.db.save_data()

    async def accept_invite(self, user, invite, platform='discord'):
        invite = self.get_invite(invite)
        if not invite:
            raise self.InviteNotFoundError('invalid invite')
        roominfo = self.get_room(invite['room'])
        if not roominfo:
            raise self.RoomNotFoundError('invalid room')
        if not roominfo['meta']['private']:
            self.delete_invite(invite)
            raise RuntimeError('invite leads to a public room, expired')
        if platform == 'discord':
            server_id = user.guild.id
            user_id = user.id
        else:
            support = self.__bot.platforms[platform]
            server_id = support.get_id(support.server(user))
            user_id = support.get_id(user)
        if (
                str(server_id) in roominfo['meta']['banned']
        ) and (not user_id in self.__bot.moderators and not self.moderator_override):
            raise self.RoomBannedError('banned from room')
        if invite['remaining'] == 1:
            self.delete_invite(invite)
        else:
            if invite['remaining'] > 0:
                self.__bot.db['invites'][invite]['remaining'] -= 1
        roominfo['meta']['private_meta']['allowed'].append(server_id)
        self.update_room(invite['room'], roominfo)
        self.__bot.db.save_data()

    async def join_room(self, user, room, channel, webhook_id=None, platform='discord'):
        roominfo = self.get_room(room)
        if not roominfo:
            raise self.RoomNotFoundError('invalid room')

        if not self.can_join_room(room, user, platform=platform):
            raise self.RoomNotFoundError('cannot join room')

        if self.check_duplicate(channel, platform=platform):
            raise restrictions.AlreadyConnected()

        if not platform=='discord':
            support = self.__bot.platforms[platform]
            channel_id = support.get_id(channel)
            user_id = support.get_id(user)
            guild_id = support.get_id(support.server(user))
        else:
            channel_id = channel.id
            user_id = user.id
            guild_id = user.guild.id

        if (
                str(guild_id) in roominfo['meta']['banned']
        ) and (not user_id in self.__bot.moderators and not self.moderator_override):
            raise self.RoomBannedError('banned from room')

        if roominfo['meta']['private']:
            if (
                    not guild_id in roominfo['meta']['private_meta']['allowed'] and
                    not guild_id == roominfo['meta']['private_meta']['server']
            ) and (not user_id in self.__bot.moderators and not self.moderator_override):
                raise ValueError('forbidden')

        guild_id = str(guild_id)

        if platform == 'discord':
            if not webhook_id:
                raise ValueError('webhook must be provided for discord')
            ids = [webhook_id, channel_id]
        else:
            ids = [channel_id]
            if webhook_id:
                ids = [webhook_id, channel_id]

        if not platform in roominfo.keys():
            self.__bot.db['rooms'][room].update({platform:{}})

        if guild_id in self.__bot.db['rooms'][room][platform].keys():
            raise ValueError('already joined')

        self.__bot.db['rooms'][room][platform].update({guild_id: ids})
        self.__bot.db.save_data()

    async def leave_room(self, guild, room, platform='discord'):
        roominfo = self.get_room(room)
        if not roominfo:
            raise ValueError('invalid room')

        support = None

        if not platform == 'discord':
            support = self.__bot.platforms[platform]

        if platform == 'discord':
            guild_id = guild.id
        else:
            guild_id = support.get_id(guild)

        guild_id = str(guild_id)

        if not platform in roominfo.keys():
            raise ValueError('not joined')

        if not guild_id in self.__bot.db['rooms'][room][platform].keys():
            raise ValueError('not joined')

        self.__bot.db['rooms'][room][platform].pop(guild_id)
        self.__bot.db.save_data()

    async def optimize(self):
        """Optimizes data to avoid having to fetch webhooks.
        This decreases latency incuded by message bridging prep."""
        for room in self.__bot.db['rooms']:
            if not 'discord' in self.__bot.db['rooms'][room].keys():
                continue
            for guild in self.__bot.db['rooms'][room]['discord']:
                if len(self.__bot.db['rooms'][room]['discord'][guild])==1:
                    try:
                        hook = await self.__bot.fetch_webhook(self.__bot.db['rooms'][room]['discord'][guild][0])
                    except:
                        continue
                    self.__bot.db['rooms'][room]['discord'][guild].append(hook.channel_id)
        self.__bot.db.save_data()

    async def convert_1(self):
        """Converts data structure to be v2.1.0-compatible.
        Eliminates the need for a lot of unneeded keys."""
        if not 'rules' in self.__bot.db.keys():
            # conversion is not needed
            return
        for room in self.__bot.db['rooms']:
            self.__bot.db['rooms'][room] = {'meta':{
                'rules': self.__bot.db['rules'][room],
                'restricted': room in self.__bot.db['restricted'],
                'locked': room in self.__bot.db['locked'],
                'private': False,
                'private_meta': {
                    'server': None,
                    'allowed': [],
                    'invites': [],
                    'platform': 'discord'
                },
                'emoji': self.__bot.db['roomemoji'][room] if room in self.__bot.db['roomemoji'].keys() else None,
                'description': self.__bot.db['descriptions'][room] if room in self.__bot.db['descriptions'].keys() else None,
                'display_name': None
            },'discord': self.__bot.db['rooms'][room]}
            if room in self.__bot.db['rooms_revolt'].keys():
                self.__bot.db['rooms'][room].update({'revolt': self.__bot.db['rooms_revolt'][room]})
            if room in self.__bot.db['rooms_guilded'].keys():
                self.__bot.db['rooms'][room].update({'guilded': self.__bot.db['rooms_guilded'][room]})

        self.__bot.db.pop('rooms_revolt')
        self.__bot.db.pop('rooms_guilded')
        self.__bot.db.pop('rules')
        self.__bot.db.pop('restricted')
        self.__bot.db.pop('locked')
        self.__bot.db.pop('roomemoji')
        self.__bot.db.pop('descriptions')

        # not sure what to do about the data stored in rooms_revolt key now...
        # maybe delete the key entirely? or keep it in case conversion went wrong?

        self.__bot.db.save_data()

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

        if self.__bot.config['compress_cache']:
            await self.__bot.loop.run_in_executor(None, lambda: compress_json.dump(data,filename+'.lzma'))
        else:
            with open(filename, "w+") as file:
                await self.__bot.loop.run_in_executor(None, lambda: json.dump(data, file))
        del data
        self.backup_running = False
        return

    async def restore(self,filename='bridge.json'):
        if self.restored:
            raise RuntimeError('Already restored from backup')
        if self.__bot.config['compress_cache']:
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
                reactions=data['messages'][f'{x}']['reactions'] if 'reactions' in list(data['messages'][f'{x}'].keys()) else {},
                reply_v2=data['messages'][f'{x}']['reply_v2'] if 'reply_v2' in list(data['messages'][f'{x}'].keys()) else False
            )
            self.bridged.append(msg)

        self.prs = data['posts']
        del data
        self.restored = True
        return

    async def run_security(self, message):
        responses = {}
        unsafe = False

        for plugin in self.__bot.loaded_plugins:
            script = self.__bot.loaded_plugins[plugin]

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
        for thread in self.__bot.db['threads']:
            if int(thread)==thread_id or int(thread_id) in self.__bot.db['threads'][thread].values():
                return {thread: self.__bot.db['threads'][thread]}
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

    async def delete_message(self,message):
        self.bridged.remove(message)

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
        if not self.__bot.config['enable_exp'] or user_id==self.__bot.user.id:
            return 0, False
        if not f'{user_id}' in self.__bot.db['exp'].keys():
            self.__bot.db['exp'].update({f'{user_id}':{'experience':0,'level':1,'progress':0}})
        t = time.time()
        if f'{user_id}' in level_cooldown.keys():
            if t < level_cooldown[f'{user_id}']:
                return self.__bot.db['exp'][f'{user_id}']['experience'], self.__bot.db['exp'][f'{user_id}']['progress'] >= 1
            else:
                level_cooldown[f'{user_id}'] = round(time.time()) + self.__bot.config['exp_cooldown']
        else:
            level_cooldown.update({f'{user_id}': round(time.time()) + self.__bot.config['exp_cooldown']})
        self.__bot.db['exp'][f'{user_id}']['experience'] += random.randint(80,120)
        ratio, remaining = await self.progression(user_id)
        if ratio >= 1:
            self.__bot.db['exp'][f'{user_id}']['experience'] = -remaining
            self.__bot.db['exp'][f'{user_id}']['level'] += 1
            newratio, _remaining = await self.progression(user_id)
        else:
            newratio = ratio
        self.__bot.db['exp'][f'{user_id}']['progress'] = newratio
        await self.__bot.loop.run_in_executor(None, lambda: self.__bot.db.save_data())
        return self.__bot.db['exp'][f'{user_id}']['experience'], ratio >= 1

    async def progression(self, user_id):
        base = 1000
        rate = 1.4
        target = base * (rate ** self.__bot.db['exp'][f'{user_id}']['level'])
        return (
            self.__bot.db['exp'][f'{user_id}']['experience']/target, target-self.__bot.db['exp'][f'{user_id}']['experience']
        )

    async def roomstats(self, roomname):
        online = 0
        members = 0
        guilds = 0
        for platform in self.__bot.db['rooms'][roomname]:
            if platform == 'meta':
                continue

            support = None
            if not platform == 'discord':
                support = self.__bot.platforms[platform]

            for guild_id in self.__bot.db['rooms'][roomname][platform]:
                try:
                    if platform=='discord':
                        guild = self.__bot.get_guild(int(guild_id))
                    else:
                        try:
                            guild = support.get_server(int(guild_id))
                            if not guild:
                                raise Exception()
                        except:
                            guild = await support.fetch_server(int(guild_id))
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
            ch = self.__bot.get_channel(int(msg.channel_id))
            todelete = await ch.fetch_message(int(msg.id))
            await todelete.delete()
        else:
            source_support = self.__bot.platforms[msg.source]
            try:
                ch = source_support.get_channel(msg.channel_id)
            except:
                ch = await source_support.fetch_channel(msg.channel_id)
            todelete = await source_support.fetch_message(ch,msg.id)
            await source_support.delete(todelete)

    async def delete_copies(self, message):
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message)
        threads = []

        async def delete_discord(msgs):
            count = 0
            threads = []
            for key in list(self.__bot.db['rooms'][msg.room]['discord'].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.__bot.get_guild(int(key))
                try:
                    try:
                        webhook = self.__bot.bridge.webhook_cache.get_webhook([
                            f'{self.__bot.db["rooms"][msg.room]["discord"][f"{guild.id}"][0]}'
                        ])
                    except:
                        try:
                            webhook = await self.__bot.fetch_webhook(self.__bot.db['rooms'][msg.room]['discord'][key][0])
                            self.__bot.bridge.webhook_cache.store_webhook(webhook, webhook.id, guild.id)
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
            try:
                await asyncio.gather(*threads)
            except:
                pass
            return count

        async def delete_others(msgs, target):
            count = 0
            threads = []
            support = self.__bot.platforms[target]
            for key in list(self.__bot.db['rooms'][msg.room][target].keys()):
                if not key in list(msgs.keys()):
                    continue

                channel = support.get_channel(msgs[key][0])
                todelete = await support.fetch_message(channel, msgs[key][1])
                try:
                    threads.append(asyncio.create_task(
                        support.delete_message(todelete)
                    ))
                    count += 1
                except:
                    pass
            try:
                await asyncio.gather(*threads)
            except:
                pass
            return count

        if msg.source=='discord':
            threads.append(asyncio.create_task(
                delete_discord(msg.copies)
            ))
        else:
            threads.append(asyncio.create_task(
                delete_others(msg.copies,msg.source)
            ))

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                threads.append(asyncio.create_task(
                    delete_discord(msg.external_copies['discord'])
                ))
            else:
                threads.append(asyncio.create_task(
                    delete_others(msg.external_copies[msg.source],msg.source)
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
                    user = self.__bot.revolt_client.get_user(userid)
                    display_name = user.display_name or user.name
                elif source == 'guilded':
                    user = self.__bot.guilded_client.get_user(userid)
                    display_name = user.display_name or user.name
                else:
                    user = self.__bot.get_user(userid)
                    display_name = user.global_name or user.name
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
                        channel = self.__bot.revolt_client.get_channel(channelid)
                    except:
                        channel = await self.__bot.revolt_client.fetch_channel(channelid)
                elif source == 'guilded':
                    channel = self.__bot.guilded_client.get_channel(channelid)
                else:
                    channel = self.__bot.get_channel(channelid)
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

        if source == 'guilded':
            lines = text.split('\n')
            offset = 0
            for index in range(len(lines)):
                try:
                    line = lines[index-offset]
                except:
                    break
                if line.startswith('![](https://cdn.gilcdn.com/ContentMediaGenericFiles'):
                    try:
                        lines.pop(index-offset)
                        offset += 1
                    except:
                        pass
                elif line.startswith('![](') and line.endswith(')'):
                    lines[index-offset] = line.replace('![](','',1)[:-1]

            if len(lines) == 0:
                text = ''
            else:
                text = '\n'.join(lines)

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

            for key in list(self.__bot.db['rooms'][msg.room]['discord'].keys()):
                if not key in list(msgs.keys()):
                    continue

                # Fetch webhook
                try:
                    webhook = await self.__bot.fetch_webhook(self.__bot.db['rooms'][msg.room]['discord'][key][0])
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

        async def edit_others(msgs,target,friendly=False):
            source_support = self.__bot.platforms[msg.source] if msg.source != 'discord' else None
            dest_support = self.__bot.platforms[target]
            if friendly:
                if msg.source == 'discord':
                    text = await self.make_friendly(content, msg.source)
                else:
                    text = await source_support.make_friendly(content)
            else:
                text = content

            for key in list(self.__bot.db['rooms'][msg.room][target].keys()):
                if not key in list(msgs.keys()):
                    continue

                try:
                    try:
                        ch = dest_support.get_channel(msgs[key][0])
                    except:
                        ch = await dest_support.fetch_channel(msgs[key][0])
                    toedit = await dest_support.fetch_message(ch, msgs[key][1])
                    await dest_support.edit(toedit, text)
                except:
                    traceback.print_exc()
                    continue

        if msg.source=='discord':
            threads.append(asyncio.create_task(
                edit_discord(msg.copies)
            ))
        else:
            threads.append(asyncio.create_task(
                edit_others(msg.copies, msg.source)
            ))

        for platform in list(msg.external_copies.keys()):
            if platform=='discord':
                threads.append(asyncio.create_task(
                    edit_discord(msg.external_copies['discord'],friendly=True)
                ))
            else:
                threads.append(asyncio.create_task(
                    edit_others(msg.external_copies[platform],platform,friendly=True)
                ))

        await asyncio.gather(*threads)

    async def send(self, room: str, message,
                   platform: str = 'discord', system: bool = False,
                   extbridge=False, id_override=None, ignore=None, source='discord',
                   content_override=None, alert=None):
        if is_room_locked(room,self.__bot.db) and not message.author.id in self.__bot.admins:
            return
        if ignore is None:
            ignore = []

        alert_embed = None
        alert_text = None
        if alert:
            system = True

            alert_color = {
                'emergency': self.__bot.colors.error,
                'warning': self.__bot.colors.warning,
                'advisory': self.__bot.colors.blurple,
                'clear': self.__bot.colors.success
            }

            alert_embed = nextcord.Embed(
                title=(
                    self.__bot.ui_emojis.success if alert['severity'] == 'clear' else self.__bot.ui_emojis.warning
                ) + ' ' + self.alert.titles[alert['type']][alert['severity']],
                description=alert['description'], color=alert_color[alert['severity']],
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            alert_embed.set_footer(
                text=(
                    f'{self.__bot.user.global_name or self.__bot.user.name} moderators have been alerted of this '+
                    'risk. Feel free to report any more information that you may have to us.'
                )
            )
            alert_embed.add_field(
                name='What should I do?',
                value='\n'.join(self.alert.precautions[alert['type']][alert['severity']])
            )

            alert_text = (
                '# '+self.alert.titles[alert['type']][alert['severity']]+'\n\n'+alert['description']+'\n\n**What '+
                'should I do?**\n'+'\n'.join(self.alert.precautions[alert['type']][alert['severity']])
            )

        # WIP orphan message system.
        # if type(message) is dict:
        #     orphan = True
        # else:
        #     orphan = False
        #     message = {
        #         'id': message.id,
        #         'author': message.author,
        #         'guild': message.guild,
        #         'content': message.content,
        #         'channel': message.channel,
        #         'attachments': message.attachments,
        #         'embeds': message.embeds,
        #         'reference': message.reference
        #     }

        selector = language.get_selector('bridge.bridge',userid=message.author.id)

        source_support = self.__bot.platforms[source] if source != 'discord' else None
        dest_support = self.__bot.platforms[platform] if platform != 'discord' else None

        if not source in self.__bot.platforms.keys() and not source=='discord':
            raise ValueError('invalid platform')

        if not platform in self.__bot.platforms.keys() and not platform=='discord':
            raise ValueError('invalid platform')

        # redundant check in case on_message or plugin does not respect ban status, and also
        # for under attack mode
        if source == 'discord':
            if (
                    f'{message.author.id}' in self.__bot.db['banned'].keys() or
                    f'{message.guild.id}' in self.__bot.db['banned'].keys() or
                    f'{message.guild.id}' in self.__bot.db['rooms'][room]['meta']['banned'] or
                    f'{message.guild.id}' in self.__bot.db['underattack']
            ):
                return
        else:
            if (
                    f'{source_support.get_id(source_support.author(message))}' in self.__bot.db['banned'].keys() or
                    f'{source_support.get_id(source_support.server(message))}' in self.__bot.db['banned'].keys() or
                    f'{source_support.get_id(source_support.author(message))}' in self.__bot.db['rooms'][room]['meta']['banned'] or
                    f'{source_support.get_id(source_support.server(message))}' in self.__bot.db['underattack']
            ):
                return

        if not platform in self.__bot.db['rooms'][room].keys():
            return

        guilds = self.__bot.db['rooms'][room][platform]

        is_pr = room == self.__bot.config['posts_room'] and (
            self.__bot.config['allow_prs'] if 'allow_prs' in list(self.__bot.config.keys()) else False or
            self.__bot.config['allow_posts'] if 'allow_posts' in list(self.__bot.config.keys()) else False
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
        temp_pr_ref = room == self.__bot.config['posts_ref_room'] and (
            self.__bot.config['allow_prs'] if 'allow_prs' in list(self.__bot.config.keys()) else False or
            self.__bot.config['allow_posts'] if 'allow_posts' in list(self.__bot.config.keys()) else False
        )
        if temp_pr_ref and message.content.startswith('[') and source==platform=='discord' and (
                self.__bot.config['allow_prs'] if 'allow_prs' in list(self.__bot.config.keys()) else False or
                self.__bot.config['allow_posts'] if 'allow_posts' in list(self.__bot.config.keys()) else False
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
                    lambda e: e.name == name and not e.id in skip and e.guild_id in self.__bot.db['emojis'],
                    self.__bot.emojis)
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
                    await message.channel.send(selector.get('delete_fail'))
                    raise SelfDeleteException('Could not delete parent message')
                elif is_pr:
                    await message.channel.send(selector.fget('post_id',values={'post_id': pr_id}), reference=message)
                should_resend = False
        elif is_pr and source == platform:
            if not source=='discord':
                channel = source_support.channel(message)
                await source_support.send(channel, selector.fget('post_id',values={'post_id': pr_id}), reply=message)

        # Username
        if source == 'discord':
            author = message.author.global_name if message.author.global_name else message.author.name
            if f'{message.author.id}' in list(self.__bot.db['nicknames'].keys()):
                author = self.__bot.db['nicknames'][f'{message.author.id}']
        else:
            author_obj = source_support.author(message)
            author = source_support.display_name(author_obj)
            if f'{source_support.get_id(author_obj)}' in list(self.__bot.db['nicknames'].keys()):
                author = self.__bot.db['nicknames'][f'{source_support.get_id(author_obj)}']

        # Get dedupe
        if source == 'discord':
            author_id = message.author.id
            is_bot = message.author.bot
        else:
            author_id = source_support.get_id(source_support.author(message))
            is_bot = source_support.is_bot(source_support.author(message))

        dedupe = await self.dedupe_name(author, author_id)
        should_dedupe = dedupe > -1

        # Emoji time
        useremoji = None
        if self.__bot.config['enable_emoji_tags'] and not system:
            while True:
                author_split = [*author]
                if len(author_split) == 1:
                    if source == 'discord':
                        author = message.author.name
                    else:
                        author = source_support.user_name(message.author)
                    break
                if pymoji.is_emoji(author_split[len(author_split)-1]):
                    author_split.pop(len(author_split)-1)
                    author = ''.join(author_split)
                    while author.endswith(' '):
                        author = author[:-1]
                else:
                    break
            if (
                    author_id == self.__bot.config['owner'] or (
                            author_id == self.__bot.config['owner_external'][source]
                            if source in self.__bot.config['owner_external'].keys() else False
                    )
            ):
                useremoji = '\U0001F451'
            elif author_id in self.__bot.admins:
                useremoji = '\U0001F510'
            elif author_id in self.__bot.moderators:
                useremoji = '\U0001F6E1'
            elif author_id in self.__bot.db['trusted']:
                useremoji = '\U0001F31F'
            elif is_bot:
                useremoji = '\U0001F916'
            elif should_dedupe:
                useremoji = dedupe_emojis[dedupe]

        if content_override:
            msg_content = content_override
        else:
            if source=='discord':
                msg_content = message.content
            else:
                msg_content = source_support.content(message)

        friendlified = False
        friendly_content = None
        if not source == platform:
            friendlified = True
            if source=='discord':
                friendly_content = await self.make_friendly(msg_content, source)
            else:
                try:
                    friendly_content = await source_support.make_friendly(msg_content)
                except platform_base.MissingImplementation:
                    friendly_content = msg_content

        message_ids = {}
        urls = {}
        trimmed = None
        replying = False
        global_reply_v2 = False

        # Threading
        thread_urls = {}
        threads = []
        tb_v2 = source=='discord'
        size_total = 0
        max_files = 0

        # Check attachments size
        if source=='discord':
            attachments = message.attachments
        else:
            attachments = source_support.attachments(message)
        for attachment in attachments:
            if system:
                break
            if source=='discord':
                size_total += attachment.size
            else:
                size_total += source_support.attachment_size(attachment)
            if size_total > 25000000:
                if not self.__bot.config['suppress_filesize_warning'] and source == platform:
                    if source=='discord':
                        await message.channel.send(selector.get('filesize_limit'),
                                                   reference=message)
                    else:
                        await source_support.send(source_support.channel(message),selector.get('filesize_limit'),
                                                  special={'reply':message})
                break
            max_files += 1

        # Attachment processing
        async def get_files(attachments):
            files = []

            async def to_file(source_file):
                if platform == 'discord':
                    if source == 'discord':
                        try:
                            return await source_file.to_file(use_cached=True, spoiler=source_file.is_spoiler(), force_close=False)
                        except:
                            try:
                                return await source_file.to_file(use_cached=True, spoiler=False, force_close=False)
                            except:
                                return await source_file.to_file(use_cached=False, spoiler=False, force_close=False)
                    else:
                        return await source_support.to_discord_file(source_file)
                else:
                    if source == 'discord':
                        return await dest_support.to_platform_file(source_file)
                    else:
                        # use nextcord.File as a universal file object
                        return await dest_support.to_platform_file(
                            await source_support.to_discord_file(source_file)
                        )

            index = 0
            for attachment in attachments:
                if system:
                    break
                if source == 'discord':
                    if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                            not 'image' in attachment.content_type and not 'text/plain' in attachment.content_type and
                            self.__bot.config['safe_filetypes']
                    ) or attachment.size > 25000000:
                        continue
                else:
                    attachment_size = source_support.attachment_size(attachment)
                    content_type = source_support.attachment_size(attachment)
                    if (
                            not 'audio' in content_type and not 'video' in content_type and not 'image' in content.type
                            and not 'text/plain' in content_type and self.__bot.config['safe_filetypes']
                    ) or attachment_size > 25000000 or not dest_support.attachment_type_allowed(content_type):
                        continue

                try:
                    files.append(await to_file(attachment))
                except platform_base.MissingImplementation:
                    continue
                index += 1
                if index >= max_files:
                    break

            return files

        files = await get_files(message.attachments)

        # Broadcast message
        for guild in list(guilds.keys()):
            if source == 'discord':
                compare_guild = message.guild
            else:
                compare_guild = source_support.server(message)
            if platform=='discord':
                reply_v2 = self.get_reply_style(int(guild)) == 1
                if source == 'discord':
                    sameguild = (guild == str(message.guild.id)) if message.guild else False
                else:
                    sameguild = (guild == source_support.get_id(compare_guild)) if compare_guild else False
            else:
                reply_v2 = False
                if not compare_guild:
                    sameguild = False
                else:
                    if source == 'discord':
                        guild_id = compare_guild.id
                    else:
                        guild_id = source_support.get_id(compare_guild)
                    sameguild = (guild == str(guild_id))

            try:
                bans = self.__bot.db['blocked'][str(guild)]
                if source=='discord':
                    guildban = message.guild.id in bans
                else:
                    guildban = source_support.server(message) in bans
                if (author_id in bans or guildban) and not sameguild:
                    continue
            except:
                pass

            # Destination guild object
            if platform == 'discord':
                destguild = self.__bot.get_guild(int(guild))
                if not destguild:
                    continue
            else:
                try:
                    destguild = dest_support.get_server(guild)
                    if not destguild:
                        continue
                except:
                    continue

            if platform == 'discord':
                if destguild.id in ignore:
                    continue
            else:
                if dest_support.get_id(destguild) in ignore:
                    continue

            if sameguild and not system:
                if not should_resend or not platform=='discord':
                    if platform=='discord':
                        urls.update({f'{message.guild.id}':f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'})
                    else:
                        try:
                            urls.update({f'{source_support.server(message)}': source_support.url(message)})
                        except platform_base.MissingImplementation:
                            pass
                    continue

            # Reply processing
            reply_msg = None
            components = None
            pr_actionrow = None
            replytext = ''

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
                            nextcord.ui.Button(style=button_style,
                                               label=selector.fget('post_id',values={'post_id': pr_id}),
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
                                    nextcord.ui.Button(style=nextcord.ButtonStyle.url,
                                                       label=selector.fget('post_reference',values={'post_id': pr_id}),
                                                       emoji='\U0001F517',url=await msg.fetch_url(guild))
                                )
                            except:
                                pr_actionrow = ui.ActionRow(
                                    nextcord.ui.Button(style=nextcord.ButtonStyle.gray,
                                                       label=selector.fget('post_reference',values={'post_id': pr_id}),
                                                       emoji='\U0001F517', disabled=True)
                                )
                    if pr_actionrow:
                        components = ui.View()
                        components.add_row(pr_actionrow)
                if reply_msg:
                    if not trimmed:
                        try:
                            if source=='discord':
                                content = message.reference.cached_message.content
                            else:
                                # for NUPS, plugins process the content, not unifier
                                msg = source_support.reply(message)
                                if type(msg) is str or type(msg) is int:
                                    msg = await source_support.fetch_message(
                                        source_support.channel(message),msg
                                    )
                                content = source_support.content(msg)
                        except:
                            if source=='discord':
                                msg = await message.channel.fetch_message(message.reference.message_id)
                            else:
                                raise
                            content = msg.content

                        if source=='discord':
                            used_reply_v2 = self.get_reply_style(message.reference.guild_id) == 1
                            if reply_msg.reply_v2 and (
                                    str(message.reference.guild_id) in reply_msg.copies.keys() or
                                    reply_msg.webhook
                            ) and used_reply_v2:
                                # remove "replying to" text
                                content_comp = content.split('\n')
                                if len(content_comp) == 1:
                                    content = ''
                                else:
                                    content_comp.pop(0)
                                    content = '\n'.join(content_comp)

                        clean_content = nextcord.utils.remove_markdown(content)
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
                            user = self.__bot.get_user(userid)
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
                        if reply_msg.source=='discord':
                            user = self.__bot.get_user(int(reply_msg.author_id))
                            author_text = f'@{user.global_name or user.name}'
                        else:
                            user = source_support.get_user(reply_msg.author_id)
                            author_text = f'@{source_support.display_name(user)}'
                        if f'{reply_msg.author_id}' in list(self.__bot.db['nicknames'].keys()):
                            author_text = '@'+self.__bot.db['nicknames'][f'{reply_msg.author_id}']
                    except:
                        pass

                    # Prevent empty buttons
                    try:
                        if source == 'discord':
                            count = len(message.reference.cached_message.embeds) + len(message.reference.cached_message.attachments)
                        else:
                            reply_msg_id = source_support.reply(message)
                            if type(reply_msg_id) is str or type(reply_msg_id) is int:
                                msg = await source_support.fetch_message(
                                    source_support.channel(message), reply_msg_id
                                )
                            else:
                                msg = reply_msg_id
                            count = len(source_support.embeds(msg)) + len(source_support.attachments(msg))
                    except:
                        if source == 'discord':
                            msg = await message.channel.fetch_message(message.reference.message_id)
                        else:
                            raise
                        count = len(msg.embeds) + len(msg.attachments)

                    if len(trimmed)==0:
                        content_btn = nextcord.ui.Button(
                            style=button_style,label=f'x{count}', emoji='\U0001F3DE', disabled=True
                        )
                        replytext = f'*:park: x{count}*'
                    else:
                        content_btn = nextcord.ui.Button(
                            style=button_style, label=trimmed, disabled=True
                        )
                        replytext = f'*{trimmed}*'

                    global_reply_v2 = True

                    # Add PR buttons too.
                    if is_pr or is_pr_ref:
                        components = ui.View()
                        try:
                            if not reply_v2:
                                components.add_rows(
                                    pr_actionrow,
                                    ui.ActionRow(
                                        nextcord.ui.Button(
                                            style=nextcord.ButtonStyle.url,
                                            label=selector.fget('replying',values={'user': author_text}),
                                            url=await reply_msg.fetch_url(guild)
                                        )
                                    ),
                                    ui.ActionRow(
                                        content_btn
                                    )
                                )
                            else:
                                components.add_row(
                                    pr_actionrow
                                )
                            replytext = (
                                f'-# {arrow_unicode} ' +
                                f'[{selector.fget("replying", values={"user": author_text})}](<{await reply_msg.fetch_url(guild)}>)' +
                                f' - {replytext}'
                            )
                        except:
                            if not reply_v2:
                                components.add_rows(
                                    pr_actionrow,
                                    ui.ActionRow(
                                        nextcord.ui.Button(
                                            style=nextcord.ButtonStyle.gray,
                                            label=selector.fget('replying',values={'user': '[unknown]'}),
                                            disabled=True
                                        )
                                    )
                                )
                            else:
                                components.add_row(
                                    pr_actionrow
                                )
                            replytext = f'-# {arrow_unicode} {selector.fget("replying", values={"user": "[unknown"})}\n'
                    else:
                        try:
                            if not reply_v2:
                                components = ui.View()
                                components.add_rows(
                                    ui.ActionRow(
                                        nextcord.ui.Button(
                                            style=nextcord.ButtonStyle.url,
                                            label=selector.fget('replying',values={'user': author_text}),
                                            url=await reply_msg.fetch_url(guild)
                                        )
                                    ),
                                    ui.ActionRow(
                                        content_btn
                                    )
                                )
                            replytext = (
                                f'-# {arrow_unicode} '+
                                f'[{selector.fget("replying",values={"user": author_text})}](<{await reply_msg.fetch_url(guild)}>)'+
                                f' - {replytext}\n'
                            )
                        except:
                            if not reply_v2:
                                components = ui.View()
                                components.add_rows(
                                    ui.ActionRow(
                                        nextcord.ui.Button(
                                            style=nextcord.ButtonStyle.gray,
                                            label=selector.fget('replying',values={'user': '[unknown]'}),
                                            disabled=True
                                        )
                                    ),
                                    ui.ActionRow(
                                        content_btn
                                    )
                                )
                            replytext = f'-# {arrow_unicode} {selector.fget("replying", values={"user": "[unknown]"})}\n'
                elif replying:
                    global_reply_v2 = True
                    try:
                        if source == 'discord':
                            if message.reference.cached_message:
                                authid = message.reference.cached_message.author.id
                            else:
                                authmsg = await message.channel.fetch_message(message.reference.message_id)
                                authid = authmsg.author.id
                        else:
                            reply_msg_id = source_support.reply(message)
                            if type(reply_msg_id) is str or type(reply_msg_id) is int:
                                authmsg = await source_support.fetch_message(
                                    source_support.channel(message), reply_msg_id
                                )
                            else:
                                authmsg = reply_msg_id
                            authid = source_support.get_id(source_support.author(authmsg))
                    except:
                        authid = None
                    if platform == 'discord':
                        botext = False
                    else:
                        botext = authid == source_support.bot_id()

                    if authid==self.__bot.user.id or botext:
                        reply_row = ui.ActionRow(
                            nextcord.ui.Button(style=nextcord.ButtonStyle.gray,
                                               label=selector.fget('replying',values={'user': '[system]'}),
                                               disabled=True)
                        )
                        replytext = f'-# {arrow_unicode} {selector.fget("replying", values={"user": "[system]"})}\n'
                    else:
                        reply_row = ui.ActionRow(
                            nextcord.ui.Button(style=nextcord.ButtonStyle.gray,
                                               label=selector.fget('replying',values={'user': '[unknown]'}),
                                               disabled=True)
                        )
                        replytext = f'-# {arrow_unicode} {selector.fget("replying", values={"user": "[unknown]"})}\n'
                    if not reply_v2:
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
                    elif pr_actionrow:
                        components = ui.MessageComponents()
                        components.add_rows(
                            pr_actionrow
                        )

            # Avatar
            try:
                if f'{author_id}' in self.__bot.db['avatars']:
                    url = self.__bot.db['avatars'][f'{author_id}']
                else:
                    if source == 'discord':
                        url = message.author.avatar.url
                    else:
                        url = source_support.avatar(message.author)
            except:
                url = None

            if system:
                try:
                    url = self.__bot.user.avatar.url
                except:
                    url = None

            # Add system identifier
            msg_author = author
            if system:
                msg_author = (
                    self.__bot.user.global_name if self.__bot.user.global_name else self.__bot.user.name
                )+ ' (system)'

            # Send message
            embeds = message.embeds
            if not message.author.bot and not system:
                embeds = []

            if msg_author.lower()==f'{self.__bot.user.name} (system)'.lower() and not system:
                msg_author = '[hidden username]'

            if platform=='discord':
                if not reply_v2:
                    replytext = ''
                msg_author_dc = msg_author
                if len(msg_author) > 35:
                    msg_author_dc = msg_author[:-(len(msg_author) - 35)]
                    if useremoji:
                        msg_author_dc = msg_author[:-2]

                if useremoji:
                    msg_author_dc = msg_author_dc + ' ' + useremoji

                webhook = None
                try:
                    webhook = self.__bot.bridge.webhook_cache.get_webhook(
                        f'{self.__bot.db["rooms"][room]["discord"][guild][0]}'
                    )
                except:
                    # It'd be better to fetch all instead of individual webhooks here, so they can all be cached
                    hooks = await destguild.webhooks()
                    identifiers = [hook.id for hook in hooks]
                    self.__bot.bridge.webhook_cache.store_webhooks(hooks, identifiers, [int(guild)] * len(hooks))
                    for hook in hooks:
                        if hook.id in self.__bot.db['rooms'][room]['discord'][guild]:
                            webhook = hook
                            break
                if not webhook:
                    continue

                touse_mentions = mentions
                alert_pings = ''
                if alert:
                    embeds = [alert_embed]
                    friendly_content = msg_content = ''
                    if not alert['severity'] == 'advisory' and room == self.__bot.config['alerts_room']:
                        toping = [
                            f'<@{user.id}>' for user in destguild.members
                            if user.guild_permissions.ban_members and not user.bot
                        ]
                        if destguild.id == self.__bot.config['home_guild']:
                            toping.append(f'<@&{self.__bot.config["moderator_role"]}>')
                        alert_pings = ' '.join(toping)
                        touse_mentions = emergency_mentions

                # fun fact: tbsend stands for "threaded bridge send", but we read it
                # as "turbo send", because it sounds cooler and tbsend is what lets
                # unifier bridge using webhooks with ultra low latency.
                async def tbsend(webhook,url,msg_author_dc,embeds,_message,mentions,components,sameguild,
                                 destguild):
                    try:
                        tosend_content = replytext+(friendly_content if friendlified else msg_content)
                        if len(tosend_content) > 2000:
                            tosend_content = tosend_content[:-(len(tosend_content)-2000)]
                            if not components:
                                components = ui.MessageComponents()
                            components.add_row(
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.gray,label='[Message truncated]',disabled=True
                                    )
                                )
                            )
                        if self.__bot.config['use_multicore']:
                            async with aiohttp.ClientSession() as session:
                                webhook.session = session
                                msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                         content=tosend_content, files=files, allowed_mentions=mentions, view=(
                                                             components if components and not system else ui.MessageComponents()
                                                         ), wait=True)
                        else:
                            msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                     content=tosend_content, files=files, allowed_mentions=mentions,
                                                     view=(
                                                         components if components and not system else ui.MessageComponents()
                                                     ), wait=True)
                    except:
                        return None
                    tbresult = [
                        {f'{destguild.id}': [webhook.channel.id, msg.id]},
                        {f'{destguild.id}': f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'},
                        [sameguild, msg.id],
                        reply_v2
                    ]
                    return tbresult

                if tb_v2 and not alert:
                    if self.__bot.config['use_multicore']:
                        # noinspection PyTypeChecker
                        threads.append(
                            Worker(
                                target=tbsend,
                                args=(
                                    webhook, url, msg_author_dc, embeds, message,
                                    touse_mentions, components, sameguild,
                                    destguild
                                )
                            )
                        )
                        threads[len(threads) - 1].start()
                    else:
                        threads.append(asyncio.create_task(tbsend(webhook, url, msg_author_dc, embeds, message,
                                                                  touse_mentions, components, sameguild,
                                                                  destguild)))
                else:
                    try:
                        tosend_content = replytext + alert_pings + (friendly_content if friendlified else msg_content)
                        if len(tosend_content) > 2000:
                            tosend_content = tosend_content[:-(len(tosend_content) - 2000)]
                            if not components:
                                components = ui.MessageComponents()
                            components.add_row(
                                ui.ActionRow(
                                    nextcord.ui.Button(
                                        style=nextcord.ButtonStyle.gray, label='[Message truncated]', disabled=True
                                    )
                                )
                            )
                        msg = await webhook.send(avatar_url=url, username=msg_author_dc, embeds=embeds,
                                                 content=tosend_content,
                                                 files=files, allowed_mentions=touse_mentions, view=(
                                                     components if components and not system else ui.MessageComponents()
                                                 ), wait=True)
                    except:
                        continue
                    message_ids.update({f'{destguild.id}':[webhook.channel.id,msg.id]})
                    urls.update({f'{destguild.id}':f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'})
            else:
                ch_id = self.__bot.db['rooms'][room][platform][guild][0]
                if len(self.__bot.db['rooms'][room][platform][guild]) > 1:
                    ch_id = self.__bot.db['rooms'][room][platform][guild][1]

                try:
                    ch = dest_support.get_channel(ch_id)

                    if not ch:
                        raise Exception() # runs fetch_channel if ch is none
                except:
                    ch = await dest_support.fetch_channel(ch_id)

                reply = reply_msg

                color = None
                if str(author_id) in list(self.__bot.db['colors'].keys()):
                    color = self.__bot.db['colors'][str(author_id)]
                    if color == 'inherit':
                        try:
                            if source == 'discord':
                                color_obj = message.author.roles[len(message.author.roles) - 1].colour
                                color = f'{color_obj.r:02x}{color_obj.g:02x}{color_obj.b:02x}'
                            else:
                                roles = source_support.roles(source_support.author(message))
                                color = source_support.get_hex(roles[len(roles)-1])
                        except:
                            pass

                if alert:
                    friendly_content = msg_content = alert_text

                async def tbsend(msg_author,url,color,useremoji,reply,content):
                    files = await get_files(message.attachments)
                    special = {
                        'bridge': {
                            'name': msg_author,
                            'avatar': url,
                            'color': color,
                            'emoji': useremoji
                        },
                        'files': files if not alert else None,
                        'embeds': (
                            dest_support.convert_embeds(message.embeds) if source=='discord'
                            else dest_support.convert_embeds(
                                source_support.convert_embeds_discord(
                                    source_support.embeds(message)
                                )
                            )
                        ) if not alert else None,
                        'reply': None
                    }
                    if reply and not alert:
                        special.update({'reply': reply})
                    if replytext:
                        special.update({'reply_content': trimmed})
                    msg = await dest_support.send(
                        ch, content, special=special
                    )
                    tbresult = [
                        {f'{dest_support.get_id(destguild)}': [
                            dest_support.get_id(dest_support.channel(msg)), dest_support.get_id(msg)
                        ]},
                        None,
                        [sameguild, dest_support.get_id(msg)]
                    ]
                    try:
                        tbresult[1] = {
                            f'{dest_support.get_id(destguild)}': dest_support.url(msg)
                        }
                    except platform_base.MissingImplementation:
                        pass
                    return tbresult

                if dest_support.enable_tb:
                    threads.append(asyncio.create_task(tbsend(
                        msg_author,url,color,useremoji,reply,friendly_content if friendlified else msg_content
                    )))
                else:
                    try:
                        files = await get_files(message.attachments)
                        special = {
                            'bridge': {
                                'name': msg_author,
                                'avatar': url,
                                'color': color,
                                'emoji': useremoji
                            },
                            'files': files if not alert else None,
                            'embeds': (
                                dest_support.convert_embeds(message.embeds) if source=='discord'
                                else dest_support.convert_embeds(
                                    source_support.convert_embeds_discord(
                                        source_support.embeds(message)
                                    )
                                )
                            ) if not alert else None,
                            'reply': None
                        }
                        if reply and not alert:
                            special.update({'reply': reply})
                        if replytext:
                            special.update({'reply_content': replytext})
                        msg = await dest_support.send(
                            ch, friendly_content if friendlified else msg_content, special=special
                        )
                    except:
                        continue

                    message_ids.update({
                        str(dest_support.get_id(destguild)): [
                            dest_support.get_id(ch),dest_support.get_id(msg)
                        ]
                    })
                    try:
                        urls.update({str(dest_support.get_id(destguild)): dest_support.url(msg)})
                    except platform_base.MissingImplementation:
                        pass

        # Free up memory
        del files

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
                if result[1]:
                    urls.update(result[1])
                if result[2][0]:
                    parent_id = result[2][1]

        if not parent_id:
            parent_id = message.id

        if is_pr and not pr_id in list(self.prs.keys()) and platform == source:
            self.prs.update({pr_id: parent_id})

        if system:
            msg_author = self.__bot.user.id
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
                    self.bridged[index].external_copies[platform] = (
                        self.bridged[index].external_copies[platform] | message_ids
                    )
                except:
                    self.bridged[index].external_copies.update({platform: message_ids})
            self.bridged[index].urls = self.bridged[index].urls | urls
            self.bridged[index].reply_v2 = global_reply_v2 if not self.bridged[index].reply_v2 else self.bridged[index].reply_v2
        except:
            copies = {}
            external_copies = {}
            if source == platform:
                copies = message_ids
            else:
                external_copies = {platform: message_ids}
            if source == 'discord':
                server_id = message.guild.id
            else:
                server_id = source_support.get_id(source_support.server(message))
            if extbridge:
                try:
                    hook = await self.__bot.fetch_webhook(message.webhook_id)
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
                external_bridged=extbridge,
                reply_v2=global_reply_v2
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
        self.__bot = bot
        self.__webhooks = {}

    def store_webhook(self, webhook, identifier, server):
        if not server in self.__webhooks.keys():
            self.__webhooks.update({server: {identifier: webhook}})
        self.__webhooks[server].update({identifier: webhook})
        return len(self.__webhooks[server])

    def store_webhooks(self, webhooks: list, identifiers: list, servers: list):
        if not len(webhooks) == len(identifiers) == len(servers):
            raise ValueError('webhooks, identifiers, and servers must be the same length')

        for index in range(len(webhooks)):
            webhook = webhooks[index]
            identifier = identifiers[index]
            server = servers[index]
            if not server in self.__webhooks.keys():
                self.__webhooks.update({server: {identifier: webhook}})
            self.__webhooks[server].update({identifier: webhook})
        return len(self.__webhooks)

    def get_webhooks(self, server: int or str):
        try:
            server = int(server)
        except:
            pass
        if len(self.__webhooks[server].values())==0:
            raise ValueError('no webhooks')
        return list(self.__webhooks[server].values())

    def get_webhook(self, identifier: int or str):
        try:
            identifier = int(identifier)
        except:
            pass
        for guild in self.__webhooks.keys():
            if identifier in self.__webhooks[guild].keys():
                return self.__webhooks[guild][identifier]
        raise ValueError('invalid webhook')

    def clear(self, server: int or str = None):
        if not server:
            self.__webhooks = {}
        else:
            self.__webhooks[server] = {}
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
    @restrictions.not_banned_guild()
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
    @restrictions.not_banned_guild()
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
                            label=language.get('prev','commons.navigation',language=selector.language_set),
                            custom_id='prev',
                            disabled=page <= 0 or selection.disabled,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=language.get('next','commons.navigation',language=selector.language_set),
                            custom_id='next',
                            disabled=page >= maxpage or selection.disabled,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=language.get('search','commons.navigation',language=selector.language_set),
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
                    values={'query': query, 'results': len(emojis)},
                    language=selector.language_set
                )
                maxcount = (page + 1) * limit
                if maxcount > len(emojis):
                    maxcount = len(emojis)
                embed.set_footer(
                    text=(
                        language.fget('page','commons.search',values={
                            'page': page+1, 'maxpage': maxpage+1
                        }, language=selector.language_set)
                        + ' | ' + language.fget('result_count','commons.search',values={
                            'lower':page*limit+1,'upper':maxcount
                        }, language=selector.language_set)
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
                            label=language.get('prev','commons.navigation',language=selector.language_set),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=language.get('next','commons.navigation',language=selector.language_set),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=language.get('search','commons.navigation',language=selector.language_set),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search
                        )
                    )
                ),
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=language.get('back','commons.navigation',language=selector.language_set),
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
                            label=language.get('back','commons.navigation',language=selector.language_set),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if panel == 0:
                embed.set_footer(text=language.get(
                    'page','commons.search',values={'page':page+1,'maxpage':maxpage+1 if maxpage >= 0 else 1},
                    language=selector.language_set
                ))
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
                try:
                    await msg.edit(view=None)
                except:
                    pass
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
                    modal = nextcord.ui.Modal(
                        title=language.get('search_title','commons.search',language=selector.language_set),
                        auto_defer=False
                    )
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label=language.get('query','commons.search',language=selector.language_set),
                            style=nextcord.TextInputStyle.short,
                            placeholder=language.get('query_prompt','commons.search',language=selector.language_set)
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
    @restrictions.not_banned()
    async def modping(self,ctx):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_logging']:
            return await ctx.send(selector.get('disabled'))

        if ctx.guild.id in self.bot.db['underattack']:
            return await ctx.send(f'{self.bot.ui_emojis.error} This server is in Under Attack mode. Some functionality is unavailable.')

        found = False
        room = None

        # Optimized logic
        for key in self.bot.db['rooms']:
            if not 'discord' in self.bot.db['rooms'][key].keys():
                continue
            data = self.bot.db['rooms'][key]['discord']
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
                    if not 'discord' in self.bot.db['rooms'][key].keys():
                        continue
                    data = self.bot.db['rooms'][key]['discord']
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

        hook_id = self.bot.db['rooms'][room]['discord'][f'{self.bot.config["home_guild"]}'][0]
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
                await ch.send(
                    f'<@&{role}> {selector.fget("needhelp",values={"username":author,"userid":ctx.author.id,"guildname":ctx.guild.name,"guildid":ctx.guild.id})}',
                    allowed_mentions=nextcord.AllowedMentions(roles=True,everyone=False,users=False)
                )
                return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

        await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("bad_config")}')

    @nextcord.message_command(name='View reactions')
    async def reactions_ctx(self, interaction, msg: nextcord.Message):
        if interaction.user.id in self.bot.db['fullbanned']:
            return
        selector = language.get_selector('bridge.reactions_ctx',userid=interaction.user.id)
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
            return await interaction.response.send_message(
                language.get('banned','commons.interaction',language=selector.language_set),
                ephemeral=True
            )
        msg_id = msg.id

        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
        except:
            return await interaction.response.send_message(
                language.get('not_found','commons.interaction',language=selector.language_set),
                ephemeral=True
            )

        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.emoji} {selector.get("reactions")}',color=self.bot.colors.unifier)

        index = 0
        page = 0
        limit = 25

        maxpage = math.ceil(len(msg.reactions.keys()) / limit) - 1
        author_id = interaction.user.id
        respmsg = None
        interaction_resp = None

        while True:
            selection = nextcord.ui.StringSelect(
                max_values=1, min_values=1, custom_id='selection',
                placeholder=language.get('selection_emoji','bridge.emojis',language=selector.language_set)
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
                    description=selector.fget('reactions_count',values={"count": len(msg.reactions[list(msg.reactions.keys())[x + (page * limit)]].keys())})
                )
            users = []

            if len(msg.reactions.keys()) == 0:
                embed.description = selector.get('no_reactions')
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
        selector = language.get_selector('bridge.report',userid=interaction.user.id)
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
            return await interaction.response.send_message(
                language.get('banned','commons.interaction',language=selector.language_set),
                ephemeral=True
            )

        if not self.bot.config['enable_logging']:
            return await interaction.response.send_message(selector.get('disabled'), ephemeral=True)

        try:
            msgdata = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await interaction.response.send_message(
                language.get('not_found','commons.interaction',language=selector.language_set)
            )

        roomname = msgdata.room
        userid = msgdata.author_id
        content = copy.deepcopy(msg.content)  # Prevent tampering w/ original content

        btns = ui.ActionRow(
            nextcord.ui.Button(style=nextcord.ButtonStyle.blurple, label=selector.get('spam'), custom_id=f'spam', disabled=False),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('abuse'), custom_id=f'abuse', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('explicit'), custom_id=f'explicit', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('other'), custom_id=f'other', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('misc'), custom_id=f'misc', disabled=False
            )
        )
        btns_abuse = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('abuse_1'), custom_id=f'abuse_1', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('abuse_2'), custom_id=f'abuse_2', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('abuse_3'), custom_id=f'abuse_3', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('abuse_4'), custom_id=f'abuse_4', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('category_misc'), custom_id=f'abuse_5', disabled=False
            )
        )
        btns_explicit = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('explicit_1'), custom_id=f'explicit_1', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('explicit_2'), custom_id=f'explicit_2', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('explicit_3'), custom_id=f'explicit_3', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('explicit_4'), custom_id=f'explicit_4', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.blurple, label=selector.get('category_misc'), custom_id=f'explicit_5', disabled=False
            )
        )
        btns2 = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray,
                label=language.get('cancel','commons.navigation',language=selector.language_set),
                custom_id=f'cancel', disabled=False
            )
        )
        components = ui.MessageComponents()
        components.add_rows(btns, btns2)
        msg = await interaction.response.send_message(selector.get('question'), view=components, ephemeral=True)
        msg = await msg.fetch()

        def check(interaction):
            return interaction.user.id == interaction.user.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            try:
                return await interaction.edit_original_message(
                    content=language.get('timeout','commons.interaction',language=selector.language_set),
                    view=None
                )
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
            await interaction.response.edit_message(content=selector.get('question_2'), view=components)
        elif interaction.data["custom_id"] == 'explicit':
            components.add_rows(btns_explicit, btns2)
            await interaction.response.edit_message(content=selector.get('question_2'), view=components)
        elif interaction.data["custom_id"] == 'cancel':
            return await interaction.response.edit_message(
                content=language.get('cancel','commons.interaction',language=selector.language_set),
                view=None
            )
        else:
            asked = False
        if asked:
            try:
                interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
            except:
                try:
                    return await interaction.edit_original_message(
                        content=language.get('timeout','commons.interaction',language=selector.language_set),
                        view=None
                    )
                except:
                    return
            buttons = msg.components[0].children
            cat2 = None
            for button in buttons:
                if button.custom_id == interaction.data["custom_id"]:
                    cat2 = button.label
                    break
            if interaction.data["custom_id"] == 'cancel':
                return await interaction.response.edit_message(content=language.get('cancel','commons.interaction',language=selector.language_set), view=None)
        else:
            cat2 = 'none'
        self.bot.reports.update({f'{interaction.user.id}_{userid}_{msg.id}': [cat, cat2, content, roomname, msgdata.id]})
        reason = nextcord.ui.TextInput(
            style=nextcord.TextInputStyle.paragraph, label=selector.get('details_title'),
            placeholder=selector.get('details_prompt'),
            required=False
        )
        signature = nextcord.ui.TextInput(
            style=nextcord.TextInputStyle.short, label=selector.get('sign_title'),
            placeholder=selector.get('sign_prompt'),
            required=True, min_length=len(interaction.user.name), max_length=len(interaction.user.name)
        )
        modal = nextcord.ui.Modal(title=selector.get('title'), custom_id=f'{userid}_{msg.id}', auto_defer=False)
        modal.add_item(reason)
        modal.add_item(signature)
        await interaction.response.send_modal(modal)

    @commands.command(description=language.desc('bridge.serverstatus'))
    @restrictions.not_banned_guild()
    async def serverstatus(self,ctx):
        selector = language.get_selector(ctx)
        embed = nextcord.Embed(
            title=selector.get('title'),
            description=selector.get('body_ok'),
            color=self.bot.colors.success
        )
        if f'{ctx.guild.id}' in self.bot.bridge.restricted:
            embed.description = selector.get('body_restricted')
            embed.colour = self.bot.colors.warning
        await ctx.send(embed=embed)

    @commands.command(aliases=['exp','lvl','experience'], description=language.desc('bridge.level'))
    async def level(self,ctx,*,user=None):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_exp']:
            return await ctx.send(selector.get('disabled'))
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
                selector.get("title_self") if user.id==ctx.author.id else
                selector.fget("title_other", values={"username": user.global_name if user.global_name else user.name})
             ),
            description=(
                f'{selector.fget("level", values={"level": data["level"]})} | {selector.fget("exp",values={"exp": {round(data["experience"],2)}})}\n\n'+
                f'`{progressbar}`\n{selector.fget("progress",values={"progress": round(data["progress"]*100)})}'
            ),
            color=self.bot.colors.unifier
        )
        embed.set_author(
            name=f'@{user.name}',
            icon_url=user.avatar.url if user.avatar else None
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['lb'],description=language.desc('bridge.leaderboard'))
    async def leaderboard(self,ctx):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_exp']:
            return await ctx.send(language.get('disabled','bridge.level',language=selector.language_set))
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
            title=f'{self.bot.ui_emojis.leaderboard} {selector.fget("title",values={"botname": self.bot.user.global_name or self.bot.user.name})}',
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
                    f'{placement_emoji[rank]} **{username}**: {language.fget("level","bridge.level",values={"level": lb_data[index][1]["level"]},language=selector.language_set)}' if rank <= 3 else
                    f'`{rank}.` **{username}**: {language.fget("level","bridge.level",values={"level": lb_data[index][1]["level"]},language=selector.language_set)}'
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

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type==nextcord.InteractionType.component:
            if not 'custom_id' in interaction.data.keys():
                return
            if (interaction.data["custom_id"].startswith('rp') or interaction.data["custom_id"].startswith('ap')) and not interaction.user.id in self.bot.moderators:
                selector = language.get_selector('bridge.bridge',interaction.user.id)
                return await interaction.response.send_message(language.get("mod_unexpected","commons.interaction",language=selector.language_set),ephemeral=True)
            if interaction.data["custom_id"].startswith('rpdelete'):
                selector = language.get_selector('bridge.bridge', interaction.user.id)
                msg_id = int(interaction.data["custom_id"].replace('rpdelete_','',1))
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red, label=language.get('delete','commons.moderation',language=selector.language_set),
                        custom_id=f'rpdelete_{interaction.data["custom_id"].split("_")[1]}', disabled=True
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green, label=language.get('review','bridge.report',language=selector.language_set),
                        custom_id=f'rpreview_{interaction.data["custom_id"].split("_")[1]}', disabled=False
                    )
                )
                components = ui.MessageComponents()
                components.add_row(btns)

                try:
                    msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(msg_id)
                except:
                    return await interaction.response.send_message(language.get('not_found','commons.interaction',language=selector.language_set),ephemeral=True)

                if not interaction.user.id in self.bot.moderators:
                    return await interaction.response.send_message('go away',ephemeral=True)

                await interaction.response.defer(ephemeral=True,with_message=True)

                try:
                    await self.bot.bridge.delete_parent(msg_id)
                    if msg.webhook:
                        raise ValueError()
                    await interaction.message.edit(view=components)
                    return await interaction.edit_original_message(language.get("parent_delete","moderation.delete",language=selector.language_set))
                except:
                    try:
                        deleted = await self.bot.bridge.delete_copies(msg_id)
                        await interaction.message.edit(view=components)
                        return await interaction.edit_original_message(language.fget("children_delete","moderation.delete",values={"count": deleted},language=selector.language_set))
                    except:
                        traceback.print_exc()
                        await interaction.edit_original_message(content=language.get("error","moderation.delete",language=selector.language_set))
            elif interaction.data["custom_id"].startswith('rpreview_'):
                selector = language.get_selector('moderation.report',userid=interaction.user.id)
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.red, label=language.get("delete","commons.moderation",language=selector.language_set),
                        custom_id=f'rpdelete_{interaction.data["custom_id"].split("_")[1]}', disabled=True
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green, label=selector.get("review"),
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
                embed.title = selector.fget("reviewed_notice",values={"moderator": author})
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
                            await thread.send(selector.get("reviewed_thread"))
                        except:
                            pass
                    self.bot.db['report_threads'].pop(str(interaction.message.id))
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content=selector.get('reviewed'))
            elif interaction.data["custom_id"].startswith('apaccept_') or interaction.data["custom_id"].startswith('apreject_'):
                selector = language.get_selector('moderation.appeal',userid=interaction.user.id)
                btns = ui.ActionRow(
                    nextcord.ui.Button(
                        style=(
                            nextcord.ButtonStyle.gray if interaction.data["custom_id"].startswith('apaccept_')
                            else nextcord.ButtonStyle.red
                        ),
                        label=language.get('reject','commons.navigation',language=selector.language_set),
                        disabled=True,
                        emoji=self.bot.ui_emojis.error
                    ),
                    nextcord.ui.Button(
                        style=(
                            nextcord.ButtonStyle.gray if interaction.data["custom_id"].startswith('apreject_')
                            else nextcord.ButtonStyle.green
                        ),
                        label=selector.get('accept'),
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
                embed.title = selector.fget(
                    "accepted_notice" if interaction.data["custom_id"].startswith('apaccept_') else 'rejected_notice',
                    values={'moderator': author}
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
                            await thread.send(selector.get('reviewed_thread'))
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
                        title=selector.get('accepted_title'),
                        description=selector.get('accepted_body'),
                        color=self.bot.colors.success
                    )
                else:
                    results_embed = nextcord.Embed(
                        title=selector.get('rejected_title'),
                        description=selector.get('rejected_body'),
                        color=self.bot.colors.error
                    )
                user = self.bot.get_user(userid)
                if user:
                    await user.send(embed=results_embed)
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content=selector.get('reviewed'))
        elif interaction.type == nextcord.InteractionType.modal_submit:
            selector = language.get_selector('bridge.report',userid=interaction.user.id)
            if not interaction.data['custom_id']==f'{interaction.user.id}_{interaction.message.id}':
                # not a report
                return
            context = interaction.data['components'][0]['components'][0]['value']
            if not interaction.data['components'][1]['components'][0]['value'].lower() == interaction.user.name.lower():
                return
            if context is None or context == '':
                context = selector.get('no_context')
            author = f'@{interaction.user.name}'
            if not interaction.user.discriminator == '0':
                author = f'{interaction.user.name}#{interaction.user.discriminator}'
            try:
                report = self.bot.reports[f'{interaction.user.id}_{interaction.data["custom_id"]}']
            except:
                return await interaction.response.send_message(selector.get('failed'), ephemeral=True)

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
                title=selector.get('report_title'),
                description=content,
                color=self.bot.colors.warning,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name=language.get('reason','commons.moderation',language=selector.language_set), value=f'{cat} => {cat2}', inline=False)
            embed.add_field(name=language.get('context','commons.moderation',language=selector.language_set), value=context, inline=False)
            embed.add_field(name=language.get('sender_id','commons.moderation',language=selector.language_set), value=str(msgdata.author_id), inline=False)
            embed.add_field(name=language.get('room','commons.moderation',language=selector.language_set), value=roomname, inline=False)
            embed.add_field(name=language.get('message_id','commons.moderation',language=selector.language_set), value=str(msgid), inline=False)
            embed.add_field(name=language.get('reporter_id','commons.moderation',language=selector.language_set), value=str(interaction.user.id), inline=False)
            try:
                embed.set_footer(text=selector.fget('submitted_by',values={'username': author}),
                                 icon_url=interaction.user.avatar.url)
            except:
                embed.set_footer(text=selector.fget('submitted_by',values={'username': author}))
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
                    style=nextcord.ButtonStyle.red, label=language.get('delete','commons.moderation',language=selector.language_set), custom_id=f'rpdelete_{msgid}',
                    disabled=False),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green, label=selector.get('review'), custom_id=f'rpreview_{msgid}',
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
                    name=selector.get('discussion',values={'message_id': msgid}),
                    auto_archive_duration=10080
                )
                self.bot.db['report_threads'].update({str(msg.id): thread.id})
                await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            except:
                pass
            self.bot.reports.pop(f'{interaction.user.id}_{interaction.data["custom_id"]}')
            return await interaction.edit_original_message(
                content=f'# {self.bot.ui_emojis.success} {selector.get("success_title")}\n{selector.get("success_body")}',
                view=None
            )

    @commands.command(hidden=True,description=language.desc("bridge.initbridge"))
    @restrictions.owner()
    async def initbridge(self, ctx, *, args=''):
        selector = language.get_selector(ctx)
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
        await ctx.send(selector.get("success"))

    @commands.command(hidden=True,description=language.desc("bridge.system"))
    @restrictions.owner()
    async def system(self, ctx, room, *, content):
        selector = language.get_selector(ctx)
        await self.bot.bridge.send(room,ctx.message,'discord',system=True,content_override=content)
        for platform in self.bot.platforms.keys():
            await self.bot.bridge.send(
                room, ctx.message, platform, system=True,
                content_override=content)
        await ctx.send(selector.get("success"))

    @commands.Cog.listener()
    async def on_message(self, message):
        selector = language.get_selector("bridge.bridge",userid=message.author.id)
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
            if not 'discord' in self.bot.db['rooms'][key].keys():
                continue
            data = self.bot.db['rooms'][key]['discord']
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
                    if not 'discord' in self.bot.db['rooms'][key].keys():
                        continue
                    data = self.bot.db['rooms'][key]['discord']
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
                title=selector.get("blocked_title"),
                description=selector.get("blocked_body"),
                color=self.bot.colors.error
            )

            if public:
                embed.add_field(name=language.get("reason","commons.moderation",language=selector.language_set),value=public_reason if public_reason else '[unknown]',inline=False)

            await message.channel.send(embed=embed)

            embed = nextcord.Embed(
                title=f'{self.bot.ui_emojis.warning} {selector.get("blocked_report_title")}',
                description=message.content[:-(len(message.content)-4096)] if len(message.content) > 4096 else message.content,
                color=self.bot.colors.error,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
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
                    name=plugname + f' ({selector.fget("involved",values={"count":len(responses[plugin]["target"])})})',
                    value=responses[plugin]['description'],
                    inline=False
                )
                if len(embed.fields) == 23:
                    break

            embed.add_field(name=selector.get("punished"), value=' '.join(list(banned.keys())), inline=False)
            embed.add_field(name=language.get("room","commons.moderation",language=selector.language_set), value=roomname, inline=False)
            embed.set_footer(
                text=selector.get("automated"),
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
                        await user_obj.send(selector.get("owner_immunity"))
                    except:
                        pass
                    continue
                nt = time.time() + banned[user]
                embed = nextcord.Embed(
                    title=language.fget("ban_title","commons.moderation",values={"moderator": "@Unifier (system)"},language=selector.language_set),
                    description=selector.get("ban_reason"),
                    color=self.bot.colors.warning,
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                embed.set_author(
                    name='@Unifier (system)',
                    icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                )
                if banned[user]==0:
                    embed.colour = self.bot.colors.critical
                    embed.add_field(
                        name=language.get('actions_taken','commons.moderation',language=selector.language_set),
                        value=f'- :zipper_mouth: {language.get("perm_ban","commons.moderation",language=selector.language_set)}\n- :white_check_mark: {language.get("perm_ban_appeal","commons.moderation",language=selector.language_set)}',
                        inline=False
                    )
                    embed.add_field(name=language.get('appeal_title','commons.moderation',language=selector.language_set),
                                    value=language.get('appeal_body','commons.moderation',language=selector.language_set),
                                    inline=False)
                    await self.bot.loop.run_in_executor(None,lambda: self.bot.bridge.add_modlog(0, user_obj.id, 'Automatic action carried out by security plugins', self.bot.user.id))
                else:
                    embed.add_field(
                        name=language.get('actions_taken','commons.moderation',language=selector.language_set),
                        value=f"- :warning: {language.get('warned','commons.moderation',language=selector.language_set)}\n- :zipper_mouth: {language.fget('temp_ban','commons.moderation',values={'unix': round(nt)},language=selector.language_set)}",
                        inline=False
                    )
                    embed.add_field(name=language.get('appeal_title','commons.moderation',language=selector.language_set),
                                    value=selector.get('cannot_appeal'),
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
                        selector.fget("limited_limit",values={'count': self.bot.config['restriction_length']})
                    )
                elif self.bot.bridge.cooldowned[f'{message.author.id}'] < time.time():
                    return await message.channel.send(
                        selector.get("limited_cooldown")
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

        emojified = False
        should_resend = False

        skip = []

        if '[emoji' in message.content:
            content_split = message.content.split('[emoji')

            for i in range(1,len(content_split)):
                if not ']' in content_split[i]:
                    continue

                emojiname = content_split[i].replace(': ',':',1).split(':')[1].split(']')[0]
                emoji = nextcord.utils.find(
                    lambda e: e.name == emojiname and not e.id in skip and e.guild_id in self.bot.db['emojis'],
                    self.bot.emojis
                )

                if not emoji:
                    continue

                skip.append(emoji.id)

        if is_pr or is_pr_ref or len(skip) >= 1:
            multisend = False
            should_resend = True
            emojified = True

        tasks = []
        parent_id = None

        if not message.channel.permissions_for(message.guild.me).manage_messages:
            if emojified or is_pr_ref:
                return await message.channel.send(selector.get('delete_fail'))

        if (message.content.lower().startswith('is unifier down') or
                message.content.lower().startswith('unifier not working')):
            await message.channel.send(selector.get('is_unifier_down'),reference=message)

        if multisend:
            # Multisend
            # Sends Discord message along with other platforms to minimize
            # latency on external platforms.
            self.bot.bridge.bridged.append(
                UnifierBridge.UnifierMessage(
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

        for platform in self.bot.platforms.keys():
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
                return await message.channel.send(selector.get('debug_msg_ids_fail'))
            if parent_id:
                ids.append(parent_id)
            if len(list(set(ids)))==1:
                await message.channel.send(selector.fget('debug_msg_ids_match', values={'message_id': str(ids[0])}))
            else:
                text = ''
                for msgid in ids:
                    text = text + f'\n{msgid}'
                await message.channel.send(selector.get('debug_msg_ids_mismatch')+text)

        if not message.author.bot and self.bot.config['enable_exp']:
            _newexp, levelup = await self.bot.bridge.add_exp(message.author.id)

            if levelup:
                level = self.bot.db['exp'][f'{message.author.id}']['level']
                embed = nextcord.Embed(
                    title=selector.fget('level_progress',values={'previous': level-1, 'new': level}),
                    color=self.bot.colors.blurple
                )
                embed.set_author(
                    name=(selector.fget('level_up',values={
                        'username': message.author.global_name if message.author.global_name else message.author.name
                    })),
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
            if not 'discord' in self.bot.db['rooms'][key].keys():
                continue
            data = self.bot.db['rooms'][key]['discord']
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
                    if not 'discord' in self.bot.db['rooms'][key].keys():
                        continue
                    data = self.bot.db['rooms'][key]['discord']
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
            if not ch:
                try:
                    ch = await self.bot.fetch_channel(payload.channel_id)
                except:
                    return
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
                if not 'discord' in self.bot.db['rooms'][key].keys():
                    continue
                data = self.bot.db['rooms'][key]['discord']
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
                        if not 'discord' in self.bot.db['rooms'][key].keys():
                            continue
                        data = self.bot.db['rooms'][key]['discord']
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
        selector = language.get_selector('bridge.bridge',userid=message.author.id)
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
            if not 'discord' in self.bot.db['rooms'][key].keys():
                continue
            data = self.bot.db['rooms'][key]['discord']
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
                    if not 'discord' in self.bot.db['rooms'][key].keys():
                        continue
                    data = self.bot.db['rooms'][key]['discord']
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
            embed = nextcord.Embed(title=selector.fget('deleted',values={'roomname':roomname}), description=content)
            embed.add_field(name='Embeds',
                            value=selector.fget(
                                      'embeds',values={'count': len(message.embeds)}
                                  )+', '+selector.fget(
                                      'files',values={'count': len(message.attachments)}
                                  ),
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

        await self.bot.bridge.delete_message(msg)

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
