import datetime
from functools import lru_cache
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING

from common.jsonlogging.jsonlogger import Logging
from common.managers.investigations.investigation_model import (
    AbbreviatedInvestigation,
    Investigation,
)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class InvestigationException(Exception):
    """Base class for exceptions in this module."""

    pass


class InvestigationManager:
    def __init__(self) -> None:
        self._storage_collection: AgnosticCollection | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "InvestigationManager":
        return InvestigationManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection) -> None:
        if self._storage_collection is not None:
            logger().warning(
                "InvestigationManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "InvestigationManager initialized without a storage collection - investigations will not be persisted"
            )
            return
        await self._storage_collection.create_index([("id", ASCENDING)])

    @tracer.start_as_current_span("get_investigation_async")
    async def get_investigation_async(self, id: str, user_id: str) -> Investigation | None:
        if self._storage_collection is None:
            raise InvestigationException("Unable to get investigation because no storage collection was initialized.")

        investigation = await self._storage_collection.find_one({"_id": id, "user_id": user_id, "archived_at": None})  # type: ignore[func-returns-value]

        if investigation is None:
            return None

        logger().info("Retrieved investigation with id '%s'", id)
        return Investigation.from_mongo(investigation)

    @tracer.start_as_current_span("get_all_investigations_async")
    async def get_all_abbreviated_investigations_async(
        self, user_id: str, skip: int | None = None, limit: int | None = None
    ) -> list[AbbreviatedInvestigation]:
        if self._storage_collection is None:
            raise InvestigationException("Unable to get investigations because no storage collection was initialized.")

        pipeline: list[dict[str, Any]] = [{"$match": {"user_id": user_id, "archived_at": None}}]
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})

        investigations_in_mongo = await self._storage_collection.aggregate(pipeline).to_list(length=None)  # type: ignore
        logger().info("Retrieved %s investigations", len(investigations_in_mongo))

        investigations: list[AbbreviatedInvestigation] = []
        for investigation in investigations_in_mongo:
            investigation_response = Investigation.from_mongo(investigation)
            if investigation_response:
                abbreviated_investigation = investigation_response.get_abbreviated()
                investigations.append(abbreviated_investigation)
        investigations.sort(key=lambda investigation: investigation.creation_time, reverse=True)
        return investigations

    @tracer.start_as_current_span("archive_investigation_async")
    async def archive_investigation_async(self, id: str, user_id: str) -> bool:
        if self._storage_collection is None:
            raise InvestigationException(
                f"Unable to archive investigation with id '{id}' because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.update_one(
                {"_id": id, "user_id": user_id, "archived_at": None},
                {"$set": {"archived_at": datetime.datetime.now(datetime.UTC)}},
            )
        except Exception as err:
            raise InvestigationException(f"Unable to archive investigation with id '{id}'") from err

        if result.matched_count == 0 or result.modified_count == 0:
            logger().info("Investigation with id '%s' was already archived or never existed", id)
            return False

        logger().info("Archived investigation with id '%s'", id)
        return True

    @tracer.start_as_current_span("archive_all_investigations_async")
    async def archive_all_investigations_async(self, user_id: str) -> bool:
        if self._storage_collection is None:
            raise InvestigationException(
                "Unable to archive investigations because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.update_many(
                {"user_id": user_id, "archived_at": None},
                {"$set": {"archived_at": datetime.datetime.now(datetime.UTC)}},
            )
        except Exception as err:
            raise InvestigationException("Unable to archive investigations") from err

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already archived
            logger().info("No investigations are available to archive for user '%s'", user_id)
            return False

        logger().info("Archived all investigations for user '%s'", user_id)
        return True

    @tracer.start_as_current_span("upsert_investigation_async")
    async def upsert_investigation_async(self, new_investigation: Investigation) -> Investigation:
        if self._storage_collection is None:
            raise InvestigationException(
                f"Unable to set investigation with id '{new_investigation.id}' because no storage collection was initialized."
            )
        try:
            new_investigation.last_updated = datetime.datetime.now(datetime.UTC)
            updated_investigation = (
                await self._storage_collection.find_one_and_update(
                    {
                        "_id": new_investigation.id,
                        "user_id": new_investigation.user_id,
                        "archived_at": None,
                    },
                    {"$set": new_investigation.to_mongo()},
                    upsert=True,
                    return_document=True,
                )  # type: ignore[var-annotated]
            )

            if updated_investigation is None:
                raise InvestigationException(f"Unable to update investigation with id '{new_investigation.id}'")

            updated_inv = Investigation.from_mongo(updated_investigation)

            if updated_inv is None:
                raise InvestigationException(
                    f"Unable to convert investigation from mongo with id '{new_investigation.id}"
                )

            logger().info(
                "Investigation with id '%s' was updated",
                updated_inv.id,
            )
            return updated_inv
        except Exception as e:
            logger().error(f"An error occurred while setting investigation with id '{new_investigation.id}': {e}")
            raise e
