from utils.base_filter import FilterResult, BaseFilter
from better_profanity import profanity

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'swearing',
            'Swearing Filter',
            'Keep your chat family-friendly!'
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(
            not profanity.contains_profanity(message['content']), None, message='No swearing allowed!'
        )
