from typing import Optional, Self
from pydantic import model_validator
from pydantic_settings import BaseSettings
from redis import Redis as SyncRedis
from redis.asyncio import RedisError, Redis as AsyncRedis


class RedisConfig(BaseSettings):
    host: str = "redis"
    port: int = 6379
    tls: bool = True

    @property
    def redis_url(self):
        protocol = "rediss" if self.tls else "redis"
        return f"{protocol}://{self.host}:{self.port}"

    @model_validator(mode="after")
    def validate_connection_string(self) -> Self:
        if not self.host or not self.port:
            raise ValueError(
                f"Cannot form a valid connection string from {self.host} and {self.port}"
            )
        return self


class RedisClientException(RedisError):
    def __init__(self, message: str):
        super().__init__(message)


class RedisClient:
    _client: Optional[AsyncRedis] = None
    _sync_client: Optional[SyncRedis] = None

    @classmethod
    async def initialize(cls, cfg: RedisConfig) -> None:
        cls._client = AsyncRedis.from_url(
            cfg.redis_url, socket_timeout=60, socket_connect_timeout=30
        )
        cls._sync_client = SyncRedis.from_url(
            cfg.redis_url, socket_timeout=60, socket_connect_timeout=30
        )

    @classmethod
    async def close(cls) -> None:
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._sync_client:
            cls._sync_client.close()
            cls._sync_client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            raise RedisClientException("Redis async client not initialized")

        return cls._client

    @classmethod
    def get_sync_client(cls):
        if cls._sync_client is None:
            raise RedisClientException("Redis sync client not initialized")

        return cls._sync_client
