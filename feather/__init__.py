from feather import driver, webhook_cache
from feather.models import channel
import nextcord

class Feather:
    """Feather is the bridge framework for Unifier."""

    def __init__(self, host: nextcord.Client):
        self.__host = host
        self.__webhook_cache = webhook_cache.WebhookCache()

    @property
    def webhook_cache(self) -> webhook_cache.WebhookCache:
        return self.__webhook_cache
