from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import errors

from common.jsonlogging.jsonlogger import Logging
from common.managers.alert_groups.alert_group_model import (
    AlertGroup,
    AlertGroupDeleteResult,
    AlertGroupStatus,
)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AlertGroupException(Exception):
    pass


class AlertGroupDuplicateKeyException(Exception):
    pass


class AlertGroupManager:
    def __init__(self) -> None:
        self._storage_collection: AgnosticCollection | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "AlertGroupManager":
        return AlertGroupManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_alert_group_async")
    async def get_alert_group_async(self, id: str) -> AlertGroup | None:
        if self._storage_collection is None:
            raise AlertGroupException("Unable to get alert group because no storage collection was initialized.")
        alert_group_doc = await self._storage_collection.find_one(
            {
                "_id": id,
                "archived_at": None,
            }
        )  # type: ignore[func-returns-value]
        if alert_group_doc is None:
            return None
        return AlertGroup.from_mongo(alert_group_doc)

    @tracer.start_as_current_span("delete_alert_groups_async")
    async def delete_alert_groups_async(self, alert_group_ids: list[str]) -> AlertGroupDeleteResult:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to delete alert groups {alert_group_ids} - no storage collection was initialized."
            )
        if len(alert_group_ids) == 0:
            logger().debug("No alert groups to delete")
            return AlertGroupDeleteResult(deleted_count=0, total_count=0)

        result = await self._storage_collection.update_many(
            {"_id": {"$in": alert_group_ids}, "archived_at": None},
            {"$set": {"archived_at": datetime.now(UTC)}},
        )
        if not result.acknowledged:
            raise AlertGroupException("MongoDB did not acknowledge delete request")
        logger().debug("Deleted %d alert groups %s'", result.matched_count, alert_group_ids)
        return AlertGroupDeleteResult(deleted_count=result.matched_count, total_count=len(alert_group_ids))

    @tracer.start_as_current_span("archive_all_alert_groups_async")
    async def archive_all_alert_groups_async(self) -> AlertGroupDeleteResult:
        if self._storage_collection is None:
            raise AlertGroupException("Unable to archive all alert groups - no storage collection was initialized.")
        try:
            result = await self._storage_collection.update_many(
                {"archived_at": None},
                {"$set": {"archived_at": datetime.now(UTC)}},
            )
        except Exception as err:
            raise AlertGroupException("Unable to archive all alert groups") from err

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already archived
            logger().info("No alert groups are available to archive")
            return AlertGroupDeleteResult(deleted_count=0, total_count=0)

        logger().debug("Archived %d alert groups", result.matched_count)
        return AlertGroupDeleteResult(deleted_count=result.matched_count, total_count=result.matched_count)

    @tracer.start_as_current_span("update_alert_group_status")
    async def update_alert_group_status(self, id: str, status: AlertGroupStatus) -> AlertGroup:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to update alert group status for {id} - no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {"_id": id, "archived_at": None},
                {"$set": {"status": status}},
                return_document=True,
            )  # type: ignore[var-annotated]
            updated_alert_group = AlertGroup.from_mongo(updated_mongo_document)
            if updated_alert_group is None:
                raise AlertGroupException(f"Document returned from Mongo is not valid {id}")

            logger().debug("Alert group with id '%s' was updated", id)
            return updated_alert_group
        except Exception as e:
            logger().exception(f"An error occurred while setting alert group id {id}")
            raise e

    @tracer.start_as_current_span("get_alert_groups_async")
    async def get_alert_groups_async(
        self,
        skip: int | None = None,
        limit: int | None = None,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[AlertGroup]:
        if self._storage_collection is None:
            raise AlertGroupException("Unable to get alert groups - no storage collection was initialized.")

        pipeline: list[dict[str, Any]] = [{"$match": {"archived_at": None}}]
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})
        if before:
            pipeline.append({"$match": {"time_alerts_last_modified": {"$lt": before}}})
        if after:
            pipeline.append({"$match": {"time_alerts_last_modified": {"$gte": after}}})

        documents = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None
        )
        if not documents:
            return []

        alert_groups = []
        for doc in documents:
            response = AlertGroup.from_mongo(doc)
            if response:
                alert_groups.append(response)

        return alert_groups

    @tracer.start_as_current_span("upsert_alert_group_async")
    async def upsert_alert_group_async(self, alert_group: AlertGroup) -> AlertGroup:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to upsert alert group with {alert_group.id} because no storage collection was initialized."
            )
        try:
            alert_group.time_alerts_last_modified = datetime.now(UTC)
            if alert_group.group_migrated_to is not None:
                alert_group.status = AlertGroupStatus.MIGRATED
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "_id": alert_group.id,
                    "archived_at": None,
                },
                {"$set": alert_group.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_alert = AlertGroup.from_mongo(updated_mongo_document)
            if updated_alert is None:
                raise AlertGroupException(f"Document returned from Mongo is not valid {alert_group.id}")

            logger().debug("Alert group with and id '%s' was updated", alert_group.id)
            return updated_alert
        except Exception as e:
            logger().exception(f"An error occurred while setting alert group id {alert_group.id}")
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection | None = None):
        if self._storage_collection is not None:
            logger().warning(
                "AlertGroupManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning("AlertGroupManager initialized without a storage collection - alert groups")
            return

        # migration for post-April 1, 2025
        try:
            await self._storage_collection.drop_index("alert_ids_1")
        except errors.OperationFailure:
            logger().debug("'alert_ids_1' index has already been dropped")

    # Supports schema as of April 9, 2025
    async def migrate(self):
        if self._storage_collection is None:
            raise AlertGroupException("Unable to get alert groups because no storage collection was initialized.")

        groups_from_storage = self._storage_collection.find(
            {
                "summary": {"$exists": False},
                "archived_at": None,
            }
        )
        async for d in groups_from_storage:
            description = d.get("description")
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {
                        "summary": description,
                    },
                },
            )
            logger().debug(f"Updated alert group {d['_id']} with summary {description}")
        logger().info("Alert Groups Migration Complete")
