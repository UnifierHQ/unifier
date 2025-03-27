from typing import Union, Any

class WebhookCache:
    def __init__(self):
        self._cache = {}

    def store(self, webhook_id: Union[int, str], webhook: Any):
        self._cache[webhook_id] = webhook

    def store_multiple(self, webhooks: dict):
        self._cache.update(webhooks)

    def get(self, webhook_id: Union[int, str]):
        return self._cache.get(webhook_id)

    def get_multiple(self, webhook_ids: list):
        return {webhook_id: self._cache.get(webhook_id) for webhook_id in webhook_ids}
