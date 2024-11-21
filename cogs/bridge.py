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
from typing import Optional, Union
from nextcord.ext import commands, application_checks
import traceback
import time
import datetime
import random
import string
import json
import compress_json
import re
import ast
import math
import os
import sys
from utils import log, langmgr, ui, webhook_cache as wcache, platform_base, restrictions as r, restrictions_legacy as r_legacy, slash as slash_helper
import importlib
import emoji as pymoji
import aiomultiprocess
import aiohttp
from aiomultiprocess import Worker

# import ujson if installed
try:
    import ujson as json  # pylint: disable=import-error
except:
    pass

try:
    import uvloop  # pylint: disable=import-error
except:
    pass

if not sys.platform == 'win32':
    force_disable_multicore = False # disables multicore regardless of config
    aiomultiprocess.set_start_method("fork")
else:
    force_disable_multicore = True

mentions = nextcord.AllowedMentions(everyone=False, roles=False, users=False)
emergency_mentions = nextcord.AllowedMentions(everyone=False, roles=True, users=True)
restrictions = r.Restrictions()
restrictions_legacy = r_legacy.Restrictions()
language = langmgr.partial()
language.load()
slash = slash_helper.SlashHelper(language)

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
    # In case of the infamous Room Robbery bug, (room ownership gets stolen from a server),
    # convert some variables to private variables (e.g. room ==> __room). Should help.
    #
    # If it didn't, DM me so I can look into it

    def __init__(self, bot, logger, webhook_cache=None):
        self.__bot = bot
        self.bridged = []
        self.prs = {}
        self.webhook_cache = webhook_cache or wcache.WebhookCacheStore(self.__bot)
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
        self.alert = UnifierAlert

    @property
    def room_template(self):
        return {
            'rules': [], 'restricted': False, 'locked': False, 'private': False,
            'private_meta': {
                'server': None,
                'allowed': [],
                'invites': [],
                'platform': 'discord'
            },
            'emoji': None, 'description': None, 'display_name': None, 'banned': []
        }

    @property
    def rooms(self):
        return list(self.__bot.db['rooms'].keys())

    @property
    def public_rooms(self):
        return [room for room in self.rooms if not self.get_room(room)['meta']['private']]

    class UnifierMessage:
        def __init__(self, author_id, guild_id, channel_id, original, copies, external_copies, urls, source, room,
                     external_urls=None, webhook=False, prehook=None, reply=False, external_bridged=False,
                     reactions=None, thread=None):
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

    class UnifierUser:
        def __init__(self, bot, user_id, name, global_name=None, platform='discord', system=False):
            self.__bot = bot
            self.__id = user_id
            self.__name = name
            self.__global_name = global_name
            self.__platform = platform
            self.__system = system
            self.__redacted = False

        @property
        def id(self):
            return self.__id

        @property
        def name(self):
            return self.__name

        @property
        def global_name(self):
            return self.__global_name or self.__name

        @property
        def platform(self):
            return self.__platform

        @property
        def unifier_name(self):
            if self.__redacted:
                return '[hidden username]'
            return (
                    self.__bot.db['nicknames'].get(f'{self.id}') or self.global_name
            ) + (
                ' (system)' if self.__system else ''
            )

        @property
        def unifier_avatar(self):
            return (
                    self.__bot.db['avatars'].get(f'{self.id}') or self.avatar_url
            ) if not self.__system else (
                    self.__bot.user.avatar.url if self.__bot.user.avatar else None
            )

        @property
        def avatar_url(self):
            if self.platform == 'discord':
                return self.__bot.get_user(self.id).avatar.url

            source_support = self.__bot.platforms[self.platform]
            return source_support.avatar(source_support.get_user(self.id))

        def redact(self):
            self.__redacted = True

    class RoomForbiddenError(Exception):
        pass

    class TooManyRooms(Exception):
        """Server has reached maximum Private Room creations."""
        pass

    class TooManyConnections(Exception):
        """Server has reached maximum Private Room connections."""
        pass

    class RoomBannedError(Exception):
        pass

    class RoomNotFoundError(Exception):
        pass

    class RoomExistsError(Exception):
        pass

    class AlreadyJoined(Exception):
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
            __roominfo: dict = dict(self.get_room(room))

            if not platform in __roominfo.keys():
                continue

            if platform=='discord':
                if not f'{channel.guild.id}' in __roominfo['discord'].keys():
                    continue
                if channel.id in __roominfo['discord'][f'{channel.guild.id}']:
                    return room
            else:
                if not f'{support.get_id(support.server(channel))}' in __roominfo[platform].keys():
                    continue
                if support.get_id(channel) in __roominfo[platform][f'{support.get_id(support.server(channel))}']:
                    return room
        return False

    def get_room(self, room) -> dict or None:
        """Gets a Unifier room.
        This will be moved to UnifierBridge for a future update."""
        try:
            __roominfo = self.__bot.db['rooms'][room]
            base = {'meta': dict(self.room_template)}

            # add template keys and values to data
            for key in __roominfo.keys():
                if key == 'meta':
                    for meta_key in __roominfo['meta'].keys():
                        if meta_key == 'private_meta':
                            for pmeta_key in __roominfo['meta']['private_meta'].keys():
                                base['meta']['private_meta'].update(
                                    {pmeta_key: __roominfo['meta']['private_meta'][pmeta_key]}
                                )
                        else:
                            base['meta'].update({meta_key: __roominfo['meta'][meta_key]})
                else:
                    base.update({key: __roominfo[key]})

            return dict(base)
        except:
            return None

    def can_manage_room(self, room, user, platform='discord') -> bool:
        roominfo = self.get_room(room)

        if not roominfo:
            roominfo = self.get_room(self.get_invite(room)['room'])

        if platform == 'discord':
            manage_guild = user.guild_permissions.manage_channels
            user_id = user.id
            guild_id = user.guild.id
        else:
            support = self.__bot.platforms[platform]
            manage_guild = support.permissions(user).manage_channels
            user_id = support.get_id(user)
            guild_id = support.get_id(support.server(user))

        is_server = guild_id == roominfo['meta']['private_meta']['server']

        if user_id in self.__bot.admins:
            return True

        if roominfo['meta']['private']:
            if user:
                if user_id in self.__bot.moderators and self.__bot.config['private_rooms_mod_access']:
                    return True
            return is_server and manage_guild
        else:
            return user_id in self.__bot.admins

    def can_join_room(self, room, user, platform='discord') -> bool:
        roominfo = self.get_room(room)

        if not roominfo:
            roominfo = self.get_room(self.get_invite(room)['room'])

        if platform == 'discord':
            manage_channels = user.guild_permissions.manage_channels
            user_id = user.id
            guild_id = user.guild.id
        else:
            support = self.__bot.platforms[platform]
            manage_channels = support.permissions(user).manage_channels
            user_id = support.get_id(user)
            guild_id = support.get_id(support.server(user))

        is_server = guild_id == roominfo['meta']['private_meta']['server']
        can_join = guild_id in roominfo['meta']['private_meta']['allowed']

        if user_id in self.__bot.admins:
            return True

        if roominfo['meta']['private']:
            if user:
                if user_id in self.__bot.moderators and self.__bot.config['private_rooms_mod_access']:
                    return True
            return (is_server or can_join) and manage_channels
        else:
            return manage_channels

    def can_access_room(self, room, user, platform='discord', ignore_mod=False) -> bool:
        __roominfo = self.get_room(room)

        if not __roominfo:
            __roominfo = self.get_room(self.get_invite(room)['room'])

        if platform=='discord':
            user_id = user.id
            guild_id = user.guild.id
        else:
            support = self.__bot.platforms[platform]
            user_id = support.get_id(user)
            guild_id = support.get_id(support.server(user))

        if user.id in self.__bot.admins and not ignore_mod:
            return True

        if __roominfo['meta']['private']:
            if user:
                if user_id in self.__bot.moderators and (self.__bot.config['private_rooms_mod_access'] and not ignore_mod):
                    return True
            return (
                    guild_id == __roominfo['meta']['private_meta']['server'] or
                    guild_id in __roominfo['meta']['private_meta']['allowed']
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

        __room_base = {'meta': dict(self.room_template)}
        __room_base['meta'].update({'private': private})

        if private:
            if not self.__bot.config['enable_private_rooms']:
                raise ValueError('private rooms are disabled')

            if not dry_run:
                limit = self.get_rooms_limit(origin)

                if not f'{origin}' in self.__bot.db['rooms_count'].keys():
                    self.__bot.db['rooms_count'].update({f'{origin}': 0})
                if self.__bot.db['rooms_count'][f'{origin}'] >= limit and not limit == 0:
                    raise self.TooManyRooms('exceeded limit')
                self.__bot.db['rooms_count'][f'{origin}'] += 1
            __room_base['meta']['private_meta'].update({'server': origin, 'platform': platform})

        if not dry_run:
            self.__bot.db['rooms'].update({room: dict(__room_base)})
            self.__bot.db.save_data()

        return dict(__room_base)

    def delete_room(self, room):
        if not room in self.rooms:
            raise self.RoomNotFoundError('invalid room')

        roomname = str(room)

        room = self.get_room(room)
        for invite in room['meta']['private_meta']['invites']:
            try:
                self.delete_invite(invite)
            except:
                pass

        try:
            if (
                    (room['meta']['private_meta']['server']) and
                    (self.__bot.db['rooms_count'][str(room['meta']['private_meta']['server'])] > 0)
            ):
                self.__bot.db['rooms_count'][str(room['meta']['private_meta']['server'])] -= 1
        except:
            # not something to worry about
            pass

        for platform in room.keys():
            if not room['meta']['private']:
                break
            if platform == 'meta':
                continue
            for guild in room[platform].keys():
                if not guild in self.__bot.db['connections_count'].keys():
                    continue
                self.__bot.db['connections_count'][guild] -= 1
                if self.__bot.db['connections_count'][guild] < 0:
                    self.__bot.db['connections_count'][guild] = 0

        self.__bot.db['rooms'].pop(roomname)
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
            __invite = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            if not __invite in self.__bot.db['invites'].keys():
                break

        self.__bot.db['invites'].update({__invite: {
            'remaining': max_usage, 'expire': expire, 'room': room
        }})
        self.__bot.db['rooms'][room]['meta']['private_meta']['invites'].append(__invite)
        self.__bot.db.save_data()
        return __invite

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
        ) and (not user_id in self.__bot.moderators and not self.__bot.config['private_rooms_mod_access']):
            raise self.RoomBannedError('banned from room')
        if invite['remaining'] == 1:
            self.delete_invite(invite)
        else:
            if invite['remaining'] > 0:
                self.__bot.db['invites'][invite]['remaining'] -= 1
        roominfo['meta']['private_meta']['allowed'].append(server_id)
        self.update_room(invite['room'], roominfo)
        self.__bot.db.save_data()

    def get_rooms_count(self, guild_id):
        # we don't need to pull some fancy logic here since this existed since v3
        return (
            self.__bot.db['rooms_count'][f'{guild_id}'] if str(guild_id) in self.__bot.db['rooms_count'].keys() else 0
        )

    def get_connections_count(self, guild_id, platform='discord'):
        if str(guild_id) in self.__bot.db['connections_count'].keys():
            return self.__bot.db['connections_count'][f'{guild_id}']

        count = 0
        for room in self.rooms:
            roominfo = self.get_room(room)
            if not roominfo['meta']['private']:
                continue
            try:
                if str(guild_id) in roominfo[platform].keys():
                    count += 1
            except KeyError:
                continue
        return count

    def get_rooms_limit(self, guild_id):
        if str(guild_id) in self.__bot.db['allocations_override'].keys():
            return self.__bot.db['allocations_override'][f'{guild_id}']['rooms']
        else:
            return self.__bot.config['private_rooms_limit']

    def get_connections_limit(self, guild_id):
        if str(guild_id) in self.__bot.db['allocations_override'].keys():
            return self.__bot.db['allocations_override'][f'{guild_id}']['connections']
        else:
            return self.__bot.config['private_rooms_connections_limit']

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

        limit = self.get_connections_limit(guild_id)

        if not f'{guild_id}' in self.__bot.db['connections_count'].keys():
            self.__bot.db['connections_count'].update({f'{guild_id}': self.get_connections_count(guild_id, platform)})

        if roominfo['meta']['private']:
            if self.__bot.db['connections_count'][f'{guild_id}'] >= limit and not limit == 0:
                raise self.TooManyConnections('exceeded limit')

        if str(guild_id) in roominfo['meta']['banned'] and ((
                not user_id in self.__bot.moderators and not self.__bot.config['private_rooms_mod_access']
        ) or not roominfo['meta']['private']):
            raise self.RoomBannedError('banned from room')

        if roominfo['meta']['private']:
            if (
                    not guild_id in roominfo['meta']['private_meta']['allowed'] and
                    not guild_id == roominfo['meta']['private_meta']['server']
            ) and (not user_id in self.__bot.moderators and not self.__bot.config['private_rooms_mod_access']):
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
            raise self.AlreadyJoined('already joined')

        self.__bot.db['rooms'][room][platform].update({guild_id: ids})

        if roominfo['meta']['private']:
            self.__bot.db['connections_count'][f'{guild_id}'] += 1

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

        if not f'{guild_id}' in self.__bot.db['connections_count'].keys():
            self.__bot.db['connections_count'].update({f'{guild_id}': self.get_connections_count(guild_id, platform)})

        guild_id = str(guild_id)

        if not platform in roominfo.keys():
            raise ValueError('not joined')

        if not guild_id in self.__bot.db['rooms'][room][platform].keys():
            raise ValueError('not joined')

        self.__bot.db['rooms'][room][platform].pop(guild_id)

        if roominfo['meta']['private']:
            self.__bot.db['connections_count'][f'{guild_id}'] -= 1
            if self.__bot.db['connections_count'][f'{guild_id}'] < 0:
                self.__bot.db['connections_count'][f'{guild_id}'] = 0

        self.__bot.db.save_data()

    async def optimize(self, platform='discord'):
        """Optimizes data to avoid having to fetch webhooks.
        This decreases latency incuded by message bridging prep."""
        support = None
        if not platform == 'discord':
            support = self.__bot.platforms[platform]

        for room in self.__bot.db['rooms']:
            if platform == 'discord':
                if 'discord' in self.__bot.db['rooms'][room].keys():
                    for guild in self.__bot.db['rooms'][room]['discord']:
                        if len(self.__bot.db['rooms'][room]['discord'][guild])==1:
                            try:
                                hook = await self.__bot.fetch_webhook(self.__bot.db['rooms'][room]['discord'][guild][0])
                            except:
                                continue
                            self.__bot.db['rooms'][room]['discord'][guild].append(hook.channel_id)
            else:
                if not support.uses_webhooks:
                    continue
                if platform in self.__bot.db['rooms'][room].keys():
                    for guild in self.__bot.db['rooms'][room][platform]:
                        if len(self.__bot.db['rooms'][room][platform][guild])==1:
                            try:
                                hook = await support.fetch_webhook(self.__bot.db['rooms'][room][platform][guild][0], guild)
                            except:
                                continue
                            try:
                                channel_id = support.get_id(support.channel(hook))
                            except:
                                channel_id = support.channel_id(hook)
                            self.__bot.db['rooms'][room][platform][guild].append(channel_id)

        self.__bot.db.save_data()

    async def convert_1(self):
        """Converts data structure to be v3.0.0-compatible.
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
                'emoji': self.__bot.db['roomemojis'][room] if room in self.__bot.db['roomemojis'].keys() else None,
                'description': self.__bot.db['descriptions'][room] if room in self.__bot.db['descriptions'].keys() else None,
                'display_name': None,
                'banned': []
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
        self.__bot.db.pop('roomemojis')
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

    # noinspection PyTypeChecker
    async def backup(self,filename='bridge.json',limit=None):
        if self.backup_lock:
            return

        if not limit:
            limit = self.__bot.config['cache_backup_limit']

        if limit <= 0:
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

    async def fetch_message(self,message_id,prehook=False,not_prehook=False,can_wait=False):
        if prehook and not_prehook:
            raise ValueError('Conflicting arguments')
        waiting = self.__bot.config['existence_wait']
        if waiting <= 0 or not can_wait:
            waiting = 1
        for waited in range(waiting):
            for message in self.bridged:
                if (str(message.id)==str(message_id) or str(message_id) in str(message.copies) or
                        str(message_id) in str(message.external_copies) or str(message.prehook)==str(message_id)):
                    if prehook and str(message.prehook)==str(message_id) and not str(message.id) == str(message_id):
                        return message
                    elif not_prehook and not str(message.prehook) == str(message_id):
                        return message
                    elif not prehook:
                        return message
            await asyncio.sleep(1)
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

            for guild_id in self.__bot.db['rooms'][roomname][platform]:
                try:
                    if platform=='meta':
                        continue
                    elif platform=='discord':
                        guild = self.__bot.get_guild(int(guild_id))
                    else:
                        support = self.__bot.platforms[platform]
                        try:
                            guild = support.get_server(guild_id)
                            if not guild:
                                raise Exception()
                        except:
                            guild = await support.fetch_server(guild_id)
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
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message, can_wait=True)
        if msg.source=='discord':
            ch = self.__bot.get_channel(int(msg.channel_id))
            todelete = await ch.fetch_message(int(msg.id))

            guild = self.__bot.get_guild(int(msg.guild_id))
            if guild.me.guild_permissions.administrator:
                raise restrictions.TooManyPermissions()

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
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message, can_wait=True)
        threads = []

        async def delete_discord(msgs):
            count = 0
            threads = []
            for key in list(self.__bot.db['rooms'][msg.room]['discord'].keys()):
                if not key in list(msgs.keys()):
                    continue

                guild = self.__bot.get_guild(int(key))
                if guild.me.guild_permissions.administrator:
                    continue

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
                        support.delete(todelete)
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
                    delete_others(msg.external_copies[platform],platform)
                ))

        results = await asyncio.gather(*threads)
        return sum(results)

    async def make_friendly(self, text, server=None, image_markdown=False):
        # Replace community channels with placeholders
        text = text.replace('<id:customize>','#Channels & Roles')
        text = text.replace('<id:browse>', '#Browse Channels')

        # Replace emoji with URL if text contains solely an emoji
        if (text.startswith('<:') or text.startswith('<a:')) and text.endswith('>'):
            try:
                emoji_name = text.split(':')[1]
                emoji_id = int(text.split(':')[2].replace('>','',1))
                if image_markdown:
                    return f'![](https://cdn.discordapp.com/emojis/{emoji_id}.webp?size=48&quality=lossless)'
                else:
                    return f'[emoji ({emoji_name})](https://cdn.discordapp.com/emojis/{emoji_id}.webp?size=48&quality=lossless)'
            except:
                pass

        # Replace mentions with placeholders (handles both user and role mentions)
        components = text.split('<@')
        offset = 0
        if text.startswith('<@'):
            offset = 1

        while offset < len(components):
            if len(components) == 1 and offset == 0:
                break
            is_role = False
            try:
                userid = int(components[offset].split('>', 1)[0])
            except:
                userid = components[offset].split('>', 1)[0]
                if userid.startswith('&'):
                    is_role = True
                    try:
                        userid = int(components[offset].split('>', 1)[0].replace('&','',1))
                    except:
                        pass
            try:
                if is_role:
                    role = server.get_role(userid)
                    display_name = role.name
                else:
                    user = self.__bot.get_user(userid)
                    display_name = user.global_name or user.name
            except:
                offset += 1
                continue
            if is_role:
                text = text.replace(f'<@&{userid}>', f'@{display_name}')
            else:
                text = text.replace(f'<@{userid}>', f'@{display_name}').replace(
                    f'<@!{userid}>', f'@{display_name}')
            offset += 1

        # Replace channel mentions with placeholders
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
            channel = self.__bot.get_channel(channelid)
            if not channel:
                offset += 1
                continue
            text = text.replace(f'<#{channelid}>', f'#{channel.name}').replace(
                f'<#!{channelid}>', f'#{channel.name}')
            offset += 1

        # Replace static emojis with placeholders
        components = text.split('<:')
        offset = 0
        if text.startswith('<:'):
            offset = 1

        while offset < len(components):
            if len(components) == 1 and offset == 0:
                break
            try:
                emojiname = components[offset].split(':', 1)[0]
                emojiafter = components[offset].split(':', 1)[1].split('>')[0]+'>'
                text = text.replace(f'<:{emojiname}:{emojiafter}', f':{emojiname}\\:')
            except:
                pass
            offset += 1

        # Replace animated emojis with placeholders
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
        msg: UnifierBridge.UnifierMessage = await self.fetch_message(message, can_wait=True)

        threads = []

        source_support = self.__bot.platforms[msg.source] if msg.source != 'discord' else None

        if msg.source == 'discord':
            server = self.__bot.get_guild(int(msg.guild_id))
        else:
            server = source_support.get_server(msg.guild_id)

        async def edit_discord(msgs,friendly=False):
            threads = []

            if friendly:
                if msg.source == 'discord':
                    text = await self.make_friendly(content, server=server)
                else:
                    try:
                        text = await source_support.make_friendly(content)
                    except platform_base.MissingImplementation:
                        text = content
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
            dest_support = self.__bot.platforms[target]
            if friendly:
                if msg.source == 'discord':
                    text = await self.make_friendly(content, server=server)
                else:
                    try:
                        text = await source_support.make_friendly(content)
                    except platform_base.MissingImplementation:
                        text = content

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

        can_override = not content_override is None

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

        if source == 'discord':
            unifier_user: UnifierBridge.UnifierUser = UnifierBridge.UnifierUser(
                self.__bot, message.author.id, message.author.name, global_name=message.author.global_name,
                system=system
            )
        else:
            unifier_user: UnifierBridge.UnifierUser = UnifierBridge.UnifierUser(
                self.__bot, source_support.get_id(source_support.author(message)),
                source_support.name(source_support.author(message)),
                global_name=source_support.display_name(source_support.author(message)),
                platform=source, system=system
            )

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

        # Get dedupe
        if source == 'discord':
            author_id = message.author.id
            is_bot = message.author.bot
        else:
            author_id = source_support.get_id(source_support.author(message))
            is_bot = source_support.is_bot(source_support.author(message))

        dedupe = await self.dedupe_name(unifier_user.unifier_name, author_id)
        should_dedupe = dedupe > -1

        # Emoji time
        useremoji = None
        if self.__bot.config['enable_emoji_tags'] and not system:
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
                friendly_content = await self.make_friendly(msg_content, server=message.guild)
            else:
                try:
                    friendly_content = await source_support.make_friendly(msg_content)
                except platform_base.MissingImplementation:
                    friendly_content = msg_content

        message_ids = {}
        urls = {}
        trimmed = None
        replying = False

        # Threading
        thread_urls = {}
        threads = []
        size_total = 0
        max_files = 0
        if platform == 'discord':
            tb_v2 = True
        else:
            tb_v2 = dest_support.enable_tb

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

            if platform == 'discord':
                size_limit = 25000000
            else:
                size_limit = dest_support.attachment_size_limit or 0

            if size_limit > self.__bot.config['global_filesize_limit'] > 0:
                size_limit = self.__bot.config['global_filesize_limit']

            if not platform == 'discord':
                size_limit = dest_support.attachment_size_limit

            if size_total > size_limit:
                if not self.__bot.config['suppress_filesize_warning']:
                    if source=='discord':
                        await message.channel.send(
                            '`' + platform + '`: ' + selector.fget('filesize_limit',values={'limit':size_limit // 1000000}),
                            reference=message
                        )
                    else:
                        await source_support.send(
                            source_support.channel(message),
                            '`' + platform + '`: ' + selector.fget('filesize_limit',values={'limit':size_limit // 1000000}),
                            special={'reply':message}
                        )
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

                if platform == 'discord':
                    size_limit = 25000000
                else:
                    size_limit = dest_support.attachment_size_limit or 0

                if size_limit > self.__bot.config['global_filesize_limit'] > 0:
                    size_limit = self.__bot.config['global_filesize_limit']

                if source == 'discord':
                    if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                            not 'image' in attachment.content_type and not 'text/plain' in attachment.content_type and
                            self.__bot.config['safe_filetypes']) or attachment.size > size_limit:
                        continue
                else:
                    attachment_size = source_support.attachment_size(attachment)
                    content_type = source_support.attachment_type(attachment)
                    if platform == 'discord':
                        # already checked for, so skip
                        is_allowed = True
                    else:
                        is_allowed = dest_support.attachment_type_allowed(content_type)
                    if (
                            not 'audio' in content_type and not 'video' in content_type and not 'image' in content_type
                            and not 'text/plain' in content_type and self.__bot.config['safe_filetypes']
                    ) or attachment_size > size_limit or not is_allowed:
                        continue

                try:
                    files.append(await to_file(attachment))
                except platform_base.MissingImplementation:
                    continue
                index += 1
                if index >= max_files:
                    break

            return files

        async def stickers_to_urls(stickers):
            urls = []
            for sticker in stickers:
                if sticker.format == nextcord.StickerFormatType.lottie:
                    continue
                elif sticker.format == nextcord.StickerFormatType.apng or sticker.format == nextcord.StickerFormatType.png:
                    sticker_format = '.png'
                else:
                    sticker_format = '.gif'

                url = f'https://media.discordapp.net/stickers/{sticker.id}{sticker_format}'

                if platform == 'discord':
                    urls.append(f'[sticker ({sticker.name})]({url})')
                else:
                    if dest_support.uses_image_markdown:
                        urls.append(f'![]({url})')
                    else:
                        urls.append(f'[sticker ({sticker.name})]({url})')

            return urls

        files = []
        if platform == 'discord':
            files = await get_files(message.attachments)
        else:
            if not dest_support.files_per_guild:
                files = await get_files(message.attachments)

        # Process stickers
        stickertext = ''
        if source == 'discord' and not system:
            if len(message.stickers) > 0:
                stickertext = '\n'.join(await stickers_to_urls(message.stickers))
        if (len(message.content) > 0 or len(content_override if not content_override is None else '') > 0) and len(stickertext) > 0:
            stickertext = '\n' + stickertext

        # Broadcast message
        for guild in list(guilds.keys()):
            if source == 'discord':
                compare_guild = message.guild
            else:
                compare_guild = source_support.server(message)
            if platform=='discord':
                if source == 'discord':
                    sameguild = (guild == str(message.guild.id)) if message.guild else False
                else:
                    sameguild = (guild == source_support.get_id(compare_guild)) if compare_guild else False
            else:
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
                            urls.update({f'{source_support.get_id(source_support.server(message))}': source_support.url(message)})
                        except platform_base.MissingImplementation:
                            pass
                    continue

            # Reply processing
            reply_msg = None
            components = None
            pr_actionrow = None

            try:
                if source=='discord':
                    msgid = message.reference.message_id
                else:
                    msgid = source_support.reply(message)
                    if not type(msgid) is int and not type(msgid) is str:
                        msgid = source_support.get_id(msgid)
                replying = True
                reply_msg = await self.fetch_message(msgid)
            except:
                pass

            # Get reply message content if reply_msg exists
            if reply_msg:
                if not trimmed:
                    try:
                        if source == 'discord':
                            content = message.reference.cached_message.content
                        else:
                            # for NUPS, plugins process the content, not unifier
                            msg = source_support.reply(message)
                            if type(msg) is str or type(msg) is int:
                                msg = await source_support.fetch_message(
                                    source_support.channel(message), msg
                                )
                            content = source_support.content(msg)

                            if source_support.reply_using_text and reply_msg.reply:
                                # remove reply display if message is replying to another message
                                # and the reply text exists
                                if (
                                        reply_msg.server_id == source_support.get_id(source_support.server(message)) and not
                                        str(reply_msg.server_id) in reply_msg.copies.keys()
                                ):
                                    pass
                                split = content.split('\n')
                                split.pop(0)
                                content = '\n'.join(split)
                    except:
                        if source == 'discord':
                            msg = await message.channel.fetch_message(message.reference.message_id)
                        else:
                            raise
                        content = msg.content

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
                        if source == 'discord':
                            user = self.__bot.get_user(userid)
                            if not user:
                                global_name = 'unknown-user'
                            else:
                                global_name = user.global_name or user.name
                        else:
                            user = source_support.get_user(userid)
                            if not user:
                                global_name = 'unknown-user'
                            else:
                                global_name = source_support.display_name(user)
                        if user:
                            clean_content = clean_content.replace(f'<@{userid}>',
                                                                  f'@{global_name}').replace(
                                f'<@!{userid}>', f'@{global_name}')
                        offset += 1
                    if len(clean_content) > 80:
                        trimmed = clean_content[:-(len(clean_content) - 77)] + '...'
                    else:
                        trimmed = clean_content
                    trimmed = trimmed.replace('\n', ' ')

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
                            reply_support = self.__bot.platforms[reply_msg.source]
                            user = reply_support.get_user(reply_msg.author_id)
                            author_text = f'@{reply_support.display_name(user)}'
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
                            # no need to attempt a refetch as that has already been done
                            raise
                        count = len(msg.embeds) + len(msg.attachments)

                    if len(str(trimmed))==0 or not trimmed:
                        content_btn = nextcord.ui.Button(
                            style=button_style,label=f'x{count}', emoji='\U0001F3DE', disabled=True
                        )
                    else:
                        content_btn = nextcord.ui.Button(
                            style=button_style, label=trimmed, disabled=True
                        )

                    # Add PR buttons too.
                    if is_pr or is_pr_ref:
                        components = ui.View()
                        try:
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
                        except:
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
                        try:
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
                        except:
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
                elif replying:
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
                    else:
                        reply_row = ui.ActionRow(
                            nextcord.ui.Button(style=nextcord.ButtonStyle.gray,
                                               label=selector.fget('replying',values={'user': '[unknown]'}),
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

            # Send message
            embeds = message.embeds
            if not message.author.bot and not system:
                embeds = []

            if unifier_user.unifier_name.lower()==f'{self.__bot.user.name} (system)'.lower() and not system:
                unifier_user.redact()

            if platform=='discord':
                msg_author_dc = unifier_user.unifier_name
                if len(msg_author_dc) > 35:
                    msg_author_dc = msg_author_dc[:-(len(msg_author_dc) - 35)]
                    if useremoji:
                        msg_author_dc = msg_author_dc[:-2]

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
                async def tbsend(webhook,msg_author_dc,embeds,message,mentions,components,sameguild,
                                 destguild):
                    try:
                        tosend_content = (friendly_content if friendlified else msg_content) + stickertext
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
                        if sys.platform == 'win32':
                            __files = await get_files(message.attachments)
                        else:
                            __files = files
                        if self.__bot.config['use_multicore']:
                            async with aiohttp.ClientSession() as session:
                                webhook.session = session
                                msg = await webhook.send(avatar_url=unifier_user.unifier_avatar, username=msg_author_dc, embeds=embeds,
                                                         content=content_override if can_override else tosend_content, files=__files, allowed_mentions=mentions, view=(
                                                             components if components and not system else ui.MessageComponents()
                                                         ), wait=True)
                        else:
                            msg = await webhook.send(avatar_url=unifier_user.unifier_avatar, username=msg_author_dc, embeds=embeds,
                                                     content=content_override if can_override else tosend_content, files=__files, allowed_mentions=mentions,
                                                     view=(
                                                         components if components and not system else ui.MessageComponents()
                                                     ), wait=True)
                    except:
                        if self.__bot.config['debug']:
                            raise
                        return None
                    tbresult = [
                        {f'{destguild.id}': [webhook.channel.id, msg.id]},
                        {f'{destguild.id}': f'https://discord.com/channels/{destguild.id}/{webhook.channel.id}/{msg.id}'},
                        [sameguild, msg.id]
                    ]
                    return tbresult

                if tb_v2 and not alert:
                    if self.__bot.config['use_multicore'] and not force_disable_multicore:
                        # noinspection PyTypeChecker
                        threads.append(
                            Worker(
                                target=tbsend,
                                args=(
                                    webhook, msg_author_dc, embeds, message,
                                    touse_mentions, components, sameguild,
                                    destguild
                                ),
                                loop_initializer=uvloop.new_event_loop
                            )
                        )
                        threads[len(threads) - 1].start()
                    else:
                        threads.append(asyncio.create_task(tbsend(webhook, msg_author_dc, embeds, message,
                                                                  touse_mentions, components, sameguild,
                                                                  destguild)))
                else:
                    try:
                        tosend_content = alert_pings + (friendly_content if friendlified else msg_content) + stickertext

                        if content_override:
                            tosend_content = content_override

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
                        files = await get_files(message.attachments)
                        msg = await webhook.send(avatar_url=unifier_user.unifier_avatar, username=msg_author_dc, embeds=embeds,
                                                 content=content_override if can_override else tosend_content,
                                                 files=files, allowed_mentions=touse_mentions, view=(
                                                     components if components and not system else ui.MessageComponents()
                                                 ), wait=True)
                    except:
                        if self.__bot.config['debug']:
                            raise
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

                async def tbsend(msg_author,url,color,useremoji,reply,content, files, destguild):
                    guild_id = dest_support.get_id(destguild)

                    if sys.platform == 'win32':
                        __files = await get_files(message.attachments)
                    else:
                        __files = files

                    special = {
                        'bridge': {
                            'name': msg_author,
                            'avatar': url,
                            'color': color,
                            'emoji': useremoji
                        },
                        'files': __files if not alert else None,
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

                    if source == 'discord':
                        if not message.author.bot:
                            special['embeds'] = []
                    else:
                        try:
                            if not dest_support.is_bot(dest_support.author(message)):
                                special['embeds'] = []
                        except platform_base.MissingImplementation:
                            # assume user is not a bot
                            special['embeds'] = []

                    if reply and not alert:
                        special.update({'reply': reply})
                    if trimmed:
                        special.update({'reply_content': trimmed})
                    try:
                        msg = await dest_support.send(
                            ch, content_override if can_override else (content + stickertext), special=special
                        )
                    except Exception as e:
                        if dest_support.error_is_unavoidable(e) and not self.__bot.config['debug']:
                            return None
                        raise
                    tbresult = [
                        {f'{guild_id}': [
                            dest_support.get_id(dest_support.channel(msg)), dest_support.get_id(msg)
                        ]},
                        None,
                        [sameguild, dest_support.get_id(msg)]
                    ]
                    try:
                        tbresult[1] = {
                            f'{guild_id}': dest_support.url(msg)
                        }
                    except platform_base.MissingImplementation:
                        pass
                    return tbresult

                if content_override:
                    friendly_content = content_override
                    msg_content = content_override

                if dest_support.enable_tb:
                    threads.append(asyncio.create_task(tbsend(
                        unifier_user.unifier_name,unifier_user.unifier_avatar,color,useremoji,reply,content_override if can_override else (friendly_content if friendlified else msg_content), files, destguild
                    )))
                else:
                    try:
                        special = {
                            'bridge': {
                                'name': unifier_user.unifier_name,
                                'avatar': unifier_user.unifier_avatar,
                                'color': color,
                                'emoji': useremoji
                            },
                            'files': await get_files(message.attachments) if dest_support.files_per_guild else (files if not alert else None),
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

                        if source == 'discord':
                            if not message.author.bot:
                                special['embeds'] = []
                        else:
                            try:
                                if not dest_support.is_bot(dest_support.author(message)):
                                    special['embeds'] = []
                            except platform_base.MissingImplementation:
                                # assume user is not a bot
                                special['embeds'] = []

                        if reply and not alert:
                            special.update({'reply': reply})
                        if trimmed:
                            special.update({'reply_content': trimmed})
                        msg = await dest_support.send(
                            ch,
                            content_override if can_override else ((friendly_content + stickertext) if friendlified else (msg_content + stickertext)), special=special
                        )
                    except Exception as e:
                        if dest_support.error_is_unavoidable(e) and not self.__bot.config['debug']:
                            continue
                        raise

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
            if source == 'discord':
                msg_author = message.author.id
            else:
                msg_author = source_support.get_id(source_support.author(message))

        if id_override:
            parent_id = id_override

        if source == 'discord':
            urls.update({f'{message.guild.id}': message.jump_url})
        else:
            guild_id = source_support.get_id(source_support.server(message))
            try:
                msg_url = source_support.url(message)
                urls.update({f'{guild_id}': msg_url})
            except platform_base.MissingImplementation:
                pass

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
            ))
            if datetime.datetime.now().day != self.msg_stats_reset:
                self.msg_stats = {}
            try:
                self.msg_stats[room] += 1
            except:
                self.msg_stats.update({room: 1})
        return parent_id

class Bridge(commands.Cog, name=':link: Bridge'):
    """Bridge is the heart of Unifier, it's the extension that handles the bridging and everything chat related."""

    def __init__(self, bot):
        global language
        self.bot = bot
        language = self.bot.langmgr
        restrictions.attach_bot(self.bot)
        restrictions_legacy.attach_bot(self.bot)
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

        if sys.platform == 'win32' and self.bot.config['use_multicore']:
            self.logger.warning('Multicore is enabled, but it is not supported on Windows. Unifier will not use it.')
            self.logger.warning('Please consider using a Linux/macOS server for production environments.')

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
    
    def can_moderate(self, user, room):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            try:
                room = self.bot.bridge.get_invite(room)['room']
            except:
                return False

        __roominfo = self.bot.bridge.get_room(room)
        if not __roominfo:
            return False

        is_server = str(user.guild.id) == __roominfo['meta']['private_meta']['server']
        is_moderator = user.id in self.bot.moderators
        is_admin = user.id in self.bot.admins
        is_owner = user.id == self.bot.owner or user.id in self.bot.other_owners

        if __roominfo['meta']['private']:
            return (
                    user.guild_permissions.ban_members and is_server
            ) or ((is_moderator and self.bot.config['private_rooms_mod_access']) or is_admin or is_owner)
        else:
            return is_admin or is_owner

    async def roomslist(self, ctx: nextcord.Interaction, private):
        selector = language.get_selector('bridge.rooms', userid=ctx.user.id)

        show_restricted = False
        show_locked = False

        if ctx.user.id in self.bot.admins:
            show_restricted = True
            show_locked = True
        elif ctx.user.id in self.bot.moderators:
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
        ignore_mod = True

        helptext = selector.fget("title", values={"botname": self.bot.user.global_name or self.bot.user.name})

        if private:
            helptext = selector.fget("title_private",
                                     values={"botname": self.bot.user.global_name or self.bot.user.name})

        while True:
            embed = nextcord.Embed(color=self.bot.colors.unifier)
            maxpage = 0
            components = ui.MessageComponents()

            if panel == 0:
                was_searching = False
                search_roomlist = self.bot.bridge.rooms
                roomlist = []
                for search_room in search_roomlist:
                    # yes, this logic is messy.
                    # but it doesn't overwrite the origin server thing so i'm keeping it for now
                    if private:
                        if not self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not self.bot.bridge.can_access_room(search_room, ctx.user, ignore_mod=ignore_mod):
                            continue
                    else:
                        search_roomdata = self.bot.bridge.get_room(search_room)
                        if self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not show_restricted and search_roomdata['meta']['restricted']:
                            continue
                        elif not show_locked and search_roomdata['meta']['locked']:
                            continue
                    roomlist.append(search_room)

                maxpage = math.ceil(len(roomlist) / limit) - 1
                if interaction:
                    if page > maxpage:
                        page = maxpage
                embed.title = f'{self.bot.ui_emojis.rooms} {helptext}'
                embed.description = selector.get("choose_room")
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room")
                )

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(roomlist):
                        break
                    try:
                        # redundant try-except block
                        name = roomlist[index]
                    except:
                        break
                    search_roomdata = self.bot.bridge.get_room(name)
                    display_name = (
                            self.bot.db['rooms'][name]['meta']['display_name'] or name
                    )
                    description = (
                            self.bot.db['rooms'][name]['meta']['description'] or selector.get("no_desc")
                    )
                    emoji = (
                        '\U0001F527' if search_roomdata['meta']['restricted'] else
                        '\U0001F512' if search_roomdata['meta']['locked'] else
                        '\U0001F310'
                    ) if not self.bot.db['rooms'][name]['meta']['emoji'] else self.bot.db['rooms'][name]['meta'][
                        'emoji']

                    embed.add_field(
                        name=f'{emoji} ' + (
                            f'{display_name} (`{name}`)' if self.bot.db['rooms'][name]['meta']['display_name'] else
                            f'`{display_name}`'
                        ),
                        value=description,
                        inline=False
                    )
                    selection.add_option(
                        label=display_name,
                        emoji=emoji,
                        description=description,
                        value=name
                    )

                if len(embed.fields) == 0:
                    embed.add_field(
                        name=selector.get("noresults_title"),
                        value=selector.get("noresults_body_room"),
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
                            label=selector.rawget("prev", "commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0 or selection.disabled,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next", "commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage or selection.disabled,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget("search", "commons.search"),
                            custom_id='search',
                            emoji=self.bot.ui_emojis.search,
                            disabled=selection.disabled
                        )
                    )
                )

                if ctx.user.id in self.bot.moderators and private:
                    components.add_row(
                        ui.ActionRow(
                            nextcord.ui.Button(
                                style=nextcord.ButtonStyle.gray,
                                label=selector.get("show_all") if ignore_mod else selector.get("hide_inaccessible"),
                                custom_id='viewall'
                            )
                        )
                    )
            elif panel == 1:
                was_searching = True
                search_roomlist = list(self.bot.db['rooms'].keys())

                def search_filter(query, query_cmd):
                    if match == 0:
                        return (
                                (
                                    query.lower() in (
                                        self.bot.db['rooms'][query_cmd]['meta']['display_name'] or query_cmd
                                    )
                                ) and namematch or
                                (
                                    query.lower() in self.bot.db['rooms'][query_cmd]['meta']['description'].lower()
                                    if self.bot.db['rooms'][query_cmd]['meta']['description'] else False
                                ) and descmatch
                        )
                    elif match == 1:
                        return (
                                (((
                                      query.lower() in (
                                          self.bot.db['rooms'][query_cmd]['meta']['display_name'] or query_cmd
                                      )
                                  ) and namematch) or not namematch) and
                                ((
                                     query.lower() in self.bot.db['rooms'][query_cmd]['meta']['description'].lower()
                                     if self.bot.db['rooms'][query_cmd]['meta']['description'] else False
                                 ) and descmatch or not descmatch)
                        )

                roomlist = []
                for search_room in search_roomlist:
                    # yes, this logic is messy.
                    # but it doesn't overwrite the origin server thing so i'm keeping it for now
                    if not search_filter(query, search_room):
                        continue
                    if private:
                        if not self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not self.bot.bridge.can_access_room(search_room, ctx.user, ignore_mod=ignore_mod):
                            continue
                    else:
                        search_roomdata = self.bot.bridge.get_room(search_room)
                        if self.bot.db['rooms'][search_room]['meta']['private']:
                            continue
                        elif not show_restricted and search_roomdata['meta']['restricted']:
                            continue
                        elif not show_locked and search_roomdata['meta']['locked']:
                            continue
                    roomlist.append(search_room)

                embed.title = f'{self.bot.ui_emojis.rooms} {helptext} / search'
                embed.description = selector.get("choose_room")

                if len(roomlist) == 0:
                    maxpage = 0
                    embed.add_field(
                        name=selector.get("noresults_title"),
                        value=selector.get("noresults_body_search"),
                        inline=False
                    )
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room"),
                        disabled=True
                    )
                    selection.add_option(
                        label='No rooms'
                    )
                else:
                    maxpage = math.ceil(len(roomlist) / limit) - 1
                    selection = nextcord.ui.StringSelect(
                        max_values=1, min_values=1, custom_id='selection', placeholder=selector.get("selection_room")
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
                        search_roomdata = self.bot.bridge.get_room(room)
                        display_name = (
                                self.bot.db['rooms'][room]['meta']['display_name'] or room
                        )
                        emoji = (
                            '\U0001F527' if search_roomdata['meta']['restricted'] else
                            '\U0001F512' if search_roomdata['meta']['locked'] else
                            '\U0001F310'
                        ) if not self.bot.db['rooms'][room]['meta']['emoji'] else self.bot.db['rooms'][room]['meta'][
                            'emoji']
                        roomdesc = (
                            self.bot.db['rooms'][room]['meta']['description']
                            if self.bot.db['rooms'][room]['meta']['description'] else selector.get("no_desc")
                        )
                        embed.add_field(
                            name=f'{emoji} ' + (
                                f'{display_name} (`{room}`)' if self.bot.db['rooms'][room]['meta']['display_name'] else
                                f'`{display_name}`'
                            ),
                            value=roomdesc,
                            inline=False
                        )
                        selection.add_option(
                            label=display_name,
                            description=roomdesc if len(roomdesc) <= 100 else roomdesc[:-(len(roomdesc) - 97)] + '...',
                            value=room,
                            emoji=emoji
                        )

                embed.description = selector.rawfget("search_results", "commons.search",
                                                     values={"query": query, "results": len(roomlist)})
                maxcount = (page + 1) * limit
                if maxcount > len(roomlist):
                    maxcount = len(roomlist)
                embed.set_footer(
                    text=(
                            selector.rawfget("page", "commons.search",
                                             values={"page": page + 1, "maxpage": maxpage + 1}) + ' | ' +
                            selector.rawfget("result_count", "commons.search",
                                             values={"lower": page * limit + 1, "upper": maxcount,
                                                     "total": len(roomlist)})
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
                            label=selector.rawget("prev", "commons.navigation"),
                            custom_id='prev',
                            disabled=page <= 0,
                            emoji=self.bot.ui_emojis.prev
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.rawget("next", "commons.navigation"),
                            custom_id='next',
                            disabled=page >= maxpage,
                            emoji=self.bot.ui_emojis.next
                        ),
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.green,
                            label=selector.rawget("search", "commons.search"),
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
                                selector.rawget("match_any", "commons.search") if match == 0 else
                                selector.rawget("match_both", "commons.search")
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
                            label=selector.get("room_name"),
                            style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label=selector.get("room_desc"),
                            style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                        )
                    )
                )
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back", "commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 2:
                search_roomdata = self.bot.bridge.get_room(roomname)
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {helptext} / search / {roomname}'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {helptext} / {roomname}'
                )
                display_name = (
                        self.bot.db['rooms'][roomname]['meta']['display_name'] or roomname
                )
                description = (
                        self.bot.db['rooms'][roomname]['meta']['description'] or selector.get("no_desc")
                )
                emoji = (
                    '\U0001F527' if search_roomdata['meta']['restricted'] else
                    '\U0001F512' if search_roomdata['meta']['locked'] else
                    '\U0001F310'
                ) if not self.bot.db['rooms'][roomname]['meta']['emoji'] else self.bot.db['rooms'][roomname]['meta'][
                    'emoji']
                if self.bot.db['rooms'][roomname]['meta']['display_name']:
                    embed.description = f'# **{emoji} {display_name}**\n`{roomname}`\n\n{description}'
                else:
                    embed.description = f'# **{emoji} `{display_name}`**\n{description}'
                stats = await self.bot.bridge.roomstats(roomname)
                embed.add_field(name=selector.get("statistics"), value=(
                        f':homes: {selector.fget("servers", values={"count": stats["guilds"]})}\n' +
                        f':busts_in_silhouette: {selector.fget("members", values={"count": stats["members"]})}\n' +
                        f':speech_balloon: {selector.fget("messages", values={"count": stats["messages"]})}'
                ))
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=selector.get("view_rules"),
                            custom_id='rules',
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back", "commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )
            elif panel == 3:
                embed.title = (
                    f'{self.bot.ui_emojis.rooms} {helptext} / {selector.rawget("search_nav", "sysmgr.help")} / {roomname} / {selector.get("rules_nav")}'
                    if was_searching else
                    f'{self.bot.ui_emojis.rooms} {helptext} / {roomname} / {selector.get("rules_nav")}'
                )
                index = 0
                text = ''
                rules = self.bot.db['rooms'][roomname]['meta']['rules']
                for rule in rules:
                    if text == '':
                        text = f'1. {rule}'
                    else:
                        text = f'{text}\n{index}. {rule}'
                    index += 1
                if len(rules) == 0:
                    text = selector.get("no_rules")
                embed.description = text
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("back", "commons.navigation"),
                            custom_id='back',
                            emoji=self.bot.ui_emojis.back
                        )
                    )
                )

            if panel == 0:
                embed.set_footer(
                    text=selector.rawfget("page", "commons.search", values={"page": page + 1, "maxpage": maxpage + 1}))
            if not msg:
                msg = await ctx.send(embed=embed, view=components)
                msg = await msg.fetch()
            else:
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=components)
            embed.clear_fields()

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id == ctx.user.id and interaction.message.id == msg.id

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
                    roomname = interaction.data['values'][0]
                    panel = 2
                    page = 0
                elif interaction.data['custom_id'] == 'back':
                    panel -= 1
                    if panel < 0 or panel == 1 and not was_searching:
                        panel = 0
                    page = 0
                elif interaction.data['custom_id'] == 'rules':
                    panel += 1
                elif interaction.data['custom_id'] == 'prev':
                    page -= 1
                elif interaction.data['custom_id'] == 'next':
                    page += 1
                elif interaction.data['custom_id'] == 'search':
                    modal = nextcord.ui.Modal(title=selector.rawget("search_title", "commons.search"), auto_defer=False)
                    modal.add_item(
                        nextcord.ui.TextInput(
                            label=selector.rawget("query", "commons.search"),
                            style=nextcord.TextInputStyle.short,
                            placeholder=selector.rawget("query_prompt", "commons.search")
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
                elif interaction.data['custom_id'] == 'viewall':
                    ignore_mod = not ignore_mod
            elif interaction.type == nextcord.InteractionType.modal_submit:
                panel = 1
                query = interaction.data['components'][0]['components'][0]['value']
                namematch = True
                descmatch = True
                match = 0
                page = 0

    async def report(self, interaction, msg: Union[nextcord.Message, str]):
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
            if isinstance(msg, str):
                msgdata = await self.bot.bridge.fetch_message(int(msg))
            else:
                msgdata = await self.bot.bridge.fetch_message(msg.id)
        except:
            return await interaction.response.send_message(
                language.get('not_found','commons.interaction',language=selector.language_set)
            )

        roomname = msgdata.room
        userid = msgdata.author_id
        content = str(msg.content)  # Prevent tampering w/ original content

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

        def check(new_interaction):
            if not new_interaction.message:
                return False
            return new_interaction.user.id == interaction.user.id and new_interaction.message.id == msg.id

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

    @nextcord.slash_command(
        contexts=[nextcord.InteractionContextType.guild],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def bridge(self, ctx: nextcord.Interaction):
        pass

    @bridge.subcommand(
        description=language.desc('bridge.bind'),
        description_localizations=language.slash_desc('bridge.bind')
    )
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_webhooks=True)
    @restrictions.not_banned()
    @restrictions.no_admin_perms()
    async def bind(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('bridge.bind.room')
    ):
        invite = False
        roominfo = self.bot.bridge.get_room(room.lower())

        if not roominfo:
            invite = True
            try:
                roominfo = self.bot.bridge.get_room(
                    self.bot.bridge.get_invite(room.lower())['room']
                )
            except:
                raise restrictions.UnknownRoom()

        mod_access = ctx.user.id in self.bot.moderators and self.bot.config['private_rooms_mod_access']

        if not invite:
            room = room.lower()
            if not room in self.bot.bridge.rooms:
                raise restrictions.UnknownRoom()

            if not self.bot.bridge.can_join_room(room, ctx.user) and not mod_access:
                raise restrictions.NoRoomJoin()
            roomname = room
        else:
            roomname = self.bot.bridge.get_invite(room.lower())['room']

        selector = language.get_selector(ctx)

        text = []
        if len(roominfo['meta']['rules']) > 0:
            for i in range(len(roominfo['meta']['rules'])):
                text.append(f'{i + 1}. ' + roominfo['meta']['rules'][i])
            text = '\n'.join(text)
        else:
            text = selector.fget("no_rules", values={"prefix": self.bot.command_prefix,
                                                     "room": roominfo['meta']['display_name'] or roomname})

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.loading} {selector.get("check_title")}',
            description=selector.get("check_body"),
            color=self.bot.colors.warning
        )
        msg = await ctx.send(embed=embed)
        msg = await msg.fetch()

        duplicate = self.bot.bridge.check_duplicate(ctx.channel)
        if duplicate:
            embed.colour = self.bot.colors.error
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("already_linked_title")}'
            embed.description = selector.fget("already_linked_body",
                                              values={"room": duplicate, "prefix": self.bot.command_prefix})
            return await msg.edit(embed=embed)

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} {selector.fget("join_title", values={"roomname": roominfo["meta"]["display_name"] or roomname})}',
            description=f'{text}\n\n{selector.get("display")}',
            color=self.bot.colors.warning
        )
        embed.set_footer(text=selector.get("disclaimer"))

        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.green,
                    label=selector.get("accept"),
                    custom_id='accept',
                    emoji=f'{self.bot.ui_emojis.success}'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel", "commons.navigation"),
                    custom_id='cancel',
                    emoji=f'{self.bot.ui_emojis.error}'
                )
            )
        )

        await msg.edit(embed=embed, view=components)

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)

            if interaction.data['custom_id'] == 'cancel':
                await interaction.response.edit_message(view=None)
                raise Exception()
        except:
            embed.title = f'{self.bot.ui_emojis.error} {selector.get("no_agree")}'
            embed.colour = self.bot.colors.error
            return await msg.edit(embed=embed, view=None)

        embed.title = embed.title.replace(self.bot.ui_emojis.rooms, self.bot.ui_emojis.loading, 1)
        await msg.edit(embed=embed, view=None)
        await interaction.response.defer(ephemeral=False, with_message=True)

        webhook = None

        try:
            roomname = room
            if invite:
                roomname = self.bot.bridge.get_invite(room.lower())['room']
                await self.bot.bridge.accept_invite(ctx.user, room.lower())

            webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
            await self.bot.bridge.join_room(ctx.user, roomname, ctx.channel, webhook_id=webhook.id)
        except Exception as e:
            if webhook:
                try:
                    await webhook.delete()
                except:
                    pass

            embed.title = f'{self.bot.ui_emojis.error} {selector.get("failed")}'

            should_raise = False

            if type(e) is self.bot.bridge.InviteNotFoundError:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("invalid_invite")}'
            elif type(e) is self.bot.bridge.RoomBannedError:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("room_banned")}'
            elif type(e) is self.bot.bridge.TooManyConnections:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("too_many")}'
            elif type(e) is self.bot.bridge.AlreadyJoined:
                embed.title = f'{self.bot.ui_emojis.error} {selector.get("already_linked_server")}'
            else:
                should_raise = True

            embed.colour = self.bot.colors.error
            await msg.edit(embed=embed)
            await interaction.delete_original_message()

            if should_raise:
                raise
        else:
            embed.title = f'{self.bot.ui_emojis.success} {selector.get("success")}'
            embed.colour = self.bot.colors.success
            await msg.edit(embed=embed)
            try:
                await msg.pin()
            except:
                pass
            await interaction.edit_original_message(content=f'{self.bot.ui_emojis.success} {selector.get("say_hi")}')

    @bridge.subcommand(
        description=language.desc('bridge.unbind'),
        description_localizations=language.slash_desc('bridge.unbind')
    )
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_webhooks=True)
    @restrictions.no_admin_perms()
    async def unbind(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('bridge.unbind.room', required=False)
    ):
        selector = language.get_selector(ctx)
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_connected")}')
        data = self.bot.bridge.get_room(room.lower())
        if not data:
            raise restrictions.UnknownRoom()

        await ctx.response.defer(ephemeral=False, with_message=True)

        hook_deleted = True
        try:
            hooks = await ctx.guild.webhooks()
            if f'{ctx.guild.id}' in list(data.keys()):
                hook_ids = data[f'{ctx.guild.id}']
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
        except:
            hook_deleted = False

        await self.bot.bridge.leave_room(ctx.guild, room)

        if hook_deleted:
            await ctx.edit_original_message(content=f'{self.bot.ui_emojis.success} {selector.get("success")}')
        else:
            await ctx.edit_original_message(content=f'{self.bot.ui_emojis.warning} {selector.get("success_semi")}')

    async def room_autocomplete(self, room, server, connected=False):
        possible = []
        for roomname in self.bot.bridge.rooms:
            if not roomname.startswith(room):
                continue
            roominfo = self.bot.bridge.get_room(roomname)
            if roominfo['meta']['private'] and not (
                    server in roominfo['meta']['private_meta']['allowed'] or
                    str(server) == roominfo['meta']['private_meta']['server']
            ):
                continue

            platforms = ['discord'] + list(self.bot.platforms.keys())
            for platform in platforms:
                if not platform in roominfo.keys() and not roominfo['meta']['private']:
                    possible.append(roomname)
                    break
                if str(server.id) in roominfo[platform].keys() or not connected:
                    possible.append(roomname)
                    break

        return possible

    async def room_manage_autocomplete(self, room, user):
        possible = []
        for roomname in self.bot.bridge.rooms:
            if self.bot.bridge.can_manage_room(roomname, user) and roomname.startswith(room):
                possible.append(roomname)

        return possible

    @bind.on_autocomplete("room")
    async def bind_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_autocomplete(room, ctx.guild))

    @unbind.on_autocomplete("room")
    async def unbind_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_autocomplete(room, ctx.guild, connected=True))

    @bridge.subcommand(
        description=language.desc('bridge.rooms'),
        description_localizations=language.slash_desc('bridge.rooms')
    )
    async def rooms(self, ctx):
        await self.roomslist(ctx, False)

    @bridge.subcommand(
        name='private-rooms',
        description=language.desc('bridge.private-rooms'),
        description_localizations=language.slash_desc('bridge.private-rooms')
    )
    async def private_rooms(self, ctx):
        await self.roomslist(ctx, True)

    @bridge.subcommand(
        description=language.desc('bridge.servers'),
        description_localizations=language.slash_desc('bridge.servers')
    )
    async def servers(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('bridge.servers.room', required=False)
    ):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel)
            if not room:
                room = self.bot.config['main_room']
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_join_room(room, ctx.user):
            raise restrictions.NoRoomJoin()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room)

        text = ''
        for platform in data.keys():
            if platform == 'meta':
                continue
            for guild_id in data[platform]:
                try:
                    if platform == 'discord':
                        name = self.bot.get_guild(int(guild_id)).name
                    else:
                        support = self.bot.platforms[platform]
                        name = support.name(support.get_server(guild_id))
                except:
                    continue
                if len(text) == 0:
                    text = f'- {name} (`{guild_id}`, {platform})'
                else:
                    text = f'{text}\n- {name} (`{guild_id}`, {platform})'
        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} {selector.fget("title", values={"room": room})}', description=text,
            color=self.bot.colors.unifier
        )
        await ctx.send(embed=embed)

    @servers.on_autocomplete("room")
    async def servers_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_autocomplete(room, ctx.guild))

    @bridge.subcommand(
        description=language.desc('bridge.rules'),
        description_localizations=language.slash_desc('bridge.rules')
    )
    async def rules(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('bridge.rules.room', required=False)
    ):
        if not room:
            room = self.bot.bridge.check_duplicate(ctx.channel) or self.bot.config['main_room']
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if self.bot.db['rooms'][room]['meta']['restricted'] and not ctx.user.id in self.bot.admins:
            return await ctx.send(':eyes:')

        selector = language.get_selector(ctx)

        index = 0
        text = ''
        if room in list(self.bot.db['rooms'].keys()):
            rules = self.bot.db['rooms'][room]['meta']['rules']
            if len(rules) == 0:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_rules")}')
        else:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_rules")}')
        for rule in rules:
            if text == '':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        embed = nextcord.Embed(title=f'{self.bot.ui_emojis.rooms} {selector.get("rules_title")}', description=text,
                               color=self.bot.colors.unifier)
        embed.set_footer(text=selector.rawget("disclaimer", "bridge.bind"))
        await ctx.send(embed=embed)

    @rules.on_autocomplete("room")
    async def rules_autocomplete(self, ctx: nextcord.Interaction, room: str):
        return await ctx.response.send_autocomplete(await self.room_autocomplete(room, ctx.guild))

    @bridge.subcommand(
        description=language.desc('bridge.avatar'),
        description_localizations=language.slash_desc('bridge.avatar')
    )
    @restrictions.not_banned()
    async def avatar(
            self, ctx: nextcord.Interaction,
            url: Optional[str] = slash.option('bridge.avatar.url', required=False)
    ):
        if not url:
            url = ''
        selector = language.get_selector(ctx)

        desc = selector.fget("no_avatar", values={"prefix": self.bot.command_prefix})
        try:
            if f'{ctx.user.id}' in list(self.bot.db['avatars'].keys()):
                avurl = self.bot.db['avatars'][f'{ctx.user.id}']
                desc = selector.fget("custom_avatar", values={"prefix": self.bot.command_prefix})
            else:
                desc = selector.fget("default_avatar", values={"prefix": self.bot.command_prefix})
                avurl = ctx.user.avatar.url
        except:
            avurl = None
        if not url == '':
            avurl = url
        embed = nextcord.Embed(
            title=selector.get("title"),
            description=desc,
            color=self.bot.colors.unifier
        )
        author = f'{ctx.user.name}#{ctx.user.discriminator}'
        if ctx.user.discriminator == '0':
            author = f'@{ctx.user.name}'
        try:
            embed.set_author(name=author, icon_url=avurl)
            embed.set_thumbnail(url=avurl)
        except:
            return await ctx.send(f"{self.bot.ui_emojis.error} Invalid URL!")
        if url == 'remove':
            if not f'{ctx.user.id}' in list(self.bot.db['avatars'].keys()):
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("error_missing")}')
            self.bot.db['avatars'].pop(f'{ctx.user.id}')
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success_unset")}')
        if not url == '':
            embed.title = selector.get("confirmation_title")
            embed.description = selector.get("confirmation_body")
        btns = ui.ActionRow(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label=selector.get("apply"), custom_id='apply',
                disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.gray, label=selector.rawget("cancel", "commons.navigation"),
                custom_id='cancel',
                disabled=False
            )
        )
        components = ui.MessageComponents()
        components.add_row(btns)
        if url == '':
            embed.set_footer(text=selector.fget("change", values={"prefix": self.bot.command_prefix}))
            components = ui.MessageComponents()
        msg = await ctx.send(embed=embed, view=components)
        msg = await msg.fetch()
        if not url == '':
            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

            try:
                interaction = await self.bot.wait_for("interaction", check=check, timeout=30.0)
            except:
                btns.items[0].disabled = True
                btns.items[1].disabled = True
                components = ui.MessageComponents()
                components.add_row(btns)
                await msg.edit(view=components)
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.rawget("timeout", "commons.navigation")}')
            if interaction.data['custom_id'] == 'cancel':
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
            self.bot.db['avatars'].update({f'{ctx.user.id}': url})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            return await interaction.response.send_message(
                f'{self.bot.ui_emojis.success} {selector.get("success_set")}')

    @bridge.subcommand(
        name='create-room',
        description=language.desc('bridge.create-room'),
        description_localizations=language.slash_desc('bridge.create-room')
    )
    @restrictions.can_create()
    @restrictions.not_banned()
    async def create_room(
            self, ctx: nextcord.Interaction,
            room: Optional[str] = slash.option('bridge.create-room.room', required=False)
    ):
        roomtype = 'private'
        dry_run = False

        selector = language.get_selector(ctx)

        if room:
            if room.startswith('-dry-run'):
                if room == '-dry-run':
                    room = None
                dry_run = ctx.user.id == self.bot.owner or ctx.user.id in self.bot.other_owners

        if room:
            room = room.lower().replace(' ', '-')
            if not bool(re.match("^[A-Za-z0-9_-]*$", room)):
                return await ctx.send(
                    f'{self.bot.ui_emojis.error} {selector.get("alphanumeric")}'
                )

        interaction = None
        if ctx.user.id in self.bot.admins or ctx.user.id == self.bot.config['owner']:
            if not self.bot.config['enable_private_rooms']:
                roomtype = 'public'
            else:
                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.StringSelect(
                            options=[
                                nextcord.SelectOption(
                                    value='private',
                                    label=selector.get("private_name"),
                                    description=selector.get("private_desc"),
                                    emoji='\U0001F512'
                                ),
                                nextcord.SelectOption(
                                    value='public',
                                    label=selector.get("public_name"),
                                    description=selector.get("public_desc"),
                                    emoji='\U0001F310'
                                )
                            ],
                            custom_id='selection'
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label=selector.rawget("cancel", "commons.navigation"),
                            custom_id='cancel'
                        )
                    )
                )
                msg = await ctx.send(f'{self.bot.ui_emojis.warning} {selector.get("select")}', view=components)
                msg = await msg.fetch()

                def check(interaction):
                    if not interaction.message:
                        return False
                    return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

                try:
                    interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
                    if interaction.data['custom_id'] == 'cancel':
                        return await interaction.response.edit_message(
                            content=f'{self.bot.ui_emojis.error} {selector.rawget("aborted", "commons.navigation")}',
                            view=None
                        )
                    else:
                        roomtype = interaction.data['values'][0]
                except:
                    return await msg.edit(
                        content=f'{self.bot.ui_emojis.error} {selector.rawget("timeout", "commons.navigation")}',
                        view=None)

        if not self.bot.config['enable_private_rooms'] and roomtype == 'private':
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.rawget("private_disabled","commons.rooms")}', ephemeral=True
            )

        if not room or roomtype == 'private':
            for _ in range(10):
                room = roomtype + '-' + ''.join(
                    random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                if not room in self.bot.bridge.rooms:
                    break
            if room in self.bot.bridge.rooms:
                if interaction:
                    return await interaction.response.edit_message(
                        content=f'{self.bot.ui_emojis.error} {selector.get("unique_fail")}', ephemeral=True
                    )
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("unique_fail")}', ephemeral=True)

        if room in list(self.bot.db['rooms'].keys()):
            if interaction:
                return await interaction.response.edit_message(
                    content=f'{self.bot.ui_emojis.error} {selector.get("exists")}', ephemeral=True
                )
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exists")}', ephemeral=True)
        try:
            roomdata = self.bot.bridge.create_room(
                room, private=roomtype == 'private', dry_run=dry_run, origin=ctx.guild.id
            )
        except self.bot.bridge.TooManyRooms:
            if interaction:
                return await interaction.response.edit_message(
                    content=f'{self.bot.ui_emojis.error} {selector.fget("private_limit", values={"limit": self.bot.config["private_rooms_limit"]})}',
                    view=None, ephemeral=True
                )
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.fget("private_limit", values={"limit": self.bot.config["private_rooms_limit"]})}',
                ephemeral=True
            )

        dry_run_text = ''
        if dry_run:
            dry_run_text = f'\n```js\n{roomdata}```\n-# {self.bot.ui_emojis.warning} {selector.get("dryrun_warning")}'

        roomtype_text = selector.get(roomtype + '_name')

        steps = '\n'.join([f'- {step}' for step in ([
            selector.fget(
                'step_1',
                values={'command': self.bot.get_application_command_from_signature('config create-invite').get_mention()}
            ),
            selector.get('step_2')
        ] if roomtype == 'private' else [selector.get('step_2')])])

        embed = nextcord.Embed(
            title=selector.rawget('nextsteps', 'commons.navigation'),
            description=steps,
            color=self.bot.colors.unifier
        )

        if interaction:
            return await interaction.response.edit_message(
                content=f'{self.bot.ui_emojis.success} {selector.fget("success", values={"roomtype": roomtype_text, "room": room})}{dry_run_text}',
                embed=embed, view=None
            )

        await ctx.send(
            f'{self.bot.ui_emojis.success} {selector.fget("success", values={"roomtype": roomtype_text, "room": room})}{dry_run_text}',
            embed=embed
        )

    @bridge.subcommand(
        name='allocations',
        description=language.desc('bridge.allocations'),
        description_localizations=language.slash_desc('bridge.allocations')
    )
    async def allocations(self, ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)

        if not self.bot.config['enable_private_rooms']:
            return await ctx.send(
                f'{self.bot.ui_emojis.error} {selector.rawget("private_disabled","commons.rooms")}', ephemeral=True
            )

        create_used = self.bot.bridge.get_rooms_count(ctx.guild.id)
        conn_used = self.bot.bridge.get_connections_count(ctx.guild.id)
        create_limit = self.bot.bridge.get_rooms_limit(ctx.guild.id)
        conn_limit = self.bot.bridge.get_connections_limit(ctx.guild.id)

        if create_limit > 0:
            create_warning = f'{self.bot.ui_emojis.warning} ' if (create_used / create_limit) > 0.8 else ''
        else:
            create_warning = ''

        if conn_limit > 0:
            conn_warning = f'{self.bot.ui_emojis.warning} ' if (conn_used / conn_limit) > 0.8 else ''
        else:
            conn_warning = ''

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.rooms} {selector.get("title")}',
            color=self.bot.colors.unifier
        )
        embed.add_field(
            name=selector.get('create'),
            value=create_warning + (
                selector.get('create_unlimited') if create_limit == 0 else
                selector.fget('create_limit', values={"used": create_used, "total": create_limit})
            ),
            inline=False
        )
        embed.add_field(
            name=selector.get('conn'),
            value=conn_warning + (
                selector.get('conn_unlimited') if conn_limit == 0 else
                selector.fget('conn_limit', values={"used": conn_used, "total": conn_limit})
            ),
            inline=False
        )
        embed.set_footer(text=f'{selector.get("disclaimer")}\n{selector.get("disclaimer_2")}')
        await ctx.send(embed=embed)

    @bridge.subcommand(
        description=language.desc('bridge.disband'),
        description_localizations=language.slash_desc('bridge.disband')
    )
    async def disband(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('bridge.disband.room')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.bot.bridge.can_manage_room(room, ctx.user):
            raise restrictions.NoRoomManagement()

        selector = language.get_selector(ctx)

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.fget("confirm_title", values={"room": room})}',
            description=selector.get("confirm_body"),
            color=self.bot.colors.warning
        )
        view = ui.MessageComponents()
        view.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("disband"),
                    custom_id='disband'
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel", "commons.navigation"),
                    custom_id='cancel'
                )
            )
        )
        msg = await ctx.send(embed=embed, view=view)
        msg = await msg.fetch()
        view.clear_items()
        view.row_count = 0
        view.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.red,
                    label=selector.get("disband"),
                    custom_id='disband',
                    disabled=True
                ),
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.gray,
                    label=selector.rawget("cancel", "commons.navigation"),
                    custom_id='cancel',
                    disabled=True
                )
            )
        )

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.user.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=60)
        except:
            return await msg.edit(view=view)

        if interaction.data['custom_id'] == 'cancel':
            return await interaction.response.edit_message(view=view)

        self.bot.bridge.delete_room(room)
        embed.title = f'{self.bot.ui_emojis.success} {selector.fget("success_title", values={"room": room})}'
        embed.description = selector.get("success_body")
        embed.colour = self.bot.colors.success
        await interaction.response.edit_message(embed=embed, view=None)
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())

    @bridge.subcommand(
        description=language.desc('bridge.roomkick'),
        description_localizations=language.slash_desc('bridge.roomkick')
    )
    @restrictions.not_banned()
    async def roomkick(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('bridge.roomkick.room'),
            server: str = slash.option('bridge.roomkick.server')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_moderate(ctx.user, room):
            raise restrictions.NoRoomModeration()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room.lower())

        platform = None
        for check_platform in data.keys():
            if check_platform == 'meta':
                continue
            if f'{server}' in data[check_platform].keys():
                platform = check_platform
                break

        if not platform:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("not_connected")}')

        server_name = None
        try:
            if platform == 'discord':
                guild_obj = self.bot.get_guild(int(server))
                server_name = guild_obj.name
            else:
                support = self.bot.platforms[platform]
                guild_obj = support.get_server(server)
                server_name = support.name(guild_obj)

            hooks = await guild_obj.webhooks()
            if server in list(data.keys()):
                hook_ids = data[server]
            else:
                hook_ids = []
            for webhook in hooks:
                if webhook.id in hook_ids:
                    await webhook.delete()
                    break
        except:
            pass
        data[platform].pop(server)
        self.bot.bridge.update_room(room, data)

        if not server_name:
            server_name = '[unknown server]'

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"server": server_name})}')

    @bridge.subcommand(
        description=language.desc('bridge.roomban'),
        description_localizations=language.slash_desc('bridge.roomban')
    )
    @restrictions.not_banned()
    async def roomban(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('bridge.roomban.room'),
            server: str = slash.option('bridge.roomban.server')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_moderate(ctx.user, room):
            raise restrictions.NoRoomModeration()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room.lower())

        platform = None
        for check_platform in data.keys():
            if check_platform == 'meta':
                continue
            if server in data[check_platform].keys():
                platform = check_platform
                break

        if server in data['meta']['banned']:
            return await ctx.send(selector.get('duplicate'))

        server_name = None
        try:
            if platform == 'discord':
                guild_obj = self.bot.get_guild(int(server))
                server_name = guild_obj.name
            else:
                if not platform:
                    # try every platform until a match can be found
                    guild_obj = self.bot.get_guild(int(server))
                    if not guild_obj:
                        for _check_platform in self.bot.platforms.keys():
                            try:
                                support = self.bot.platforms[platform]
                                guild_obj = support.get_server(server)
                                server_name = support.name(guild_obj)
                                break
                            except:
                                pass
                    else:
                        server_name = guild_obj.name
                else:
                    support = self.bot.platforms[platform]
                    guild_obj = support.get_server(server)
                    server_name = support.name(guild_obj)

            if platform == 'discord':
                hooks = await guild_obj.webhooks()
                if server in list(data.keys()):
                    hook_ids = data[server]
                else:
                    hook_ids = []
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        await webhook.delete()
                        break
        except:
            pass

        if platform:
            data[platform].pop(server)

        if not server in data['meta']['banned']:
            data['meta']['banned'].append(server)

        self.bot.bridge.update_room(room, data)

        if not server_name:
            server_name = '[unknown server]'

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"server": server_name})}')

    @bridge.subcommand(
        description=language.desc('bridge.roomunban'),
        description_localizations=language.slash_desc('bridge.roomunban')
    )
    @restrictions.not_banned()
    async def roomunban(
            self, ctx: nextcord.Interaction,
            room: str = slash.option('bridge.roomunban.room'),
            server: str = slash.option('bridge.roomunban.server')
    ):
        room = room.lower()
        if not room in self.bot.bridge.rooms:
            raise restrictions.UnknownRoom()

        if not self.can_moderate(ctx.user, room):
            raise restrictions.NoRoomModeration()

        selector = language.get_selector(ctx)

        data = self.bot.bridge.get_room(room.lower())

        platform = None
        for check_platform in data.keys():
            if check_platform == 'meta':
                continue
            if f'{server}' in data[check_platform].keys():
                platform = check_platform
                break

        if not server in data['meta']['banned']:
            return await ctx.send(selector.get('missing'))

        server_name = None
        try:
            if platform == 'discord':
                guild_obj = self.bot.get_guild(int(server))
                server_name = guild_obj.name
            else:
                if not platform:
                    # try every platform until a match can be found
                    guild_obj = self.bot.get_guild(int(server))
                    if not guild_obj:
                        for _check_platform in self.bot.platforms.keys():
                            try:
                                support = self.bot.platforms[platform]
                                guild_obj = support.get_server(server)
                                server_name = support.name(guild_obj)
                                break
                            except:
                                pass
                    else:
                        server_name = guild_obj.name
                else:
                    support = self.bot.platforms[platform]
                    guild_obj = support.get_server(server)
                    server_name = support.name(guild_obj)

            if platform == 'discord':
                hooks = await guild_obj.webhooks()
                if server in list(data.keys()):
                    hook_ids = data[server]
                else:
                    hook_ids = []
                for webhook in hooks:
                    if webhook.id in hook_ids:
                        await webhook.delete()
                        break
        except:
            pass

        if platform:
            data[platform].pop(server)

        if server in data['meta']['banned']:
            data['meta']['banned'].remove(server)

        self.bot.bridge.update_room(room, data)

        if not server_name:
            server_name = '[unknown server]'

        await ctx.send(f'{self.bot.ui_emojis.success} {selector.fget("success", values={"server": server_name})}')

    @bridge.subcommand(
        description=language.desc('bridge.color'),
        description_localizations=language.slash_desc('bridge.color')
    )
    @restrictions.not_banned_guild()
    async def color(
            self, ctx: nextcord.Interaction,
            color: Optional[str] = slash.option('bridge.color.color', required=False)
    ):
        selector = language.get_selector(ctx)

        if not color:
            try:
                current_color = self.bot.db['colors'][f'{ctx.user.id}']
                if current_color=='':
                    current_color = selector.get('default')
                    embed_color = self.bot.colors.unifier
                elif current_color=='inherit':
                    current_color = selector.get('inherit')
                    embed_color = ctx.user.color.value
                else:
                    embed_color = ast.literal_eval('0x'+current_color)
            except:
                current_color = 'Default'
                embed_color = self.bot.colors.unifier
            embed = nextcord.Embed(title=selector.get('title'),description=current_color,color=embed_color)
            await ctx.send(embed=embed)
        elif color=='inherit':
            self.bot.db['colors'].update({f'{ctx.user.id}':'inherit'})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} '+selector.get('success_inherit'))
        else:
            try:
                tuple(int(color.replace('#','',1)[i:i + 2], 16) for i in (0, 2, 4))
            except:
                return await ctx.send(selector.get('invalid'))
            self.bot.db['colors'].update({f'{ctx.user.id}':color})
            await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
            await ctx.send(f'{self.bot.ui_emojis.success} '+selector.get('success_custom'))

    @bridge.subcommand(
        description=language.desc('bridge.nickname'),
        description_localizations=language.slash_desc('bridge.nickname')
    )
    @restrictions.not_banned_guild()
    async def nickname(
            self, ctx: nextcord.Interaction,
            nickname: Optional[str] = slash.option('bridge.nickname.nickname', required=False)
    ):
        selector = language.get_selector(ctx)
        if len(nickname) > 33:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("exceed")}')
        if len(nickname) == 0:
            self.bot.db['nicknames'].pop(f'{ctx.user.id}', None)
        else:
            self.bot.db['nicknames'].update({f'{ctx.user.id}': nickname})
        await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
        await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

    @nextcord.slash_command(
        description=language.desc('bridge.ping'),
        description_localizations=language.slash_desc('bridge.ping'),
        contexts=[nextcord.InteractionContextType.guild, nextcord.InteractionContextType.bot_dm],
        integration_types=[nextcord.IntegrationType.guild_install]
    )
    async def ping(self, ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)
        msg = await ctx.send(selector.get('ping'))
        msg = await msg.fetch()
        t = time.time()
        pingmsg = await ctx.send(selector.get('ping'))
        diff = round((time.time() - t) * 1000, 1)
        await pingmsg.delete()
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

    @bridge.subcommand(
        description=language.desc('bridge.emojis'),
        description_localizations=language.slash_desc('bridge.emojis')
    )
    async def emojis(self,ctx: nextcord.Interaction):
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
                            label=language.get('search','commons.search',language=selector.language_set),
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
                            label=language.get('search','commons.search',language=selector.language_set),
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
                embed.set_footer(text=language.fget(
                    'page','commons.search',values={'page':page+1,'maxpage':maxpage+1 if maxpage >= 0 else 1},
                    language=selector.language_set
                ))
            if not msg:
                msg = await ctx.send(embed=embed, view=components)
                msg = await msg.fetch()
            else:
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=components)
            embed.clear_fields()

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id == ctx.user.id and interaction.message.id == msg.id

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

    @bridge.subcommand(
        description=language.desc('bridge.modping'),
        description_localizations=language.slash_desc('bridge.modping')
    )
    @restrictions.cooldown(rate=1, per=1800, type='user')
    @restrictions.not_banned()
    async def modping(self,ctx):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_logging']:
            return await ctx.send(selector.get('disabled'))

        if ctx.guild.id in self.bot.db['underattack']:
            raise restrictions.UnderAttack()

        room = self.bot.bridge.get_channel_room(ctx.channel)

        if not room:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("invalid")}', ephemeral=True)

        roominfo = self.bot.bridge.get_room(room)
        if roominfo['meta']['private']:
            return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("private")}', ephemeral=True)

        guild = self.bot.get_guild(self.bot.config['home_guild'])

        author = f'{ctx.user.name}#{ctx.user.discriminator}'
        if ctx.user.discriminator=='0':
            author = f'@{ctx.user.name}'

        for ch in guild.text_channels:
            connected_room = self.bot.bridge.get_channel_room(ch)
            if not connected_room or not connected_room == room:
                continue
            try:
                role = self.bot.config["moderator_role"]
            except:
                return await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("no_moderator")}', ephemeral=True)
            await ch.send(
                f'<@&{role}> {selector.fget("needhelp",values={"username":author,"userid":ctx.user.id,"guildname":ctx.guild.name,"guildid":ctx.guild.id})}',
                allowed_mentions=nextcord.AllowedMentions(roles=True,everyone=False,users=False)
            )
            return await ctx.send(f'{self.bot.ui_emojis.success} {selector.get("success")}')

        await ctx.send(f'{self.bot.ui_emojis.error} {selector.get("bad_config")}', ephemeral=True)

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
                    (
                        f'# {list(msg.reactions.keys())[index]}\n' if platform=='discord' else
                        f'# :{list(msg.reactions.keys())[index].split(":")[1]}:\n'
                    ) if ':' in list(msg.reactions.keys())[index] else (
                        f'# {list(msg.reactions.keys())[index]}\n'
                    )
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
                if not interaction.message:
                    return False
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

    @bridge.subcommand(name='report', description=language.desc('bridge.report'))
    async def report_slash(
            self, ctx,
            message: str = slash.option('bridge.report.message')
    ):
        await self.report(ctx, message)

    @nextcord.message_command(name='Report message')
    async def report_ctx(self, interaction, message: nextcord.Message):
        await self.report(interaction, message)

    @bridge.subcommand(description=language.desc('bridge.serverstatus'))
    @restrictions.not_banned_guild()
    async def serverstatus(self, ctx: nextcord.Interaction):
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

    @bridge.subcommand(description=language.desc('bridge.level'))
    async def level(
            self, ctx: nextcord.Interaction,
            user: Optional[nextcord.User] = slash.option('bridge.level.user', required=False)
    ):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_exp']:
            return await ctx.send(selector.get('disabled'), ephemeral=True)
        if not user:
            user = ctx.user
        try:
            data = self.bot.db['exp'][f'{user.id}']
        except:
            data = {'experience':0,'level':1,'progress':0}
        bars = round(data['progress']*20)
        empty = 20-bars
        progressbar = '['+(bars*'|')+(empty*' ')+']'
        embed = nextcord.Embed(
            title=(
                selector.get("title_self") if user.id==ctx.user.id else
                selector.fget("title_other", values={"username": user.global_name if user.global_name else user.name})
             ),
            description=(
                f'{selector.fget("level", values={"level": data["level"]})} | {selector.fget("exp",values={"exp": round(data["experience"],2)})}\n\n'+
                f'`{progressbar}`\n{selector.fget("progress",values={"progress": round(data["progress"]*100)})}'
            ),
            color=self.bot.colors.unifier
        )
        embed.set_author(
            name=f'@{user.name}',
            icon_url=user.avatar.url if user.avatar else None
        )
        await ctx.send(embed=embed)

    @bridge.subcommand(description=language.desc('bridge.leaderboard'))
    async def leaderboard(self, ctx: nextcord.Interaction):
        selector = language.get_selector(ctx)
        if not self.bot.config['enable_exp']:
            return await ctx.send(language.get('disabled','bridge.level',language=selector.language_set), ephemeral=True)
        expdata = dict(self.bot.db['exp'])
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
                msg = await msg.fetch()
            else:
                await interaction.response.edit_message(embed=embed,view=components)

            def check(interaction):
                if not interaction.message:
                    return False
                return interaction.user.id==ctx.user.id and interaction.message.id==msg.id

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

                await interaction.response.send_message(f'{self.bot.ui_emojis.loading} Deleting message...',ephemeral=True)

                try:
                    await self.bot.bridge.delete_parent(msg_id)
                    if msg.webhook:
                        raise ValueError()
                    await interaction.message.edit(view=components)
                    return await interaction.edit_original_message(content=f'{self.bot.ui_emojis.success} ' + language.get("parent_delete","moderation.delete",language=selector.language_set))
                except:
                    try:
                        deleted = await self.bot.bridge.delete_copies(msg_id)
                        await interaction.message.edit(view=components)
                        return await interaction.edit_original_message(content=f'{self.bot.ui_emojis.success} ' + language.fget("children_delete","moderation.delete",values={"count": deleted},language=selector.language_set))
                    except:
                        traceback.print_exc()
                        await interaction.edit_original_message(content=f'{self.bot.ui_emojis.error} ' + language.get("error","moderation.delete",language=selector.language_set))
            elif interaction.data["custom_id"].startswith('rpreview_'):
                selector = language.get_selector('bridge.report',userid=interaction.user.id)
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
                            await thread.send(selector.rawget("reviewed_thread", "bridge.report"))
                        except:
                            pass
                    self.bot.db['report_threads'].pop(str(interaction.message.id))
                    await self.bot.loop.run_in_executor(None, lambda: self.bot.db.save_data())
                await interaction.message.edit(embed=embed,view=components)
                await interaction.edit_original_message(content=selector.rawget('reviewed', 'bridge.report'))
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

            await interaction.response.send_message(f'{self.bot.ui_emojis.loading} Sending report...', ephemeral=True)
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
    @restrictions_legacy.owner()
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
    @restrictions_legacy.owner()
    @restrictions_legacy.no_admin_perms()
    async def system(self, ctx, room, *, content):
        selector = language.get_selector(ctx)
        await self.bot.bridge.send(room,ctx.message,'discord',system=True,content_override=content)
        for platform in self.bot.platforms.keys():
            await self.bot.bridge.send(
                room, ctx.message, platform, system=True,
                content_override=content)
        await ctx.send(selector.get("success"))

    @commands.command(hidden=True, description=language.desc("bridge.purge"))
    @restrictions_legacy.owner()
    async def purge(self, ctx, user_id):
        selector = language.get_selector(ctx)

        embed = nextcord.Embed(
            title=f'{self.bot.ui_emojis.warning} {selector.fget("warning_title",values={"user": user_id})}',
            description=selector.get("warning_body"),
            color=self.bot.colors.warning
        )

        components = ui.MessageComponents()
        components.add_row(
            ui.ActionRow(
                nextcord.ui.Button(
                    label=selector.get("purge"),
                    style=nextcord.ButtonStyle.red,
                    custom_id='confirm'
                ),
                nextcord.ui.Button(
                    label=selector.rawget("cancel", "commons.navigation"),
                    style=nextcord.ButtonStyle.gray,
                    custom_id='cancel'
                )
            )
        )

        msg = await ctx.send(embed=embed, view=components)

        def check(interaction):
            if not interaction.message:
                return False
            return interaction.message.id == msg.id and interaction.user.id == ctx.author.id

        try:
            interaction = await self.bot.wait_for('interaction', check=check, timeout=30)
        except:
            return await msg.edit(view=None)

        if not interaction.data['custom_id'] == 'confirm':
            return await interaction.response.edit_message(view=None)

        await interaction.response.defer(ephemeral=True, with_message=True)

        # purge messages
        for message in self.bot.bridge.bridged:
            if str(message.author_id) == user_id:
                await self.bot.bridge.delete_message(message)

        # purge preferences and exp
        self.bot.db['nicknames'].pop(str(user_id), None)
        self.bot.db['avatars'].pop(str(user_id), None)
        self.bot.db['colors'].pop(str(user_id), None)
        self.bot.db['exp'].pop(str(user_id), None)
        self.bot.db['languages'].pop(str(user_id), None)

        # remove verified status
        try:
            self.bot.db['trusted'].remove(int(user_id))
        except:
            pass

        embed.title = f'{self.bot.ui_emojis.success} {selector.get("success_title")}'
        embed.description = selector.get("success_body")
        embed.colour = self.bot.colors.success

        await msg.edit(embed=embed, view=None)
        await interaction.delete_original_message()

    @commands.Cog.listener()
    async def on_message(self, message):
        selector = language.get_selector("bridge.bridge",userid=message.author.id)
        if not type(message.channel) is nextcord.TextChannel:
            return
        if message.content.startswith(f'{self.bot.command_prefix}system'):
            return
        if message.guild.me.guild_permissions.administrator:
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

        bridgeable_stickers = [sticker for sticker in message.stickers if not sticker.format == nextcord.StickerFormatType.lottie]

        if len(message.content)==0 and len(message.embeds)==0 and len(message.attachments)==0 and len(bridgeable_stickers) == 0:
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

        # Optimized logic
        roomname = self.bot.bridge.get_channel_room(message.channel)
        if not roomname:
            return

        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        og_embeds = []
        if message.author.bot or len(message.embeds) > 0:
            for emb in message.embeds:
                og_embeds.append(emb)

        unsafe, responses = await self.bot.bridge.run_security(message)
        message = await self.bot.bridge.run_stylizing(message)

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
        selector = language.get_selector('bridge.bridge', userid=after.author.id)
        if before.content == after.content:
            return

        message = after

        if message.author.id in self.bot.db['fullbanned']:
            return

        if message.guild == None:
            return

        if message.guild.me.guild_permissions.administrator:
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

        roomname = self.bot.bridge.get_channel_room(message.channel)

        if not roomname:
            return

        if is_room_locked(roomname, self.bot.db) and not message.author.id in self.bot.admins:
            return

        try:
            msg: UnifierBridge.UnifierMessage = await self.bot.bridge.fetch_message(message.id)
            if not str(msg.id)==str(message.id):
                raise ValueError()
        except:
            return

        try:
            roomdata = self.bot.bridge.get_room(roomname)
            if not self.bot.config['enable_logging'] or not self.bot.config['logging_edit'] or roomdata['meta']['private']:
                # do not log
                raise RuntimeError()
            ch = self.bot.get_channel(self.bot.config['logs_channel'])

            before_content = before.content
            content = message.content

            if len(before.content) == 0:
                before_content = '[no content]'
            if len(message.content) == 0:
                content = '[no content]'
            embed = nextcord.Embed(
                title=selector.fget('edited', values={'roomname': roomname}), color=self.bot.colors.blurple
            )
            embed.add_field(name=selector.get('original'), value=before_content, inline=False)
            embed.add_field(name=selector.get('new'), value=content, inline=False)
            embed.add_field(name='IDs',
                            value=f'MSG: {message.id}\nSVR: {message.guild.id}\nUSR: {message.author.id}',
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

            if message.guild.me.guild_permissions.administrator:
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

            roomname = self.bot.bridge.get_channel_room(message.channel)

            if not roomname:
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

        if message.guild.me.guild_permissions.administrator:
            return

        roomname = self.bot.bridge.get_channel_room(message.channel)

        if not roomname:
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
            roomdata = self.bot.bridge.get_room(roomname)
            if not self.bot.config['enable_logging'] or not self.bot.config['logging_delete'] or roomdata['meta']['private']:
                # do not log
                raise RuntimeError()
            ch = self.bot.get_channel(self.bot.config['logs_channel'])

            content = message.content

            if len(message.content) == 0:
                content = '[no content]'
            embed = nextcord.Embed(
                title=selector.fget('deleted',values={'roomname':roomname}), description=content,
                color=self.bot.colors.purple
            )
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

    async def cog_command_error(self, ctx: nextcord.Interaction, error):
        await self.bot.exhandler.handle(ctx, error)

def setup(bot):
    bot.add_cog(Bridge(bot))
