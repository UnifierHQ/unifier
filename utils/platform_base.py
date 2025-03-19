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

# This program serves as a template class for bridge platform Plugins.
# We recommend all such Plugins inherit this class, so missing implementations
# can be handled gracefully by the bot.

import asyncio
import time
import nextcord
from typing import Union

class MissingImplementation(Exception):
    """An exception used when something isn't implemented.
    The bot will gracefully handle this exception"""
    pass

class Permissions:
    """NUPS Permissions class."""
    def __init__(self):
        self.ban_members = False
        self.manage_channels = False

class RateLimit:
    def __init__(self, bucket: str, limit: int, reset: int):
        self.__bucket = bucket
        self.__limit = limit
        self.__reset = reset
        self.__count = 0
        self.__last_reset = time.time()

        if self.__limit <= 0:
            raise ValueError('limit must be greater than 0')
        if self.__reset <= 0:
            raise ValueError('reset must be greater than 0')

    class BucketOnCooldown(Exception):
        pass

    @property
    def bucket(self):
        return self.__bucket

    @property
    def limit(self):
        return self.__limit

    @property
    def reset(self):
        return self.__reset

    @property
    def count(self):
        if time.time() > self.__last_reset + self.__reset:
            self.__last_reset = time.time()
            self.__count = 0

        return self.__count

    def increment(self):
        if time.time() > self.__last_reset + self.__reset:
            self.__last_reset = time.time()
            self.__count = 0

        if self.__count >= self.__limit:
            raise self.BucketOnCooldown(
                f'bucket {self.__bucket} is on cooldown for {round(self.__last_reset + self.__reset - time.time())} seconds'
            )

        self.__count += 1
        return self.__count

    def force_ratelimit(self):
        self.__count = self.__limit
        self.__last_reset = time.time()

    async def wait(self, ignore_count=False):
        if not ignore_count and self.__count < self.__limit:
            raise ValueError(f'bucket {self.__bucket} is not on cooldown')

        await asyncio.sleep(self.__last_reset + self.__reset - time.time())

class PlatformBase:
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent
        self.enable_tb = False # change this to True to enable threaded bridge
        self.uses_webhooks = False # change this to True if webhooks are needed
        self.__available = False
        self.allowed_content_types = []
        self.reply_using_text = False # change this to True if the platform needs to show message reply using text
        self.files_per_guild = False # change this to True if the platform library wipes file objects' data after send
        self.uses_image_markdown = False # change this to True if the platform uses media markdown (i.e. ![](image url))
        self.filesize_limit = 25000000 # change this to the maximum total file size allowed by the platform
        self.supports_agegate = False # change this to True if the platform supports age-gated content
        self.buckets = {} # use this to store rate limit buckets

    @property
    def attachment_size_limit(self):
        # This should return the smaller filesize limit. Don't override this.
        if self.parent.config['global_filesize_limit'] <= 0:
            return self.filesize_limit

        return (
            self.filesize_limit if self.filesize_limit < self.parent.config['global_filesize_limit']
            else self.parent.config['global_filesize_limit']
        )

    def is_available(self):
        return self.__available

    def error_is_unavoidable(self, error):
        """Checks if the error was unavoidable such as 5xx, 401, 403, etc.
        Any other 4xx errors should be considered avoidable."""
        raise MissingImplementation()

    def attach_bot(self, bot):
        """In case a bot object could not be provided, it can be attached here."""
        self.bot = bot
        self.__available = True

    async def handle_ratelimit(self, bucket):
        while True:
            try:
                bucket.increment()
                return
            except bucket.BucketOnCooldown:
                await bucket.wait()

    def bot_id(self):
        raise MissingImplementation()

    def get_server(self, server_id):
        """Gets a server from cache."""
        raise MissingImplementation()

    def get_channel(self, channel_id):
        """Gets a channel from cache."""
        raise MissingImplementation()

    def get_user(self, user_id):
        """Gets a user from cache."""
        raise MissingImplementation()

    def get_member(self, server, user_id):
        """Gets a server member from cache."""
        raise MissingImplementation()

    def channel(self, message):
        """Returns the channel object from a message."""
        raise MissingImplementation()

    def is_nsfw(self, obj):
        """Returns if an object (usually a server or channel) is marked as NSFW.
        Make sure to set self.supports_agegate to True once you've implemented this."""
        raise MissingImplementation()

    def channel_id(self, obj):
        """Returns the channel ID from an object."""
        raise MissingImplementation()

    def server(self, obj):
        """Returns the server object from an object."""
        raise MissingImplementation()

    def server_id(self, obj):
        """Returns the server ID from an object."""
        raise MissingImplementation()

    def content(self, message):
        """Returns the content from a message."""
        raise MissingImplementation()

    def reply(self, message):
        """Returns the reply from a message.
        If the message replied to does not exist in cache, this should return its ID instead."""
        raise MissingImplementation()

    def roles(self, member):
        """Returns the roles of a member."""
        raise MissingImplementation()

    def get_hex(self, role):
        """Returns the hex value of a role's color."""
        raise MissingImplementation()

    def author(self, message):
        """Returns the author object from a message."""
        raise MissingImplementation()

    def embeds(self, message):
        raise MissingImplementation()

    def attachments(self, message):
        raise MissingImplementation()

    def url(self, message):
        """Returns the URL for a message."""
        raise MissingImplementation()

    def get_id(self, obj):
        """Returns the ID from any object."""
        raise MissingImplementation()

    def display_name(self, user, message=None):
        """Returns the display name of a user object, username if no display name is set."""
        raise MissingImplementation()

    def user_name(self, user, message=None):
        """Returns the username of a user object."""
        raise MissingImplementation()

    def name(self, obj):
        """Alias to user_name intended for non-user objects.
        Override this if needed."""
        return self.user_name(obj)

    def avatar(self, user, message=None):
        """Returns the avatar URL of a user object."""
        raise MissingImplementation()

    def permissions(self, user, channel=None):
        """Returns the permissions of a user object.
        If channel exists, return channel permissions rather than server permissions."""
        raise MissingImplementation()

    def is_bot(self, user):
        """Returns if the user is a bot or not."""
        raise MissingImplementation()

    def attachment_size(self, attachment):
        """Returns the size of a given attachment."""
        raise MissingImplementation()

    def attachment_type(self, attachment):
        """Returns the content type of a given attachment."""
        raise MissingImplementation()

    def attachment_type_allowed(self, content_type):
        """Returns if the content type can be bridged.
        If allowed_content_types is empty, this will always return True."""
        return len(self.allowed_content_types) == 0 or content_type in self.allowed_content_types

    def convert_embeds(self, embeds: list):
        raise MissingImplementation()

    def convert_embeds_discord(self, embeds: list):
        raise MissingImplementation()

    def remove_spoilers(self, content: str):
        """Removes spoilers from a message."""
        raise MissingImplementation()

    def webhook_id(self, message):
        """Returns the webhook ID from a message."""
        raise MissingImplementation()

    async def fetch_server(self, server_id):
        """Fetches the server from the API."""
        raise MissingImplementation()

    async def fetch_channel(self, channel_id):
        """Fetches the channel from the API."""
        raise MissingImplementation()

    async def fetch_webhook(self, webhook_id, server_id):
        """Fetches the webhook from the API.
        server_id can be ignored if the API does not require it."""
        raise MissingImplementation()

    async def fetch_message(self, channel, message_id):
        """Fetches a message from the API."""
        raise MissingImplementation()

    async def make_friendly(self, text):
        """Converts the message so it's friendly with other platforms.
        For example, <@userid> should be converted to @username."""
        raise MissingImplementation()

    async def to_discord_file(self, file):
        """Converts an attachment object to a nextcord.File object."""
        raise MissingImplementation()

    async def to_platform_file(self, file: Union[nextcord.Attachment, nextcord.File]):
        """Converts a nextcord.Attachment or nextcord.File object to the platform's file object."""
        raise MissingImplementation()

    def file_name(self, attachment):
        """Returns the filename of an attachment."""
        raise MissingImplementation()

    def file_url(self, attachment):
        """Returns the URL of an attachment."""
        raise MissingImplementation()

    async def send(self, channel, content, special: dict = None):
        """Sends a message to a channel, then returns the message object.
        Special features, such as embeds and files, can be specified in special."""

        # Note for replies:
        # If the bridge key is present in special, reply will be a UnifierMessage.
        # Otherwise, it will either be the message's ID or your platform's message object.
        # Please handle both cases accordingly.

        raise MissingImplementation()

    async def edit(self, message, content, source: str = 'discord', special: dict = None):
        """Edits a message.
        Special features, such as embeds and files, can be specified in special."""
        raise MissingImplementation()

    async def delete(self, message):
        """Deletes a message."""
        raise MissingImplementation()
