import asyncio
import json
from functools import lru_cache
from pathlib import Path

from bson import SON
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING, IndexModel

from common.jsonlogging.jsonlogger import Logging
from common.managers.alert_attributes.alert_attribute_model import AlertAttributeDb
from common.managers.base.base_manager import Manager
from common.models.mongo import DbException

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AttributeManagerException(Exception):
    pass


class AlertAttributeManager:
    def __init__(self) -> None:
        self._storage_collection: AgnosticCollection | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "AlertAttributeManager":
        return AlertAttributeManager()

    @tracer.start_as_current_span("get_attribute_async")
    async def get_attribute_async(self, id: str) -> AlertAttributeDb | None:
        document = await self.manager.find_one(id)
        return document if document else None

    @tracer.start_as_current_span("get_attributes_async")
    async def get_attributes_async(self) -> list[AlertAttributeDb]:
        return await self.manager.find_many({})

    @tracer.start_as_current_span("delete_attribute_async")
    async def delete_attribute_async(self, object_id: str) -> str:
        return await self.manager.delete_one(object_id)

    @tracer.start_as_current_span("create_attribute_async")
    async def create_attribute_async(self, attribute: AlertAttributeDb) -> str:
        return await self.manager.insert_one(attribute)

    @tracer.start_as_current_span("update_attribute_async")
    async def update_attribute_async(self, attribute: AlertAttributeDb) -> str:
        return await self.manager.update_one(attribute)

    @tracer.start_as_current_span("atm_initialize")
    async def initialize(self, storage_collection: AgnosticCollection):
        if self._storage_collection is not None:
            logger().warning("Initialized previously - calling initialize multiple times has no effect")
            return

        self._storage_collection = storage_collection
        self.manager = Manager[AlertAttributeDb](self._storage_collection, AlertAttributeDb)
        attribute_name_field = "attribute_name"
        attribute_name_index = IndexModel([(attribute_name_field, ASCENDING)], unique=True)
        indexes = self._storage_collection.list_indexes()
        is_first_initialization = True

        async for index in indexes:  # type: ignore[attr-defined]
            # SON is an ordered dictionary. All standard dictionary methods work
            # https://pymongo.readthedocs.io/en/stable/api/bson/son.html
            index_key: SON = index.get("key")
            if index_key is not None and index_key.get(attribute_name_field) == ASCENDING:
                is_first_initialization = False
                logger().info(
                    f"{attribute_name_field} index created previously. Skipping initialization of default attributes",
                )
                break

        if not is_first_initialization:
            return
        output = await self._storage_collection.create_indexes(
            [attribute_name_index]  # type: ignore[arg-type]
        )
        logger().info(
            "Created indexes for alert attribute collection: %s",
            output,
        )

        for attr in self.default_attributes:
            try:
                await self.create_attribute_async(AlertAttributeDb(**attr))
            except DbException as e:
                logger().error(f"Default alert attribute {attr} already exists", e)

    def load_initial_data(self, path: Path):
        if not path.exists() or not path.is_dir():
            logger().error(f'Default path "{path}" does not exist or is not a directory')
            raise AttributeManagerException(f'Default "{path}" does not exist')

        self.default_attributes = []
        for file in path.glob("*.json"):
            with open(file) as f:
                self.default_attributes = json.load(f)

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
