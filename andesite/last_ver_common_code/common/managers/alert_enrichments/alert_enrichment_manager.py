from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from datetime import datetime
from typing import Any, Optional

from pymongo import ASCENDING
from opentelemetry import trace

from connectors.connector_id_enum import ConnectorIdEnum

from common.jsonlogging.jsonlogger import Logging
from common.managers.alert_enrichments.alert_enrichment_model import (
    AlertEnrichment,
    AlertEnrichmentId,
)


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AlertEnrichmentException(Exception):
    """Base class for exceptions in this module."""

    pass


class AlertEnrichmentManager:
    def __init__(
        self,
    ):
        """
        Initializes the AlertEnrichmentManager.

        :return: None
        """
        self._storage_collection: Optional[AgnosticCollection] = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "AlertEnrichmentManager":
        """
        Get a global singleton of the AlertEnrichmentManager in a threadsafe manner.
        :return: The app-wide AlertEnrichmentManager singleton.
        """
        return AlertEnrichmentManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_alert_enrichment_async")
    async def get_alert_enrichment_async(
        self,
        connector: ConnectorIdEnum,
        id: str,
    ) -> Optional[AlertEnrichment]:
        """
        Asynchronously retrieves alert enrichment from the database or cache.

        :param rule_name: The rule's name.
        :return: The retrieved alert enrichment.
        :raises AlertEnrichmentException: If the alert enrichment is not found.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichment because no storage collection was initialized."
            )
        alert_enrichment_doc = await self._storage_collection.find_one(
            {
                "id": id,
                "connector": connector.value,
            }
        )  # type: ignore[func-returns-value]

        if alert_enrichment_doc is None:
            return None

        logger().info(
            "Retrieved alert enrichment with connector '%s' and id '%s'",
            connector,
            id,
        )

        return AlertEnrichment.from_mongo(alert_enrichment_doc)

    @tracer.start_as_current_span("delete_alert_enrichments_async")
    async def delete_alert_enrichments_async(self, alerts: list[AlertEnrichmentId]):
        """
        Asynchronously deletes the content of a alert enrichment in the database.

        :param alerts: a list of alerts to delete.
        :raises AlertEnrichmentException: If there is an error deleting from the alert enrichment.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                f"Unable to delete alert enrichments {alerts} because no storage collection was initialized."
            )
        if len(alerts) == 0:
            logger().debug("No alert enrichments to delete")
            return

        delete_result = await self._storage_collection.delete_many(
            {
                "$or": [
                    {"connector": alert.connector.value, "id": alert.id}
                    for alert in alerts
                ]
            }
        )
        logger().debug(
            "Deleted %d alert enrichments %s'", delete_result.deleted_count, alerts
        )

    @tracer.start_as_current_span("get_alert_enrichments_async")
    async def get_alert_enrichments_async(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> list[AlertEnrichment]:
        """
        Asynchronously gets the content of alert enrichments.

        :raises AlertEnrichmentException: If there is an error getting from the alert enrichment.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichments because no storage collection was initialized."
            )

        pipeline: list[dict[str, Any]] = []
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})
        if before:
            pipeline.append({"$match": {"time_created": {"$lt": before}}})
        if after:
            pipeline.append({"$match": {"time_created": {"$gte": after}}})

        alert_documents = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None
        )
        if not alert_documents:
            return []

        alert_enrichments = []
        for doc in alert_documents:
            alert_enrichment_response = AlertEnrichment.from_mongo(doc)
            if alert_enrichment_response:
                alert_enrichments.append(alert_enrichment_response)

        return alert_enrichments

    @tracer.start_as_current_span("upsert_alert_enrichment_async")
    async def upsert_alert_enrichment_async(
        self, alert: AlertEnrichment
    ) -> AlertEnrichment:
        """
        Asynchronously sets the content of a alert enrichment in the database. You can
        update alert enrichments and introduce new alert enrichments using this method.

        :param alert: The alert enrichment.
        :return: The updated alert enrichment.
        :raises AlertEnrichmentException: If there is an error setting the alert enrichment.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                f"Unable to set alert enrichment with connector {alert.connector} and id {alert.id} because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "id": alert.id,
                    "connector": alert.connector.value,
                },
                {"$set": alert.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_alert = AlertEnrichment.from_mongo(updated_mongo_document)
            if updated_alert is None:
                raise AlertEnrichmentException(
                    f"Unable to update document with with connector {alert.connector} and id {alert.id}"
                )

            logger().info(
                "Alert enrichment with with connector '%s' and id '%s' was updated",
                alert.connector,
                alert.id,
            )
            return updated_alert
        except Exception as e:
            logger().exception(
                f"An error occurred while setting alert enrichment with connector {alert.connector} and id {alert.id}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
        """
        Initializes the AlertEnrichmentManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "AlertEnrichmentManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "AlertEnrichmentManager initialized without a storage collection - alert enrichments will not be persisted"
            )
            return
        await self._storage_collection.create_index(
            [("connector", ASCENDING), ("id", ASCENDING)],
            unique=True,
        )
