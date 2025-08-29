
import json
from typing import Any
from redis.asyncio.client import Redis

from common.models.connector_id_enum import ConnectorIdEnum

KEY_PREFIX = "connector_"

class Cache:
    _cache: Redis | None

    def __init__(self, cache: Redis | None):
        self._cache = cache

    def _get_key(self, connector: ConnectorIdEnum, key: str) -> str:
        return f"{KEY_PREFIX}_{connector}_{key}"

    async def set(self, connector: ConnectorIdEnum, key: str, data: Any, expiry_sec: int) -> None:
        if not self._cache:
            return

        json_data = json.dumps(data)
        await self._cache.set(name=self._get_key(connector=connector, key=key), value=json_data, ex=expiry_sec)

    async def get(self, connector: ConnectorIdEnum, key: str) -> None | Any:
        if not self._cache:
            return None

        raw_data = await self._cache.get(name=self._get_key(connector=connector, key=key))
        if raw_data is None:
            return None

        return json.loads(raw_data)
