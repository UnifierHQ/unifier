from utils.base_filter import FilterResult, BaseFilter, FilterConfig
import time

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'slowmode',
            'Slowmode',
            'Enforces slowmode in rooms.'
        )
        self.add_config(
            'slowdown',
            FilterConfig(
                'Slowdown', 'Sets the slowmode duration.', 'integer',
                default=0
            )
        )

    def check(self, user, _is_bot, content, _files, data) -> FilterResult:
        if user in data['data']:
            if time.time() < data['data'][user]:
                return FilterResult(
                    False, data,
                    message=f'Slowmode is enabled. Try again in {round(data["data"][user] - time.time())} seconds.'
                )
            else:
                data['data'].update({user: time.time() + data['config']['slowdown']})
                return FilterResult(True, data)
        else:
            data['data'].update({user: time.time() + data['config']['slowdown']})
            return FilterResult(True, data)