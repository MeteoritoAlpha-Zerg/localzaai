import asyncio
from typing import Callable, Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo.errors import PyMongoError


class MongoDbConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONGODB_")
    url: str = "mongodb://localhost:27017/"
    timeout_in_ms: int = 5000


class MongoDbClientException(PyMongoError):
    def __init__(self, message: str):
        super().__init__(message)


class MongoDbClient:
    _client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def initialize(cls, cfg: MongoDbConfig) -> None:
        # Client configuration: https://pymongo.readthedocs.io/en/4.9.2/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
        cls._client = AsyncIOMotorClient(host=[cfg.url], timeoutMS=cfg.timeout_in_ms)
        # Fix motor using wrong event loop (https://github.com/fastapi/fastapi/issues/3855)
        cls._client.get_io_loop = asyncio.get_running_loop  # type: ignore[attr-defined]

    @classmethod
    def close(cls) -> None:
        if cls._client is not None:
            cls._client.close()
            cls._client = None

    @classmethod
    def get_db(cls, db_name: str) -> AsyncIOMotorDatabase:
        if cls._client is None:
            raise MongoDbClientException("MongoDB client not initialized")

        return cls._client.get_database(db_name)

    @classmethod
    def db_getter(cls, db_name: str) -> Callable[[], AsyncIOMotorDatabase]:
        def _db_getter():
            return cls.get_db(db_name)

        return _db_getter

    @classmethod
    def get_collection(
        cls, db_name: str, collection_name: str
    ) -> AsyncIOMotorCollection:
        if cls._client is None:
            raise MongoDbClientException("MongoDB client not initialized")
        db = cls.get_db(db_name)
        return db.get_collection(collection_name)  # type: ignore[return-value]

    @classmethod
    def collection_getter(
        cls, db_name: str, collection_name: str
    ) -> Callable[[], AsyncIOMotorCollection]:
        def _collection_getter():
            return cls.get_collection(db_name, collection_name)

        return _collection_getter
