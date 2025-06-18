from feather import host as feather_host
from feather.models import message as feather_message, user as feather_user, channel as feather_channel, server as feather_server
import asyncio
import aiomultiprocess
from typing import Optional

class RoomSettings:
    def __init__(self, name, description, items):
        self.name = name
        self.description = description
        self.items = items

# Room.platforms structure:
# {
#   "platform_name": {
#     "server_id": [
#       {"channel": "channel_id", "webhook": "webhook_id (if applicable)"}
#     ]
#   }
# }

class Room:
    def __init__(self, host: feather_host.FeatherHost, name: str, description: str, platforms: Optional[dict] = None):
        self.__host: feather_host.FeatherHost = host
        self.name: str = name
        self.description: str = description
        self.platforms: dict[str, dict[str, list[dict]]] = platforms or {}

    class _RoomDestination:
        """Internal object to be used by Feather. Do not instantiate manually."""

        def __init__(self, platform: str, server_id: str, channel: str, webhook: Optional[str] = None):
            self.platform: str = platform
            self.server_id: str = server_id
            self.channel: str = channel
            self.webhook: Optional[str] = webhook

    class _Room

    async def _platform_send_indiv(self, platform: str, content: feather_message.FeatherMessageContent,
                                   destination: _RoomDestination):
        pass

    async def platform_send(self, platform: str, content: feather_message.FeatherMessageContent, channel: feather_channel.Channel):
        destinations: list = []
        author: feather_user.User = content.author
        server: feather_server.Server = content.server

        for platform in self.platforms.keys():
            if platform not in self.__host:
                continue

            if server.id not in self.platforms[platform]:
                continue

            for dest in self.platforms[platform][server.id]:
                channel_id = dest['channel']
                webhook_id = dest.get('webhook')

                # Create a destination object
                destination = self._RoomDestination(platform, server.id, channel_id, webhook_id)
                destinations.append(destination)

        async with aiomultiprocess.Pool() as pool:
            return await pool.apply(self._platform_send_indiv, (platform, content))

    async def send(self, content: feather_message.FeatherMessageContent):
        threads = []
        for platform in self.platforms.keys():
            task = asyncio.create_task(self.platform_send(platform, content))
            threads.append(task)

        return await asyncio.gather(*threads)
