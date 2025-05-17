from feather import driver
from typing import Optional, Union, Any

class Channel:
    def __init__(self, driver: driver.FeatherDriver, channel_id: Union[int, str], name: Optional[str] = None):
        self.__driver = driver # Feather Driver for interacting with platform API
        self.__id = channel_id # Channel ID
        self.name = name # Channel name, if applicable

    @property
    def id(self) -> Union[int, str]:
        return self.__id

    @property
    def _channel(self) -> Any:
        return self.__driver.get_channel(self.__id)

    def __str__(self) -> Optional[str]:
        return '#' + self.name

    def __repr__(self) -> str:
        return f'<Channel id={self.__id} name={self.name}>'

    async def send(self, content: str, data: dict) -> Any:
        """Sends a message to the channel."""
        return await self.__driver.send(self._channel, content, special=data)

    async def create_webhook(self, name: str, avatar: Optional[str] = None) -> Any:
        """Creates a webhook in the channel."""
        return await self.__driver.create_webhook(self._channel, name, avatar)
