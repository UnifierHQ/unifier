from feather.models import user as feather_user, channel as feather_channel
from typing import Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from feather.driver import FeatherDriver
else:
    FeatherDriver = Any

class Server:
    def __init__(self, platform: FeatherDriver, server_id: Union[int, str], name: str, **kwargs):
        self.platform: FeatherDriver = platform
        self.id: Union[int, str] = server_id
        self.name: str = name
        self.members: list[feather_user.User] = kwargs.get('members', [])
        self.channels: list[feather_channel.Channel] = kwargs.get('channels', [])

    async def fetch_webhook(self, webhook_id: Union[int, str]) -> Any:
        """Fetches a webhook by its ID."""
        if not self.platform.uses_webhooks:
            raise NotImplementedError("platform does not use webhooks")

        webhook: Any = await self.platform.fetch_webhook(webhook_id, self.id)
        return webhook
