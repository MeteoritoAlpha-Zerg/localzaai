import asyncio
from functools import lru_cache
from typing import Optional, Any, Set
from pathlib import Path
import json
from common.jsonlogging.jsonlogger import Logging

from common.base.collection_manager import CollectionManager
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from common.models.mitre import (
    MitreEnterpriseTechnique,
    MitreEnterpriseTechniquePage,
    MitreEnterpriseTechniqueUpdate,
)

logger = Logging.get_logger(__name__)


class EnterpriseTechniqueManagerException(Exception):
    pass


class EnterpriseTechniqueManagerConfig(BaseSettings):
    mongodb_database: str = "metamorph"


class MitreTechniquePriority(BaseModel):
    id: str
    priority: float


class MitreTechniquePriorities:
    mapping: dict[str, float] = {}

    def __init__(self, techniques: list[MitreTechniquePriority]) -> None:
        for technique in techniques:
            self.mapping[technique.id] = technique.priority

    def get(self, technique_id: str, default_priority: float) -> MitreTechniquePriority:
        technique_priority = self.mapping.get(technique_id, default_priority)
        return MitreTechniquePriority(id=technique_id, priority=technique_priority)


class EnterpriseTechniqueManager(CollectionManager):
    def __init__(self):
        self._collection: Optional[AgnosticCollection] = None
        self._loaded_paths: Set[str] = set()
        self._initial_mitre_values: list = []

    # TODO: remove this when a better solution is created for PR deployments
    async def load_initial_techniques_async(self, path: Path, reload: bool = False):
        if not path.exists() or not path.is_dir():
            logger().error(
                f'Default technique path "{path}" does not exist or is not a directory'
            )
            raise EnterpriseTechniqueManagerException(
                f'Default technique path "{path}" does not exist'
            )

        if not reload and str(path) in self._loaded_paths:
            logger().info(
                f"Path '{path}' already loaded and reload is False. Skipping load."
            )
            return

        for file in path.glob("*.json"):
            try:
                with open(file, "r") as f:
                    techniques = json.load(f)
                    for technique in techniques:
                        self._initial_mitre_values.append(technique)
            except Exception as e:
                logger().error(f"Unexpected error: {str(e)}")
                continue

        self._loaded_paths.add(str(path))

    def load_initial_techniques(self, path: Path, reload: bool = False):
        """
        Synchronously loads default enterprise techniques from the given path. The function will look for all json files in the path
        (non recursively), and attempt to load a Prompt model for each file. The next call to `initialize` will perform
        the synchronization.

        :param path: The path on disk where enterprise techniques are present with JSON extensions.
        :param reload: Whether to reload from the path even if it has been loaded before. Default is False.
        :return: None
        """
        return self._get_event_loop().run_until_complete(
            self.load_initial_techniques_async(path, reload)
        )

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "EnterpriseTechniqueManager":
        return EnterpriseTechniqueManager()  # type: ignore[call-arg]

    def check_client_initialization(function: Any):
        def check_client(self, *args, **kwargs):
            if self._collection is None:
                raise ValueError("MongoDb client is not initialized.")
            return function(self, *args, **kwargs)

        return check_client

    async def initialize(
        self, storage_collection: Optional[AgnosticCollection] = None, data=None
    ):
        if self._collection is None:
            self._collection = storage_collection
        await self._collection.create_index([("tid", 1)], unique=True)  # type: ignore
        await self._collection.create_index([("priority", 1)])  # type: ignore
        await self.load_initial_tactics()

    @check_client_initialization
    async def get_technique(self, id: str) -> MitreEnterpriseTechnique | None:
        doc = await self._collection.find_one({"tid": id})  # type: ignore
        if doc is None:
            return None
        return MitreEnterpriseTechnique.from_mongo(doc)

    @check_client_initialization
    async def list_techniques(
        self, page: int, page_size: int
    ) -> MitreEnterpriseTechniquePage:
        skip = (page - 1) * page_size
        cursor = self._collection.find().skip(skip).limit(page_size)  # type: ignore
        docs = await cursor.to_list()
        doc_count = await self._collection.count_documents({})  # type: ignore

        return MitreEnterpriseTechniquePage(
            page=page, page_size=page_size, total_count=doc_count, results=docs
        )

    @check_client_initialization
    async def get_highest_technique_priority(
        self, mitre_technique_ids: list[str]
    ) -> float | None:
        """
        For a given list of techniques, return the highest priority

        NOTE: The "highest priority technique" actually has the lowest numerical priority. Priority 0 is higher priority than Priority 10

        Returns None if no technique priorities are available
        """
        result = await self._collection.aggregate(  # type: ignore
            [
                {"$match": {"tid": {"$in": mitre_technique_ids}}},
                {"$project": {"highest_priority": {"$min": "$priority"}}},
            ]
        ).to_list(length=1)  # type: ignore

        priority = None
        if len(result) > 0:
            priority = result[0].get("highest_priority")

        return float(priority) if priority is not None else None

    @check_client_initialization
    async def get_technique_priorities(
        self, page_size: Optional[int] = None
    ) -> MitreTechniquePriorities:
        cursor = self._collection.find(  # type: ignore
            projection={"tid": True, "priority": True, "_id": False}
        )
        if page_size is not None:
            cursor.limit(page_size)
        techniques: list[MitreTechniquePriority] = []
        async for document in cursor:
            techniques.append(
                MitreTechniquePriority(
                    id=document["tid"], priority=document["priority"]
                )
            )
        return MitreTechniquePriorities(techniques=techniques)

    @check_client_initialization
    async def create_technique(self, doc: MitreEnterpriseTechnique) -> Optional[dict]:
        result = await self._collection.insert_one(doc.to_mongo())  # type: ignore
        if not result.acknowledged:
            return None

        return {"tid": doc.tid, "status": "created"}

    @check_client_initialization
    async def update_technique(
        self, technique_id: str, doc: MitreEnterpriseTechnique
    ) -> str:
        technique = await self._collection.find_one_and_update(  # type: ignore
            {"tid": technique_id},
            {"$set": doc.to_mongo()},
            return_document=True,
        )
        return technique

    @check_client_initialization
    async def update_technique_batch(
        self, techniques: list[MitreEnterpriseTechnique]
    ) -> MitreEnterpriseTechniqueUpdate:
        update_ops = [
            UpdateOne(
                filter={"tid": technique.tid},
                update={"$set": technique.to_mongo()},
                upsert=True,
            )
            for technique in techniques
        ]
        result = await self._collection.bulk_write(update_ops)  # type: ignore
        return MitreEnterpriseTechniqueUpdate(
            message="Successfully updated documents.",
            matched_count=result.matched_count,
            modified_count=result.modified_count + result.upserted_count,
        )

    async def load_initial_tactics(self) -> None:
        if self._collection is None:
            logger().debug("MongoDB collection not initialized")
            return
        if len(self._initial_mitre_values) == 0:
            logger().debug("No initial tactics to load")
            return
        try:
            await self._collection.insert_many(self._initial_mitre_values)
        except BulkWriteError:
            logger().info("Mitre Enterprise tactics already loaded")

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
