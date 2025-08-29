from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from datetime import datetime
from typing import Any, Optional
from pymongo import errors

from opentelemetry import trace

from common.jsonlogging.jsonlogger import Logging
from common.managers.alert_groups.alert_group_model import (
    AlertGroup,
    AlertGroupStatus,
    AlertGroupDeleteResult,
)


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AlertGroupException(Exception):
    pass


class AlertGroupDuplicateKeyException(Exception):
    pass


class AlertGroupManager:
    def __init__(self) -> None:
        self._storage_collection: Optional[AgnosticCollection] = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "AlertGroupManager":
        return AlertGroupManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_alert_group_async")
    async def get_alert_group_async(self, id: str) -> Optional[AlertGroup]:
        if self._storage_collection is None:
            raise AlertGroupException(
                "Unable to get alert group because no storage collection was initialized."
            )
        alert_group_doc = await self._storage_collection.find_one({"_id": id})  # type: ignore[func-returns-value]
        if alert_group_doc is None:
            return None
        return AlertGroup.from_mongo(alert_group_doc)

    @tracer.start_as_current_span("delete_alert_groups_async")
    async def delete_alert_groups_async(
        self, alert_group_ids: list[str]
    ) -> AlertGroupDeleteResult:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to delete alert groups {alert_group_ids} - no storage collection was initialized."
            )
        if len(alert_group_ids) == 0:
            logger().debug("No alert groups to delete")
            return AlertGroupDeleteResult(deleted_count=0, total_count=0)

        result = await self._storage_collection.delete_many(
            {"_id": {"$in": alert_group_ids}}
        )
        if not result.acknowledged:
            raise AlertGroupException("MongoDB did not acknowledge delete request")
        logger().debug(
            "Deleted %d alert groups %s'", result.deleted_count, alert_group_ids
        )
        return AlertGroupDeleteResult(
            deleted_count=result.deleted_count, total_count=len(alert_group_ids)
        )

    @tracer.start_as_current_span("update_alert_group_status")
    async def update_alert_group_status(
        self, id: str, status: AlertGroupStatus
    ) -> AlertGroup:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to update alert group status for {id} - no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {"_id": id}, {"$set": {"status": status}}, return_document=True
            )  # type: ignore[var-annotated]
            updated_alert_group = AlertGroup.from_mongo(updated_mongo_document)
            if updated_alert_group is None:
                raise AlertGroupException(
                    f"Document returned from Mongo is not valid {id}"
                )

            logger().debug("Alert group with and id '%s' was updated", id)
            return updated_alert_group
        except Exception as e:
            logger().exception(f"An error occurred while setting alert group id {id}")
            raise e

    @tracer.start_as_current_span("get_alert_groups_async")
    async def get_alert_groups_async(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> list[AlertGroup]:
        if self._storage_collection is None:
            raise AlertGroupException(
                "Unable to get alert groups - no storage collection was initialized."
            )

        pipeline: list[dict[str, Any]] = []
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})
        if before:
            pipeline.append({"$match": {"time": {"$lt": before}}})
        if after:
            pipeline.append({"$match": {"time": {"$gte": after}}})

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
    async def upsert_alert_group_async(self, alert: AlertGroup) -> AlertGroup:
        if self._storage_collection is None:
            raise AlertGroupException(
                f"Unable to upsert alert group with {alert.id} because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "_id": alert.id,
                },
                {"$set": alert.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_alert = AlertGroup.from_mongo(updated_mongo_document)
            if updated_alert is None:
                raise AlertGroupException(
                    f"Document returned from Mongo is not valid {alert.id}"
                )

            logger().debug("Alert group with and id '%s' was updated", alert.id)
            return updated_alert
        except Exception as e:
            logger().exception(
                f"An error occurred while setting alert group id {alert.id}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
        if self._storage_collection is not None:
            logger().warning(
                "AlertGroupManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "AlertGroupManager initialized without a storage collection - alert groups"
            )
            return

        # migration for post-April 1, 2025
        try:
            await self._storage_collection.drop_index("alert_ids_1")
        except errors.OperationFailure:
            logger().debug("'alert_ids_1' index has already been dropped")
