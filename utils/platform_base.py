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

import nextcord

class MissingImplementation(Exception):
    """An exception used when something isn't implemented.
    The bot will gracefully handle this exception"""
    pass

class Permissions:
    """NUPS Permissions class."""
    def __init__(self):
        self.ban_members = False
        self.manage_channels = False

class PlatformBase:
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent
        self.enable_tb = False # change this to True to enable threaded bridge
        self.uses_webhooks = False # change this to True if webhooks are needed
        self.__available = False
        self.allowed_content_types = []

    def is_available(self):
        return self.__available

    def attach_bot(self, bot):
        """In case a bot object could not be provided, it can be attached here."""
        self.bot = bot
        self.__available = True

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

    def server(self, obj):
        """Returns the server object from an object."""
        raise MissingImplementation()

    def content(self, message):
        """Returns the content from a message."""
        raise MissingImplementation()

    def reply(self, message):
        """Returns the reply from a message."""
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

    def display_name(self, user):
        """Returns the display name of a user object, username if no display name is set."""
        raise MissingImplementation()

    def user_name(self, user):
        """Returns the username of a user object."""
        raise MissingImplementation()

    def name(self, obj):
        """Alias to user_name intended for non-user objects.
        Override this if needed."""
        return self.user_name(obj)

    def avatar(self, user):
        """Returns the avatar URL of a user object."""
        raise MissingImplementation()

    def permissions(self, user, channel=False):
        """Returns the permissions of a user object.
        If channel is True, return channel permissions rather than server permissions."""
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

    def convert_embeds(self, embeds):
        raise MissingImplementation()

    def convert_embeds_discord(self, embeds):
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

    async def make_friendly(self, text):
        """Converts the message so it's friendly with other platforms.
        For example, <@userid> should be converted to @username."""
        raise MissingImplementation()

    async def to_discord_file(self, file):
        """Converts an attachment object to a nextcord.File object."""
        raise MissingImplementation()

    async def to_platform_file(self, file: nextcord.Attachment):
        """Converts a nextcord.Attachment object to the platform's file object."""
        raise MissingImplementation()

    async def send(self, channel, content, special: dict = None):
        """Sends a message to a channel, then returns the message object.
        Special features, such as embeds and files, can be specified in special."""
        raise MissingImplementation()

    async def edit(self, message, content, special: dict = None):
        """Edits a message.
        Special features, such as embeds and files, can be specified in special."""
        raise MissingImplementation()

    async def delete(self, message):
        """Deletes a message."""
        raise MissingImplementation()
