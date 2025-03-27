from feather import driver
import nextcord
from io import BytesIO
from typing import Union, Optional, Any

class DiscordDriver(driver.Driver):
    def __init__(self, bot, parent):
        super().__init__(bot, parent)
        self.enable_tb = True
        self.uses_webhooks = True
        self.filesize_limit = 10000000
        self.supports_agegate = True

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
        return self.bot.user.id

    def get_server(self, server_id):
        """Gets a server from cache."""
        return self.bot.get_server(server_id)

    def get_channel(self, channel_id):
        """Gets a channel from cache."""
        return self.bot.get_channel(channel_id)

    def get_user(self, user_id):
        """Gets a user from cache."""
        return self.bot.get_user(user_id)

    def get_member(self, server, user_id):
        """Gets a server member from cache."""
        return server.get_member(user_id)

    def channel(self, message):
        """Returns the channel object from a message."""
        return message.channel

    def is_nsfw(self, obj):
        """Returns if an object (usually a server or channel) is marked as NSFW.
        Make sure to set self.supports_agegate to True once you've implemented this."""
        return obj.is_nsfw()

    def channel_id(self, obj):
        """Returns the channel ID from an object."""
        return obj.channel.id

    def server(self, obj):
        """Returns the server object from an object."""
        return obj.server

    def server_id(self, obj):
        """Returns the server ID from an object."""
        return obj.server.id

    def content(self, message):
        """Returns the content from a message."""
        return message.content

    def reply(self, message):
        """Returns the reply from a message.
        If the message replied to does not exist in cache, this should return its ID instead."""
        return message.reference

    def roles(self, member):
        """Returns the roles of a member."""
        return member.roles

    def get_hex(self, role):
        """Returns the hex value of a role's color."""
        return hex(role.color)[2:].zfill(6)

    def author(self, message):
        """Returns the author object from a message."""
        return message.author

    def embeds(self, message):
        return message.embeds

    def attachments(self, message):
        return message.attachments

    def url(self, message):
        """Returns the URL for a message."""
        return message.jump_url

    def get_id(self, obj):
        """Returns the ID from any object."""
        return obj.id

    def display_name(self, user, message=None):
        """Returns the display name of a user object, username if no display name is set."""
        if message and message.webhook_id:
            return message.author.display_name or message.author.name

        return user.display_name or user.name

    def user_name(self, user, message=None):
        """Returns the username of a user object."""
        if message and message.webhook_id:
            return message.author.name

        return user.name

    def name(self, obj):
        """Alias to user_name intended for non-user objects.
        Override this if needed."""
        return self.user_name(obj)

    def avatar(self, user, message=None):
        """Returns the avatar URL of a user object."""
        if message and message.webhook_id:
            return message.author.avatar.url if message.author.avatar else None

        return user.avatar.url if user.avatar else None

    def permissions(self, user, channel=None):
        """Returns the permissions of a user object.
        If channel exists, return channel permissions rather than server permissions."""
        if channel:
            user_perms = channel.permissions_for(user)
        else:
            user_perms = user.guild_permissions

        permissions = driver.Permissions()
        permissions.ban_members = user_perms.ban_members
        permissions.manage_channels = user_perms.manage_channels
        return permissions

    def is_bot(self, user):
        """Returns if the user is a bot or not."""
        return user.bot

    def attachment_size(self, attachment):
        """Returns the size of a given attachment."""
        return attachment.size

    def attachment_type(self, attachment):
        """Returns the content type of a given attachment."""
        return attachment.content_type

    def attachment_type_allowed(self, content_type):
        """Returns if the content type can be bridged.
        If allowed_content_types is empty, this will always return True."""
        return len(self.allowed_content_types) == 0 or content_type in self.allowed_content_types

    def convert_embeds(self, embeds: list):
        # These are already in Discord format
        return embeds

    def convert_embeds_discord(self, embeds: list):
        # These are already in Discord format
        return embeds

    def remove_spoilers(self, content: str):
        """Removes spoilers from a message."""
        split_content = content.split('||')
        to_merge = []

        # This must be 3 or higher
        if len(split_content) >= 3:
            to_merge.append(split_content.pop(0))

            while len(split_content) > 0:
                if len(split_content) >= 2:
                    split_content.pop(0)
                    to_merge.append('■■■■■■')
                to_merge.append(split_content.pop(0))

            return ''.join(to_merge)
        else:
            return content

    def webhook_id(self, message):
        """Returns the webhook ID from a message."""
        return message.webhook_id

    async def fetch_server(self, server_id):
        """Fetches the server from the API."""
        return await self.bot.fetch_guild(server_id)

    async def fetch_channel(self, channel_id):
        """Fetches the channel from the API."""
        return await self.bot.fetch_channel(channel_id)

    async def fetch_webhook(self, webhook_id, server_id):
        """Fetches the webhook from the API.
        server_id can be ignored if the API does not require it."""
        return await self.bot.fetch_webhook(webhook_id)

    async def fetch_message(self, channel, message_id):
        """Fetches a message from the API."""
        return await channel.fetch_message(message_id)

    async def make_friendly(self, text, server=None, image_markdown=False):
        """Converts the message so it's friendly with other platforms.
        For example, <@userid> should be converted to @username."""
        # Replace community channels with placeholders
        text = text.replace('<id:customize>', '#Channels & Roles')
        text = text.replace('<id:browse>', '#Browse Channels')

        # Replace emoji with URL if text contains solely an emoji
        if (text.startswith('<:') or text.startswith('<a:')) and text.endswith('>'):
            try:
                emoji_name = text.split(':')[1]
                emoji_id = int(text.split(':')[2].replace('>', '', 1))
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
                        userid = int(components[offset].split('>', 1)[0].replace('&', '', 1))
                    except:
                        pass
            try:
                if is_role:
                    role = server.get_role(userid)
                    display_name = role.name
                else:
                    user = self.get_user(userid)
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
            channel = self.get_channel(channelid)
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
                emojiafter = components[offset].split(':', 1)[1].split('>')[0] + '>'
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

    async def to_discord_file(self, file):
        """Converts an attachment object to a nextcord.File object."""
        return await file.to_file(use_cached=True, force_close=False, spoiler=file.is_spoiler())

    async def to_platform_file(self, file: Union[nextcord.Attachment, nextcord.File]):
        """Converts a nextcord.Attachment or nextcord.File object to the platform's file object."""
        # this is already in discord format
        if type(file) is nextcord.File:
            return file

        return await self.to_discord_file(file)

    def file_name(self, attachment):
        """Returns the filename of an attachment."""
        return attachment.filename

    def file_url(self, attachment):
        """Returns the URL of an attachment."""
        return attachment.url

    async def send(self, channel, content, special: dict = None):
        """Sends a message to a channel, then returns the message object.
        Special features, such as embeds and files, can be specified in special."""

        # Note for replies:
        # If the bridge key is present in special, reply will be a UnifierMessage.
        # Otherwise, it will either be the message's ID or your platform's message object.
        # Please handle both cases accordingly.

        files = special.get('files', [])
        embeds = special.get('embeds', [])
        reply: Any = special.get('reply', None)
        reply_content: str = special.get('reply_content', None)

        if not files:
            files = []

        if not embeds:
            embeds = []

        if 'bridge' in special.keys():
            # check if we're in a room
            room = self.parent.bridge.get_channel_room(channel, platform='guilded')

            if room:
                webhook_id = self.parent.bridge.get_room(room)['guilded'][channel.server.id][0]
                try:
                    webhook = self.get_webhook(webhook_id)
                except:
                    server = self.get_server(channel.server.id)
                    webhook = await server.fetch_webhook(webhook_id)
                    self.store_webhook(webhook)
            else:
                raise ValueError('channel is not linked to a room, remove bridge from special')

            # as Guilded only supports ascii for usernames, remove all non-ascii characters
            # user emojis will be omitted
            name = special['bridge']['name'].encode("ascii", errors="ignore").decode() or 'Empty username'
            avatar = special['bridge']['avatar']

            replytext = ''

            if reply:
                # reply must be a UnifierMessage here
                # as reply cannot be none, PyUnresolvedReferences can be ignored
                reply_name = None

                try:
                    # noinspection PyUnresolvedReferences
                    if reply.source == 'discord':
                        # noinspection PyUnresolvedReferences
                        user = self.parent.get_user(int(reply.author_id))
                        reply_name = user.global_name or user.name
                    elif reply.source == 'guilded':
                        # noinspection PyUnresolvedReferences
                        user = self.bot.get_user(reply.author_id)
                        reply_name = user.name
                    else:
                        # noinspection PyUnresolvedReferences
                        source_support = self.parent.platforms[reply.source]
                        # noinspection PyUnresolvedReferences
                        reply_name = source_support.display_name(source_support.get_user(reply.author_id))
                except:
                    pass

                if not reply_name:
                    reply_name = 'unknown'
                else:
                    reply_name = '@' + reply_name.replace('[', '').replace(']', '')

                if reply_content:
                    replytext += f' - *{reply_content}*\n'
                else:
                    replytext += '\n'

            if len(replytext + content) == 0:
                content = '[empty message]'

            return await webhook.send(replytext + content, embeds=embeds, files=files, username=name, avatar_url=avatar)
        else:
            if reply:
                # reply must be an ID or ChatMessage here
                if type(reply) is str:
                    reply = await channel.fetch_message(reply)
                elif type(reply) is nextcord.Message:
                    pass
                elif type(reply) is nextcord.MessageReference:
                    if not reply.cached_message:
                        reply = await channel.fetch_message(reply.message_id)
                else:
                    reply = None
            return await channel.send(content, embeds=embeds, files=files, reply_to=[reply] if reply else None)

    async def edit(self, message, content, source: str = 'discord', special: dict = None):
        """Edits a message.
        Special features, such as embeds and files, can be specified in special."""
        raise MissingImplementation()

    async def delete(self, message):
        """Deletes a message."""
        raise MissingImplementation()
