from utils.base_filter import FilterResult, BaseFilter
import re

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'links',
            'Links Filter',
            'A filter that blocks links.'
        )

    def find_urls(self, text):
        regex: str = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, text)
        return [x[0] for x in url]

    def check(self, message, data) -> FilterResult:
        return FilterResult(
            len(self.find_urls(message['content'])) == 0, None, message='Links are not allowed here.',
            should_log=True
        )
