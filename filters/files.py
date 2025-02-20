from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'files',
            'Files Filter',
            'A filter that blocks files from being bridged.'
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(message['files'] == 0, None, message='Attachments are not allowed here.')
