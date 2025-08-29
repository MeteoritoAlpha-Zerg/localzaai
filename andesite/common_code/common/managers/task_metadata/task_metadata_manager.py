from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING, DESCENDING

from common.jsonlogging.jsonlogger import Logging
from common.managers.task_metadata.task_metadata_model import (
    TaskMetadata,
    TaskStatusEnum,
)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class TaskMetadataException(Exception):
    """Base class for exceptions in this module."""

    pass


class TaskMetadataManager:
    def __init__(
        self,
    ):
        """
        Initializes the TaskMetadataManager.

        :return: None
        """
        self._storage_collection: AgnosticCollection | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "TaskMetadataManager":
        """
        Get a global singleton of the TaskMetadataManager in a threadsafe manner.
        :return: The app-wide TaskMetadataManager singleton.
        """
        return TaskMetadataManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_task_metadata_async")
    async def get_task_metadata_async(
        self,
        task_id: str,
    ) -> TaskMetadata | None:
        """
        Asynchronously retrieves task metadata from the database or cache.

        :param task_id: The task's task_id.
        :return: The retrieved task metadata.
        :raises TaskMetadataException: If the task metadata is not found.
        """
        if self._storage_collection is None:
            raise TaskMetadataException("Unable to get task metadata because no storage collection was initialized.")
        task_metadata = await self._storage_collection.find_one(
            {
                "task_id": task_id,
            }
        )  # type: ignore[func-returns-value]

        if task_metadata is None:
            return None

        logger().info(
            "Retrieved task metadata with id '%s'",
            task_id,
        )

        return TaskMetadata.from_mongo(task_metadata)

    @tracer.start_as_current_span("delete_task_metadatas_async")
    async def delete_task_metadatas_async(self, task_ids: list[str]):
        """
        Asynchronously deletes the content of a task metadata in the database.

        :param task_ids: a list of task ids to delete.
        :raises TaskMetadataException: If there is an error deleting from the task metadata.
        """
        if self._storage_collection is None:
            raise TaskMetadataException(
                f"Unable to delete task metadata with ids {task_ids} because no storage collection was initialized."
            )

        delete_result = await self._storage_collection.delete_many({"task_id": {"$in": task_ids}})

        logger().info(
            "Deleted %d task metadatas with ids '%s'",
            delete_result.deleted_count,
            task_ids,
        )

    @tracer.start_as_current_span("get_task_metadatas_async")
    async def get_task_metadatas_async(
        self,
        task_name: str | None = None,
        matching_statuses: list[TaskStatusEnum] | None = None,
        args: dict[str, Any] | None = None,
        incomplete_match_args: bool = True,
        before: datetime | None = None,
        after: datetime | None = None,
        limit: int | None = None,
    ) -> list[TaskMetadata]:
        """
        Asynchronously gets the content of task metadatas for a particular task in the database.
        Returns sorted by start_time with most recent first.

        :param task_name: The task's name.
        :raises TaskMetadataException: If there is an error deleting from the task metadata.
        """
        if self._storage_collection is None:
            raise TaskMetadataException(
                f"Unable to get task metadatas with name {task_name} because no storage collection was initialized."
            )

        pipeline: list[dict[str, Any]] = [
            {"$sort": {"end_time": DESCENDING, "start_time": DESCENDING}},
        ]
        if task_name:
            pipeline.append({"$match": {"task_name": task_name}})
        if matching_statuses:
            pipeline.append({"$match": {"status": {"$in": matching_statuses}}})
        if args:
            if not incomplete_match_args:
                pipeline.append({"$match": {"args": args}})
            else:
                or_clauses = [{"args." + key: value} for key, value in args.items()]
                pipeline.append({"$match": {"$and": or_clauses}})
        if before:
            pipeline.append({"$match": {"start_time": {"$lt": before}}})
        if after:
            pipeline.append({"$match": {"start_time": {"$gte": after}}})
        if limit:
            pipeline.append({"$limit": limit})

        metadata_documents = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None,
        )
        if not metadata_documents:
            return []

        task_metadatas = []
        for doc in metadata_documents:
            task_metadata_response = TaskMetadata.from_mongo(doc)
            if task_metadata_response:
                task_metadatas.append(task_metadata_response)

        return task_metadatas

    @tracer.start_as_current_span("end_task_metadata_async")
    async def end_task_metadata_async(self, task_id: str, status: TaskStatusEnum) -> TaskMetadata | None:
        """
        Asynchronously ends a task that is in the database

        :param task_id: The task's task_id.
        :param status: The status to set the task to.
        :return: The updated task metadata.
        :raises TaskMetadataException: If there is an error setting the task metadata.
        """
        if self._storage_collection is None:
            raise TaskMetadataException(
                f"Unable to set task metadata with id '{task_id}' because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.find_one_and_update(  # type: ignore
                {"task_id": task_id},
                {
                    "$set": {
                        "end_time": datetime.now(UTC),
                        "status": status,
                    }
                },
                return_document=True,
            )
            completed_task = TaskMetadata.from_mongo(result)
        except Exception as e:
            raise TaskMetadataException(f"Unable to end task with task_id '{task_id}'") from e

        if completed_task is None:
            # occurs when the task metadata doesn't exist or is already reset
            logger().info("Document with task_id '%s' was already ended or never existed", task_id)

        return completed_task

    @tracer.start_as_current_span("upsert_task_metadata_async")
    async def upsert_task_metadata_async(self, task_metadata: TaskMetadata) -> TaskMetadata:
        """
        Asynchronously sets the content of a task metadata in the database. You can
        update task metadatas and introduce new tasks using this method.

        :param task_metadata: The task metadata.
        :return: The updated task metadata.
        :raises TaskMetadataException: If there is an error setting the task metadata.
        """
        if self._storage_collection is None:
            raise TaskMetadataException(
                f"Unable to set task metadata with id '{task_metadata.task_id}' because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "task_id": task_metadata.task_id,
                },
                {"$set": task_metadata.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_task_metadata = TaskMetadata.from_mongo(updated_mongo_document)
            if updated_task_metadata is None:
                raise TaskMetadataException(f"Unable to update document with id '{task_metadata.task_id}'")

            logger().info(
                "Task metadata with with id '%s' was updated",
                task_metadata.task_id,
            )
            return updated_task_metadata
        except Exception as e:
            logger().error(f"An error occurred while setting task metadata with id '{task_metadata.task_id}': {e}")
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection | None = None):
        """
        Initializes the TaskMetadataManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "TaskMetadataManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "TaskMetadataManager initialized without a storage collection - task metadatas will not be persisted"
            )
            return
        await self._storage_collection.create_index(
            [("task_id", ASCENDING)],
            unique=True,
        )
