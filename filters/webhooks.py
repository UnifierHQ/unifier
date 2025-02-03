from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'bots',
            'Webhooks Filter',
            (
                'A filter that blocks webhook messages. Webhooks created by Unifier will always be blocked regardless '+
                'of this filter.'
            )
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(not message['webhook_id'], None, message='Webhook messages may not talk in this Room.')
