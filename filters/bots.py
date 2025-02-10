from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'bots',
            'Bots Filter',
            'A filter that blocks bot messages (excluding system messages).'
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(not message['bot'], None, message='Bots may not talk in this Room.')
