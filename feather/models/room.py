import asyncio
import aiomultiprocess
from typing import Optional

class RoomSettings:
    def __init__(self, name, description, items):
        self.name = name
        self.description = description
        self.items = items

class Room:
    def __init__(self, name, description, platforms: Optional[dict] = None):
        self.name = name
        self.description = description
        self.platforms = platforms or {}

    async def platform_send(self, platform: str, content: str, data: dict):
        pass

    async def send(self, content: str, data: dict):
        threads = []
        for platform in self.platforms.keys():
            task = asyncio.create_task(self.platform_send(platform, content, data))
            threads.append(task)

        return await asyncio.gather(*threads)
