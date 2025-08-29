from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.secret import StorableSecret

from connectors.proofpoint.client.proofpoint_instance import (
    SegmentTimeUnit,
    _segment_interval_by_unit,
)
from connectors.proofpoint.connector.config import ProofpointConnectorConfig
from connectors.proofpoint.connector.target import ProofpointTarget
from connectors.proofpoint.connector.tools import (
    FindCampaignsWithIOCsInput,
    FindSiemEventsByIOCsInput,
    GetCampaignIdsInput,
    GetForensicsByThreatInput,
    GetSiemEventsInput,
    ProofpointConnectorTools,
    search_for_iocs_in_records,
)
from tests.proofpoint.test_data import (
    get_test_find_iocs_in_campaigns_data,
    get_test_find_iocs_in_siem_events_data,
    get_test_get_forensics_data,
    get_test_get_siem_events_data,
)


def test_segment_interval_same_day():
    """Test the _segment_interval function."""
    interval = "2020-05-01T01:00:00Z/2020-05-01T02:00:00Z"
    expected_segments = [
        "2020-05-01T01:00:00Z/2020-05-01T02:00:00Z",
    ]
    result = _segment_interval_by_unit(interval, SegmentTimeUnit.DAY)
    assert result == expected_segments


def test_segment_interval_two_days():
    """Test the _segment_interval function."""
    interval = "2020-05-01T00:00:00Z/2020-05-03T00:00:00Z"
    expected_segments = [
        "2020-05-01T00:00:00Z/2020-05-02T00:00:00Z",
        "2020-05-02T00:00:00Z/2020-05-03T00:00:00Z",
    ]
    result = _segment_interval_by_unit(interval, SegmentTimeUnit.DAY)
    assert result == expected_segments


def test_segment_interval_two_days_with_extra():
    """Test the _segment_interval function."""
    interval = "2020-05-01T00:00:00Z/2020-05-02T00:10:00Z"
    expected_segments = [
        "2020-05-01T00:00:00Z/2020-05-02T00:00:00Z",
        "2020-05-02T00:00:00Z/2020-05-02T00:10:00Z",
    ]
    result = _segment_interval_by_unit(interval, SegmentTimeUnit.DAY)
    assert result == expected_segments


@pytest.mark.anyio
@patch("connectors.proofpoint.connector.tools.DatasetStructureManager.instance")
@pytest.mark.asyncio
async def test_get_campaigns_multiple_days(mocker):
    # Mock dataset structure manager
    mock_dsm = AsyncMock()
    mocker.return_value = mock_dsm

    # Create mock datasets representing 4 days of indexed data
    mock_datasets = []
    base_time = datetime(2025, 6, 20, 0, 0, 0)  # Start date

    for i in range(4):
        day_start = base_time + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        interval_str = f"{day_start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{day_end.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        mock_dataset = DatasetStructure(
            connector=ConnectorIdEnum.PROOFPOINT,
            dataset=interval_str,
            attributes={
                "campaigns": [
                    {"id": f"campaign_{i}_1", "name": f"Campaign {i}-1", "lastUpdatedAt": "foo"},
                    {"id": f"campaign_{i}_2", "name": f"Campaign {i}-2", "lastUpdatedAt": "foo"},
                ]
                if i < 3
                else []  # Last day has no campaigns to test different data sizes
            },
        )
        mock_datasets.append(mock_dataset)

    mock_dsm.get_all_dataset_structures_async = AsyncMock(return_value=mock_datasets)

    target = ProofpointTarget()
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())
    result = await tools.get_campaign_ids_async(GetCampaignIdsInput(lookback_days=4))

    assert len(result) == 6


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_get_siem_events_data(),
)
@pytest.mark.asyncio
async def test_get_siem_events(mocker):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())

    inputs = GetSiemEventsInput(interval="2020-05-01T01:00:00Z/2020-05-01T01:30:00Z")

    result = await tools.get_siem_events_for_time_range_async(inputs)
    assert len(result["results"].keys()) == 4
    assert len(result["results"]["messagesBlocked"]) == 2
    assert len(result["results"]["messagesBlocked"][0]["message_parts"]) == 1
    assert result["results"]["clicksBlocked"][0]["sender_ip"] == "123.56.79.101"


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_get_forensics_data(),
)
@pytest.mark.asyncio
async def test_get_forensics(mocker):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())

    inputs = GetForensicsByThreatInput(threat_id="abc123", include_campaign_forensics=False, include_nonmalicious=False)

    result = await tools.get_forensics_by_threat_id(inputs)
    assert len(result["reports"]) == 2
    assert len(result["reports"][0]["forensics"]) == 1
    assert result["reports"][0]["forensics"][0]["what"] == "BadVirus"


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_find_iocs_in_siem_events_data(),
)
@pytest.mark.asyncio
async def test_find_iocs_in_siem_events(mocker):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())

    inputs_all = FindSiemEventsByIOCsInput(
        interval="2020-05-01T01:00:00Z/2020-05-01T01:30:00Z", iocs=["yourdomain.ai", "closetoyour"], event_type="all"
    )

    results_all = await tools.find_siem_events_by_iocs_async(inputs_all)
    assert len(results_all["results"].keys()) == 4
    assert results_all["results"]["messagesBlocked"][0]["iocs_found"] == ["yourdomain.ai"]
    assert sorted(results_all["results"]["clicksBlocked"][0]["iocs_found"]) == sorted(["yourdomain.ai", "closetoyour"])


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_find_iocs_in_siem_events_data(),
)
@pytest.mark.asyncio
async def test_find_iocs_in_siem_events_clicks_blocked(mocker):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())

    inputs = FindSiemEventsByIOCsInput(
        interval="2020-05-01T01:00:00Z/2020-05-01T01:30:00Z",
        iocs=["yourdomain.ai", "closetoyour"],
        event_type="clicks_blocked",
    )

    results = await tools.find_siem_events_by_iocs_async(inputs)
    assert len(results["results"].keys()) == 1
    assert sorted(results["results"]["clicksBlocked"][0]["iocs_found"]) == sorted(["yourdomain.ai", "closetoyour"])


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.connector.tools.ProofpointConnectorTools.get_campaign_ids_async",
    return_value=[{"id": "campaign-1"}, {"id": "campaign-2"}],
)
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_find_iocs_in_campaigns_data(),
)
@pytest.mark.asyncio
async def test_find_iocs_in_campaigns(mock_get_campaigns, mock_request):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock(), cache=None)

    inputs = FindCampaignsWithIOCsInput(
        lookback_days=2,
        iocs=["this/command/hacks.exe", "abc-123-def-456-ghi", "ashadydomain.ru"],
        include_campaign_members=True,
    )

    results = await tools.find_campaigns_by_iocs_async(inputs)

    assert len(results) == 1
    assert results[0]["id"] == "campaign_id_1"
    assert results[0]["campaignMembers"] == ["actor1", "actor2"]


@pytest.mark.anyio
@patch(
    "connectors.proofpoint.connector.tools.ProofpointConnectorTools.get_campaign_ids_async",
    return_value=[{"id": "campaign-1"}, {"id": "campaign-2"}],
)
@patch(
    "connectors.proofpoint.client.proofpoint_instance.AsyncClient.request",
    side_effect=get_test_find_iocs_in_campaigns_data(),
)
@pytest.mark.asyncio
async def test_find_iocs_in_campaigns_no_actors(mock_get_campaigns, mock_request):
    config = ProofpointConnectorConfig(
        id=ConnectorIdEnum.PROOFPOINT,
        api_host="foo",
        principal="bar",
        token=StorableSecret.model_validate("foobar", context={"encryption_key": "mock"}),
        request_timeout=0,
        max_retries=1,
    )
    target = ProofpointTarget()
    tools = ProofpointConnectorTools(config=config, target=target, secrets=MagicMock())
    inputs = FindCampaignsWithIOCsInput(
        lookback_days=2,
        iocs=["command/hacks.exe", "abc-123-def-456-ghi", "ashadydomain", "domain.ru"],
        include_campaign_members=False,
    )
    results = await tools.find_campaigns_by_iocs_async(inputs)
    assert len(results) == 1
    assert results[0]["id"] == "campaign_id_1"
    assert "campaignMembers" not in results[0]  # No actors in the response
    assert sorted(results[0]["iocs_found"]) == sorted(
        ["command/hacks.exe", "abc-123-def-456-ghi", "ashadydomain", "domain.ru"]
    )


def test_search_for_iocs_in_records():
    text = {
        "content": "Here is some text that contains a single ioc by itself. Cryptography has more possible iocs in one word."
    }

    iocs = ["ioc", "crypt", "graph", "racecar"]
    text_with_iocs = search_for_iocs_in_records([text], iocs)[0]
    assert sorted(text_with_iocs.get("iocs_found", [])) == sorted(["ioc", "crypt", "graph"])

    empty_results = search_for_iocs_in_records(["this is not a dict and should return nothing"], iocs)
    assert empty_results == []

    partial_results = search_for_iocs_in_records(
        ["this is not a dict and should return nothing", {"content": "racecar"}], ["ace"]
    )
    assert partial_results == [{"content": "racecar", "iocs_found": ["ace"]}]
