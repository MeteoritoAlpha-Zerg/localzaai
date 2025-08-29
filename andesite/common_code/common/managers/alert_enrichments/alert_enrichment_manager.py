from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING, errors

from common.jsonlogging.jsonlogger import Logging
from common.managers.alert_enrichments.alert_enrichment_model import (
    AlertEnrichment,
    AlertEnrichmentId,
)
from common.models.connector_id_enum import ConnectorIdEnum

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
        self._storage_collection: AgnosticCollection | None = None

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
        connector: ConnectorIdEnum | None,
        id: str,
    ) -> AlertEnrichment | None:
        """
        Asynchronously retrieves alert enrichment from the database or cache.

        :param connector: The connector of the alert enrichment. If None, indicates an alert group.
        :param id: The id of the alert enrichment.
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
                "connector": connector.value if connector else None,
                "archived_at": None,
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

    @tracer.start_as_current_span("archive_alert_enrichments_async")
    async def archive_alert_enrichments_async(self, alerts: list[AlertEnrichmentId]):
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

        update_result = await self._storage_collection.update_many(
            {
                "$or": [
                    {
                        "connector": alert.connector.value if alert.connector else None,
                        "id": alert.id,
                        "archived_at": None,
                    }
                    for alert in alerts
                ]
            },
            {"$set": {"archived_at": datetime.now(UTC)}},
        )
        logger().debug("Deleted %d alert enrichments %s'", update_result.matched_count, alerts)

    @tracer.start_as_current_span("get_alert_enrichments_async")
    async def get_alert_enrichments_async(
        self,
        enrichment_ids: list[AlertEnrichmentId] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> list[AlertEnrichment]:
        """
        Asynchronously gets the content of alert enrichments.

        :raises AlertEnrichmentException: If there is an error getting from the alert enrichment.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichments because no storage collection was initialized."
            )

        pipeline: list[dict[str, Any]] = [{"$match": {"archived_at": None}}]
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})
        if enrichment_ids:
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {
                                "connector": enrichment.connector.value if enrichment.connector else None,
                                "id": enrichment.id,
                            }
                            for enrichment in enrichment_ids
                        ]
                    }
                }
            )
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
    async def upsert_alert_enrichment_async(self, enrichment: AlertEnrichment) -> AlertEnrichment:
        """
        Asynchronously sets the content of a alert enrichment in the database. You can
        update alert enrichments and introduce new alert enrichments using this method.
        You can provide enrichment.insight or enrichment.anomaly_info to set the
        content of the alert enrichment without overriding the other field.

        :param alert: The alert enrichment.
        :return: The updated alert enrichment.
        :raises AlertEnrichmentException: If there is an error setting the alert enrichment.
        """
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                f"Unable to set alert enrichment with connector {enrichment.connector} and id {enrichment.id} because no storage collection was initialized."
            )
        try:
            update_fields: dict[str, Any] = {
                "connector": enrichment.connector.value if enrichment.connector else None,
                "id": enrichment.id,
            }
            if enrichment.insight:
                update_fields["insight"] = enrichment.insight.model_dump()

            if enrichment.anomaly_info:
                update_fields["anomaly_info"] = enrichment.anomaly_info.model_dump()

            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "id": enrichment.id,
                    "connector": enrichment.connector.value if enrichment.connector else None,
                    "archived_at": None,
                },
                {"$set": update_fields},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_alert = AlertEnrichment.from_mongo(updated_mongo_document)
            if updated_alert is None:
                raise AlertEnrichmentException(
                    f"Unable to update document with with connector {enrichment.connector} and id {enrichment.id}"
                )

            logger().info(
                "Alert enrichment with with connector '%s' and id '%s' was updated",
                enrichment.connector,
                enrichment.id,
            )
            return updated_alert
        except Exception as e:
            logger().exception(
                f"An error occurred while setting alert enrichment with connector {enrichment.connector} and id {enrichment.id}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection | None = None):
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

        # migration for post-April 4, 2025
        try:
            await self._storage_collection.drop_index("connector_1_id_1")
        except errors.OperationFailure:
            logger().debug("'connector_1_id_1' index has already been dropped")

        await self._storage_collection.create_index(
            [("connector", ASCENDING), ("id", ASCENDING), ("archived_at", ASCENDING)],
            unique=True,
        )
        await self._10_04_2025_migrate_enrichment()
        await self._15_04_2025_migrate_enrichment()
        await self._24_04_2025_migrate_enrichment()

    # Supports schema as of April 10, 2025
    async def _10_04_2025_migrate_enrichment(self):
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichments because no storage collection was initialized."
            )

        enrichment_from_storage = self._storage_collection.find(
            {
                "proposed_followups": {"$exists": True},
                "archived_at": None,
            }
        )
        async for d in enrichment_from_storage:
            proposed_followups = d.get("proposed_followups", None)
            if proposed_followups is not None and isinstance(proposed_followups, str):
                proposed_followups = [proposed_followups]
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {
                        "proposed_followups": proposed_followups,
                    },
                },
            )
        logger().info("Alert Enrichment April 10, 2025 Migration Complete")

    async def _15_04_2025_migrate_enrichment(self):
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichments because no storage collection was initialized."
            )

        docs_with_proposed_followups = self._storage_collection.find(
            {
                "proposed_followups": {"$exists": True},
                "archived_at": None,
            }
        )
        async for d in docs_with_proposed_followups:
            proposed_followups: list[str] = d.get("proposed_followups", None)
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {
                        "action_items": [
                            {"proposed_followup": followup, "conversation": None} for followup in proposed_followups
                        ],
                    },
                    "$unset": {
                        "proposed_followups": "",
                    },
                },
            )

        docs_with_display_name = self._storage_collection.find(
            {
                "connector_enrichments.connector_display_name": {"$exists": True},
                "archived_at": None,
            }
        )
        async for d in docs_with_display_name:
            connector_enrichments: list = d.get("connector_enrichments", None)
            new_enrichments = []
            for enrichment in connector_enrichments:
                if "connector_display_name" in enrichment:
                    connector_display_name = enrichment["connector_display_name"]
                    connector_id: ConnectorIdEnum | None = None
                    if "Domain Tools" in connector_display_name:
                        connector_id = ConnectorIdEnum.DOMAINTOOLS
                    if "Tenable" in connector_display_name:
                        connector_id = ConnectorIdEnum.TENABLE
                    del enrichment["connector_display_name"]
                    if connector_id is not None:
                        enrichment["connector_id"] = connector_id
                        new_enrichments.append(enrichment)
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {"connector_enrichments": new_enrichments},
                },
            )
        logger().info("Alert Enrichment April 15, 2025 Migration Complete")

    # Supports schema as of April 24, 2025
    async def _24_04_2025_migrate_enrichment(self):
        if self._storage_collection is None:
            raise AlertEnrichmentException(
                "Unable to get alert enrichments because no storage collection was initialized."
            )

        enrichment_from_storage = self._storage_collection.find(
            {
                "time_created": {"$exists": True},
                "archived_at": None,
            }
        )
        async for d in enrichment_from_storage:
            saved_id = d.get("_id")
            saved_alert_id = d.get("id")
            saved_connector = d.get("connector")
            if "_id" in d:
                del d["_id"]
            if "archived_at" in d:
                del d["archived_at"]
            if "id" in d:
                del d["id"]
            if "connector" in d:
                del d["connector"]
            new_document = {
                "id": saved_alert_id,
                "connector": saved_connector,
                "insight": d,
            }
            await self._storage_collection.replace_one(
                {"_id": saved_id},
                new_document,
                upsert=True,
            )
        logger().info("Alert Enrichment April 10, 2025 Migration Complete")
