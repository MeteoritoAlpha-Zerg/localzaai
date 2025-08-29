import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.alert_enrichments.alert_enrichment_manager import (
    AlertEnrichmentManager,
)
from common.managers.alert_enrichments.alert_enrichment_model import (
    AlertAnomaly,
    AlertEnrichment,
    AlertEnrichmentId,
    AlertInsight,
)
from common.models.connector_id_enum import ConnectorIdEnum


@pytest.fixture(autouse=True)
async def alert_enrichment_manager():
    manager = AlertEnrichmentManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["alert_enrichments"]
    # Uncomment for testing against local MongoDB
    # from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
    # await MongoDbClient.initialize(MongoDbConfig())
    # collection = MongoDbClient.get_collection("metamorph_test", "alert_enrichments")
    await manager.initialize(collection)
    return manager


async def test_enrichments_not_exist(
    alert_enrichment_manager: AlertEnrichmentManager,
) -> None:
    enrichments = await alert_enrichment_manager.get_alert_enrichments_async()
    assert len(enrichments) == 0


async def test_get_all_enrichments(
    alert_enrichment_manager: AlertEnrichmentManager,
) -> None:
    alert = AlertEnrichment(
        connector=ConnectorIdEnum.SPLUNK,
        id="123",
        insight=AlertInsight(summary="summary"),
    )
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert)

    m = await alert_enrichment_manager.get_alert_enrichments_async()
    assert len(m) == 1


async def test_upsert(alert_enrichment_manager: AlertEnrichmentManager) -> None:
    alert = AlertEnrichment(
        connector=ConnectorIdEnum.SPLUNK,
        id="123",
        insight=AlertInsight(summary="summary"),
    )
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert)
    saved_enrichment = await alert_enrichment_manager.get_alert_enrichment_async(
        connector=ConnectorIdEnum.SPLUNK, id="123"
    )

    assert saved_enrichment is not None
    assert saved_enrichment.insight is not None
    assert saved_enrichment.insight.summary == "summary"

    saved_enrichment.insight.summary = "summary2"
    new_enrichment = await alert_enrichment_manager.upsert_alert_enrichment_async(saved_enrichment)
    assert new_enrichment.insight is not None
    assert new_enrichment.insight.summary == "summary2"


async def test_upsert_incomplete_model(
    alert_enrichment_manager: AlertEnrichmentManager,
) -> None:
    alert = AlertEnrichment(
        connector=ConnectorIdEnum.SPLUNK,
        id="123",
        insight=AlertInsight(summary="summary"),
    )
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert)
    saved_enrichment = await alert_enrichment_manager.get_alert_enrichment_async(
        connector=ConnectorIdEnum.SPLUNK, id="123"
    )

    assert saved_enrichment is not None
    assert saved_enrichment.anomaly_info is None

    saved_enrichment.anomaly_info = AlertAnomaly(anomaly_score=0.5)

    new_enrichment = await alert_enrichment_manager.upsert_alert_enrichment_async(saved_enrichment)
    assert new_enrichment.insight is not None
    assert new_enrichment.anomaly_info is not None


async def test_delete(alert_enrichment_manager: AlertEnrichmentManager) -> None:
    alert = AlertEnrichment(
        connector=ConnectorIdEnum.SPLUNK,
        id="123",
        insight=AlertInsight(summary="summary"),
    )
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert)

    alert2 = AlertEnrichment(
        id="1234",
        connector=ConnectorIdEnum.SPLUNK,
        insight=AlertInsight(
            summary="summary",
        ),
    )
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert2)

    alert3 = AlertEnrichment(id="123_group", connector=None, insight=AlertInsight(summary="summary"))
    await alert_enrichment_manager.upsert_alert_enrichment_async(alert3)

    await alert_enrichment_manager.archive_alert_enrichments_async(
        alerts=[
            AlertEnrichmentId(connector=alert.connector, id=alert.id),
            AlertEnrichmentId(connector=alert2.connector, id="not real alert"),
        ]
    )

    all_alerts = await alert_enrichment_manager.get_alert_enrichments_async()
    assert len(all_alerts) == 2


async def test_delete_no_ids(alert_enrichment_manager: AlertEnrichmentManager) -> None:
    await alert_enrichment_manager.archive_alert_enrichments_async(alerts=[])
