from typing import Any

class FeatherHost:
    """A wrapper for the host bot."""

    def __init__(self, host: Any, required_api_level: int):
        self.__host = host

        try:
            if not self.__host.supports_feather:
                raise RuntimeError()
        except:
            raise RuntimeError("host does not support Feather")

        if self.__host.feather_api_level < required_api_level:
            raise RuntimeError(
                f'Feather requires API level {required_api_level} or higher, but the host is at level '+
                f'{self.__host.feather_api_level}'
            )

    @property
    def config(self) -> dict:
        """Returns the host configuration."""
        return self.__host.config

    def encrypt(self, *args, **kwargs):
        return self.__host.encrypt(*args, **kwargs)

    def decrypt(self, *args, **kwargs):
        return self.__host.decrypt(*args, **kwargs)
