from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'invites',
            'Invites Filter',
            'A filter that blocks server invites.'
        )

    def check(self, message, data) -> FilterResult:
        keywords = [
            'discord.gg/', 'discord.com/invite/', 'discordapp.com/invite/'
        ]

        contains = [keyword for keyword in keywords if keyword in message['content']]
        return FilterResult(
            len(contains) == 0, None, message='Server invites are not allowed here.', should_log=True
        )
