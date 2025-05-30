from typing import Union, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from feather.driver import FeatherDriver
    from feather.models.message import FeatherMessageContent, FeatherMessage
else:
    FeatherDriver = Any
    FeatherMessage = Any
    FeatherMessageContent = Any

class User:
    def __init__(self, user_id: Union[int, str], name: str, platform: FeatherDriver, **kwargs):
        self.id: Union[int, str] = user_id # If a webhook was used, this should be the webhook ID
        self.name: str = name
        self.platform: FeatherDriver = platform
        self._display_name: Optional[str] = kwargs.get('display_name') # this is internal to allow for aliases
        self.avatar_url: Optional[str] = kwargs.get('avatar_url')
        self.bot: bool = kwargs.get('bot', False)
        self.webhook: bool = kwargs.get('webhook', False)

    @property
    def display_name(self) -> str:
        """Returns the display name of the user if it exists"""
        return self._display_name or self.name

    @property
    def global_name(self) -> str:
        """Alias for display_name"""
        return self.display_name

    async def send(self, content: FeatherMessageContent) -> FeatherMessage:
        """Sends a message to the user."""
        return await self.platform.send(content)

    def __repr__(self):
        return f"User(user_id={self.id}, name='{self.name}', platform='{self.platform}')"