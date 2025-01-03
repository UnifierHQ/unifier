from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'invites',
            'Files Filter',
            'A filter that blocks files from being bridged.'
        )

    def check(self, _user, _is_bot, _content, files, _data) -> FilterResult:
        return FilterResult(files == 0, None, message='Attachments are not allowed here.')
