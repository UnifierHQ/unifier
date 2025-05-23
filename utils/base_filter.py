from typing import Optional

class MissingFilter(Exception):
    pass

class MissingCheck(Exception):
    pass

class FilterResult:
    def __init__(self, allowed: bool, data: Optional[dict] = None, message: Optional[str] = None,
                 should_log: bool = False, should_contribute: bool = False, safe_content: Optional[str] = None):
        self.__allowed = allowed # Whether the message can be bridged or not
        self.__data = data or {} # Data to store in the temporary storage
        self.__message = message # Message to show if allowed is False and should_log is True
        self.__should_log = should_log # Whether filter detection should be logged or not
        self.__should_contribute = should_contribute # Whether filter detection should contribute to auto UAM or not
        self.__safe_content = safe_content # Substitute content to send if allowed is False

    @property
    def allowed(self):
        return self.__allowed

    @property
    def data(self):
        return self.__data

    @property
    def message(self):
        return self.__message or 'A filter blocked your message.'

    @property
    def should_log(self):
        return self.__should_log

    @property
    def should_contribute(self):
        return self.__should_contribute

    @property
    def safe_content(self):
        return self.__safe_content

class FilterConfig:
    types = {
        'string': str,
        'number': int,
        'integer': int,
        'float': float,
        'boolean': bool,
    }

    def __init__(self, name, description, config_type, limits: Optional[tuple] = None, default=None):
        self.__name = name
        self.__description = description
        self.__type = config_type
        self.__limits = limits
        self.__default = default

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def type(self):
        return self.__type

    @property
    def limits(self):
        return self.__limits

    @property
    def default(self):
        return self.__default

class BaseFilter:
    def __init__(self, filter_id, name, description):
        self.__id: str = filter_id
        self.__name: str = name
        self.__description: str = description
        self.__configs = {}

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def configs(self):
        return self.__configs

    def add_config(self, config_id, config: FilterConfig):
        if config_id in self.__configs:
            raise ValueError('config already exists')

        self.__configs.update({config_id: config})

    def check(self, message, data) -> FilterResult:
        """Checks if a content is allowed or not allowed by the filter."""
        raise MissingFilter()
