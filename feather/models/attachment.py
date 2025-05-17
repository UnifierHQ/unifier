from feather import driver
from typing import Any, Optional

class File:
    def __init__(self, platform: driver.FeatherDriver, filename: str, data: bytes):
        self.platform: driver.FeatherDriver = platform
        self.filename: str = filename
        self.bytes: bytes = data

    @property
    def fp(self) -> bytes:
        """Alias for self.bytes"""
        return self.bytes

class Attachment:
    def __init__(self, platform: driver.FeatherDriver, filename: str, url: str, data_obj: Any,
                 description: Optional[str] = None, spoiler: bool = False, content_type: Optional[str] = None,
                 size: int = 0):
        self.platform: driver.FeatherDriver = platform
        self.filename: str = filename
        self.url: str = url
        self.__data: Any = data_obj
        self.description: Optional[str] = description
        self.spoiler: bool = spoiler
        self.content_type: Optional[str] = content_type
        self.size: int = size

    async def to_file(self) -> File:
        """Converts the attachment to a file object."""
        file_bytes: bytes = await self.platform.to_bytes(self.__data)
        return File(self.platform, self.filename, file_bytes)

