from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection


class CollectionManager(ABC):
    @classmethod
    @abstractmethod
    @lru_cache(maxsize=1)
    def instance(cls):
        pass

    @abstractmethod
    async def initialize(
        self, storage_collection: Optional[AgnosticCollection] = None
    ) -> None:
        pass
