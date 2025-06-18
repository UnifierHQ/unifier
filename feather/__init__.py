from feather import driver, driver_manager, host, webhook_cache, data
from feather.models import channel, message, room
from typing import Any
import nextcord

__version__ = "1.0.0" # Feather framework version
feather_api_level = 1 # increment every Feather API update, including non-breaking changes
feather_api_level_required_host = 1 # increment every Feather API update with a breaking change for the host
feather_api_level_required_driver = 1 # increment every Feather API update with a breaking change for the driver

class Feather:
    """Feather is the bridge framework for Unifier."""

    def __init__(self, host_client: nextcord.Client):
        # Add host object and create webhook cache
        self.__host: Any = host_client
        self.__webhook_cache = webhook_cache.WebhookCache()

        # Set API levels
        self.api_level: int = feather_api_level
        self.api_level_required_host: int = feather_api_level_required_host
        self.api_level_required_driver: int = feather_api_level_required_driver

        # Initialize host and driver manager
        self.host: host.FeatherHost = host.FeatherHost(host, self.api_level_required_host)
        self.drivers: driver_manager.FeatherDriverManager = driver_manager.FeatherDriverManager(
            self.host, self.api_level_required_driver
        )

        self.__data: data.BridgeData
        self.__cache: data.HotColdData = data.HotColdData(self.host, 'feather_cache')

    @property
    def webhook_cache(self) -> webhook_cache.WebhookCache:
        return self.__webhook_cache

    @property
    def rooms(self) -> list[room.Room]:
        """Returns all rooms in the host."""

