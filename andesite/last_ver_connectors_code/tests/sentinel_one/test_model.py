import pytest

from connectors.sentinel_one.connector.model.alert_model import (
    AgentDetectionInfo,
    SentinelOneAlert,
)
from connectors.sentinel_one.connector.model.endpoint_model import (
    Alert,
    SentinelOneEndpoint,
)
from connectors.sentinel_one.connector.model.pagination_model import (
    Pagination,
    SentinelOneApiResponse,
)
from connectors.sentinel_one.connector.model.threat_model import (
    SentinelOneThreat,
    ThreatInfo,
)
from tests.sentinel_one.util import read_json_file_for_resource


@pytest.mark.parametrize(
    "resource,type",
    [
        ("alerts", SentinelOneAlert),
        ("endpoints", SentinelOneEndpoint),
        ("threats", SentinelOneThreat),
    ],
)
def test_paginated_model(resource, type):
    json_response = read_json_file_for_resource(resource)
    model = SentinelOneApiResponse[type](**json_response)
    assert model
    assert model.data
    assert model.pagination
    assert model.errors is None
    assert len(model.data) == 1


@pytest.mark.parametrize("type", [SentinelOneAlert, SentinelOneThreat, SentinelOneEndpoint])
def test_paginated_model_populates_error(type):
    payload = {
        "data": [],
        "errors": [{"message": "some error"}],
    }
    model = SentinelOneApiResponse[type](**payload)
    assert model == SentinelOneApiResponse[type](data=[], errors=[{"message": "some error"}])


@pytest.mark.parametrize(
    "payload,type,expected_model",
    [
        (
            {
                "data": [{"agentDetectionInfo": {"machineType": "laptop"}}],
                "pagination": {"totalItems": 123, "nextCursor": "abc"},
            },
            SentinelOneAlert,
            SentinelOneApiResponse[SentinelOneAlert](
                data=[
                    SentinelOneAlert(  # type: ignore[call-arg]
                        agent_detection_info=AgentDetectionInfo(machine_type="laptop")  # type: ignore[call-arg]
                    )
                ],
                pagination=Pagination(total_items=123, next_cursor="abc"),
            ),
        ),
        (
            {
                "data": [{"threatInfo": {"analystVerdict": "true_positive"}}],
                "pagination": {"totalItems": 2, "nextCursor": "abc"},
            },
            SentinelOneThreat,
            SentinelOneApiResponse[SentinelOneThreat](
                data=[
                    SentinelOneThreat(  # type: ignore[call-arg]
                        threat_info=ThreatInfo(analyst_verdict="true_positive")  # type: ignore[call-arg]
                    )
                ],
                pagination=Pagination(total_items=2, next_cursor="abc"),
            ),
        ),
        (
            {
                "data": [{"alerts": [{"count": 2, "severity": "Medium"}]}],
                "pagination": {"totalItems": 2, "nextCursor": "abc"},
            },
            SentinelOneEndpoint,
            SentinelOneApiResponse[SentinelOneEndpoint](
                data=[SentinelOneEndpoint(alerts=[Alert(count=2, severity="Medium")])],  # type: ignore[call-arg]
                pagination=Pagination(total_items=2, next_cursor="abc"),
            ),
        ),
    ],
)
def test_paginated_model_populates_pagination(payload, type, expected_model):
    model = SentinelOneApiResponse[type](**payload)
    assert model == expected_model


@pytest.mark.parametrize(
    "resource,type",
    [
        ("alerts", SentinelOneAlert),
        ("threats", SentinelOneThreat),
        ("endpoints", SentinelOneEndpoint),
    ],
)
def test_resource_model(resource, type):
    json_response = read_json_file_for_resource(resource)
    first_item = json_response["data"][0]
    model = type(**first_item)
    assert first_item == model.model_dump(by_alias=True, exclude_unset=True)
