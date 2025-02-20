from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'known-spammers',
            'Suspected Spammers Filter',
            'Prevents users that are suspected to have engaged in spam activities from talking.'
        )

    def check(self, message, data) -> FilterResult:
        return FilterResult(
            not message['suspected_spammer'], None,
            message='Discord has currently flagged your account as a likely spammer. Please try again later.',
            should_log=True
        )
