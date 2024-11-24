from utils.base_filter import FilterResult, BaseFilter

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'invites',
            'Invites Filter',
            'A filter that blocks server invites.'
        )

    def check(self, _user, _is_bot, content, _files, _data) -> FilterResult:
        keywords = [
            'discord.gg/', 'discord.com/invite/', 'discordapp.com/invite/'
        ]

        contains = [keyword for keyword in keywords if keyword in content]
        return FilterResult(len(contains) == 0, None)
