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

    def check(self, _user, _is_bot, content, _files, _data) -> FilterResult:
        return FilterResult(len(self.find_urls(content)) == 0, None)
