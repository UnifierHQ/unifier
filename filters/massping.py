from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'massping',
            'Massping Filter',
            'Blocks mass pings from being sent.'
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(
            not ('@everyone' in message['content'] or '@here' in message['content']), data,
            message='Mass pings are not allowed.', should_log=True, should_contribute=True
        )
