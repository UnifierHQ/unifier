from feather import driver, host
from typing import Any

class DriverManagerError(Exception):
    """Base class for exceptions raised by the driver manager."""
    pass

class DriverAlreadyExistsError(DriverManagerError):
    """Driver was already registered to the manager,"""
    def __init__(self, platform: str):
        super().__init__(f'driver for platform {platform} already registered.')

class DriverNotFoundError(DriverManagerError):
    """Driver does not exist in the manager."""

    def __init__(self, platform: str):
        super().__init__(f'driver for platform {platform} does not exist')

class FeatherDriverManager:
    def __init__(self, host_obj: host.FeatherHost, required_api_level: int):
        self.__drivers: dict = {}
        self.__host: host.FeatherHost = host_obj
        self.required_api_level: int = required_api_level

    def create_driver(self, platform: str, bot: Any):
        """Creates a driver for a platform."""

        if platform in self.__drivers:
            raise DriverAlreadyExistsError(platform)

        driver_obj = driver.FeatherDriver(bot, self.__host, platform, self.required_api_level)
        self.__drivers[platform] = driver_obj

    def get_driver(self, platform: str):
        """Returns the driver for a platform."""
        return self.__drivers.get(platform)

    def delete_driver(self, platform: str):
        """Deletes the driver for a platform."""
        if platform in self.__drivers:
            del self.__drivers[platform]
        else:
            raise DriverNotFoundError(platform)
