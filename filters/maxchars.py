from utils.base_filter import FilterResult, BaseFilter, FilterConfig

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'maxchars',
            'Max Characters',
            'Limits maximum characters that can be sent in a message.'
        )
        self.add_config(
            'limit',
            FilterConfig(
                'Limit', 'Sets the character limit.', 'integer', default=2000,
                limits=(0, 2000)
            )
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(
            len(message['content']) <= data['config']['limit'], data,
            message=f'Your message should be {data["config"]["limit"]} characters or less.', should_log=True
        )
