from feather.models import user as feather_user, channel as feather_channel, server as feather_server, attachment as feather_attachment
from typing import Union, Optional, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from feather.driver import FeatherDriver
else:
    FeatherDriver = Any

class FeatherMessageError(Exception):
    """Base class for all Feather message errors."""
    pass

class FeatherMessageDeleted(FeatherMessageError):
    """The message was deleted, so actions cannot be performed on it."""
    def __init__(self, message: 'FeatherMessage'):
        super().__init__(f'message {message.id} was deleted, no actions can be done on it')
        self.message: 'FeatherMessage' = message

class FeatherMessageUpdate:
    def __init__(self, content: str, edited_at: Union[datetime, int]):
        self.content: str = content
        self.edited_at: Union[datetime, int] = edited_at

        # Convert timestamps to unix
        if isinstance(self.edited_at, int):
            self.edited_at = datetime.fromtimestamp(self.edited_at)

class FeatherMessageEntry:
    """A message entry for Feather message cache. Contains minimal data needed for some features."""

    def __init__(self, platform: FeatherDriver, message_id: Union[int, str], channel: feather_channel.Channel,
                 server: feather_server.Server,
                 replies: Optional[list[Union['FeatherMessageEntry', 'FeatherMessage']]] = None,
                 forwarded: Union['FeatherMessageEntry', 'FeatherMessage', None] = None):
        self.platform: FeatherDriver = platform
        self.id: Union[int, str] = message_id
        self.channel: feather_channel.Channel = channel
        self.server: feather_server.Server = server
        self.replies: list[Union['FeatherMessageEntry', 'FeatherMessage']] = replies or []
        self.forwarded: Optional[Union['FeatherMessageEntry', 'FeatherMessage']] = forwarded

    def to_json(self) -> dict:
        """Returns the message entry as a dict object."""

        return {
            'id': self.id,
            'channel': self.channel.id,
            'server': self.server.id if self.server else None,
            'platform': self.platform.name,
            'replies': [entry.id for entry in self.replies],
            'forwarded': self.forwarded.id if self.forwarded else None
        }

class FeatherMessageReference(FeatherMessageEntry):
    """A reference to a message. Used to represent replies and forwards."""

    def __init__(self, platform: FeatherDriver, message_id: Union[int, str], channel: feather_channel.Channel,
                 server: feather_server.Server, **kwargs):
        super().__init__(platform, message_id, channel, server)
        self.type: FeatherMessageReferenceType = kwargs.get('type', FeatherMessageReferenceType.reply)
        self.__cached_message: Optional[FeatherMessage] = kwargs.get('cached_message', None)

        # Remove unused attributes
        del self.replies
        del self.forwarded

    @property
    def invalid(self) -> bool:
        """Whether the message reference is invalid and should not be used."""

        # For now, Message.deleted is the only condition determining if a message reference is invalid
        # We can add more conditions later if needed
        return (
            self.__cached_message.deleted if self.__cached_message else False
        )

    @property
    def cached_message(self) -> Optional['FeatherMessage']:
        """Returns the cached message if it exists."""
        return self.__cached_message if not self.__cached_message.deleted else None

    def to_json(self) -> dict:
        """Feather doesn't use json objects for message references, don't use this."""
        raise RuntimeError('cannot convert a reference to json as this is not used by Feather')

class FeatherMessageReferenceType(Enum):
    reply = 0
    forward = 1

class FeatherMessageContent:
    """A class containing data for a message to be sent."""

    def __init__(self, content: str, author: feather_user.User, channel: feather_channel.Channel,
                 server: Optional[feather_server.Server], **kwargs):
        self.content: str = content
        self.author: feather_user.User = author
        self.channel: feather_channel.Channel = channel
        self.server: Optional[feather_server.Server] = server
        self.replies: list[FeatherMessageReference] = kwargs.get('replies', [])
        self.files: list[feather_attachment.File] = kwargs.get('files', [])
        self.forwarded: Optional[FeatherMessageReference] = kwargs.get('forwarded')

class FeatherMessage(FeatherMessageContent):
    def __init__(self, platform: FeatherDriver, message_id: Union[int, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform: FeatherDriver = platform
        self.id: int | str = message_id
        self.attachments: list[feather_attachment.Attachment] = kwargs.get('attachments', [])
        self.replies: list[FeatherMessageReference] = kwargs.get('replies', [])
        self.forwarded: Optional[FeatherMessageReference] = kwargs.get('forwarded', None)
        self.created_at: Union[datetime, int] = kwargs.get('created_at', datetime.now())
        self.edited_at: Optional[datetime, int] = kwargs.get('edited_at', None)
        self.__deleted: bool = False # we'll let Feather delete the message on its own

        # Convert timestamps to unix
        if isinstance(self.created_at, int):
            self.created_at = datetime.fromtimestamp(self.created_at)
        if isinstance(self.edited_at, int):
            self.edited_at = datetime.fromtimestamp(self.edited_at)

        # Delete unused attributes
        del self.files

    @property
    def deleted(self) -> bool:
        """Whether the message was deleted or not."""
        return self.__deleted

    def get_reference(self, reference_type: FeatherMessageReferenceType) -> FeatherMessageReference:
        """Returns a reference to the message, which can be used for replies or forwards."""
        if self.__deleted:
            raise FeatherMessageDeleted(self)

        return FeatherMessageReference(
            self.platform, self.id, self.channel, self.server, type=reference_type, cached_message=self
        )

    def get_entry(self) -> FeatherMessageEntry:
        """Returns a message entry for the message.
        This also works for deleted messages."""

        return FeatherMessageEntry(
            self.platform, self.id, self.channel, self.server, replies=self.replies, forwarded=self.forwarded
        )

    async def edit(self, content: str, **kwargs):
        """Edits the message."""
        if self.__deleted:
            raise FeatherMessageDeleted(self)

        edit_data: FeatherMessageUpdate = await self.platform.edit(self, content, **kwargs)
        self.content = edit_data.content
        self.edited_at = edit_data.edited_at

    async def delete(self):
        """Deletes the message."""
        if self.__deleted:
            raise FeatherMessageDeleted(self)

        await self.platform.delete(self)
        self.__deleted = True

class FeatherMessageGroup:
    """A group of FeatherMessage objects. This object is stored to Feather's message cache.
    Replaces Bridge v2.5's UnifierMessage object."""

    def __init__(self, group_id: Union[int, str, None] = None, messages: Optional[list[FeatherMessage]] = None):
        self.id: Optional[int, str] = group_id # Group ID
        self.messages: dict = {} # Actual list for messages
        self.id_cache: dict = {} # Cache for speeding up server/channel ID lookups, not necessarily required

        if messages:
            # If there's no group ID, the group ID will be the first message in the list
            if not self.id:
                self.id = messages[0].id

            for message in messages:
                if not message.platform.name in self.messages:
                    self.messages[message.platform.name] = {}

                self.messages[message.platform.name][message.id] = message
                self.id_cache[message.id] = {
                    'platform': message.platform.name,
                    'server': message.server.id if message.server else None,
                    'channel': message.channel.id
                }

    def get_messages(self, identifier: Union[int, str], cache_only: bool = False) -> Union[list[FeatherMessage], list]:
        """Returns messages from the group. The identifier can be the message/channel/server ID."""

        # Cache attempt 1: message ID
        if identifier in self.id_cache:
            return [self.messages.get(self.id_cache[identifier]['platform'], {}).get(identifier)]

        results: list[list] = []

        def to_objects() -> Union[list[FeatherMessage], list]:
            objects = []
            for result in results:
                message_obj: FeatherMessage = self.messages.get(result[0], {}).get(result[1])
                if message_obj:
                    objects.append(message_obj)

            return objects

        # Cache attempt 2: server or channel ID
        for key, value in self.id_cache.items():
            if identifier in value.values():
                results.append([value['platform'], key])

        # Return if searching from cache only
        if cache_only:
            return to_objects()

        # Now we do a cacheless search
        for platform in self.messages:
            if identifier in self.messages.get(platform, {}):
                results.append([platform, identifier])

        return to_objects()

    def get_message(self, identifier: Union[int, str], cache_only: bool = False) -> Optional[FeatherMessage]:
        """Returns a message from the group. The identifier can be the message/channel/server ID.
        If there are multiple results, the first one will be returned."""

        # We already have get_messages, so we can reuse that
        messages = self.get_messages(identifier, cache_only)
        return messages[0] if messages else None

    def to_json(self) -> dict:
        """Returns the group as a dict object."""

        # Base dict object
        dict_obj = {'id': self.id, 'message_ids': list(self.id_cache.keys()), 'messages': {}}

        # Add messages to dict object
        for platform in self.messages:
            platform_msgs: dict[Union[int, str], dict] = {}
            for message_id in self.messages[platform]:
                # Add message IDs to the list to speed up message retrievals from cache
                dict_obj['message_ids'].append(message_id)

                # Add message entry to dict
                message_obj: FeatherMessage = self.messages[platform][message_id]
                platform_msgs[message_id] = message_obj.get_entry().to_json()

            dict_obj['messages'][platform] = platform_msgs

        return dict_obj

