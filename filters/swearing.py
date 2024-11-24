from utils.base_filter import FilterResult, BaseFilter
from better_profanity import profanity

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'swearing',
            'Swearing Filter',
            'Keep your chat family-friendly!'
        )

    def check(self, _user, _is_bot, content, _files, _data) -> FilterResult:
        return FilterResult(not profanity.contains_profanity(content), None)
