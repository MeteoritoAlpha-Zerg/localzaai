import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from common.models.connector_id_enum import ConnectorIdEnum
from pydantic import ValidationError

from connectors.cloudwatch.connector.config import CloudWatchConnectorConfig
from connectors.cloudwatch.connector.secrets import CloudWatchSecrets
from connectors.cloudwatch.connector.target import CloudWatchTarget
from connectors.cloudwatch.connector.tools import (
    CloudWatchConnectorTools,
    GetCloudWatchLogsFilterPatternInput,
    GetCloudWatchLogsInputBase,
    GetCloudWatchLogsInsightsQueryInput,
)


def test_valid_iso_format():
    input_data = GetCloudWatchLogsInputBase(
        start_time="2025-04-15T10:30:00Z", end_time="2025-04-15T11:30:00+00:00", limit=100
    )
    assert input_data.start_time == "2025-04-15T10:30:00+00:00"
    assert input_data.end_time == "2025-04-15T11:30:00+00:00"


def test_invalid_iso_format():
    with pytest.raises(ValidationError):
        GetCloudWatchLogsInputBase(start_time="March 14 2025", end_time="2025-04-15T11:30:00Z", limit=100)


def test_start_timestamp():
    input_data = GetCloudWatchLogsInputBase(
        start_time="2025-04-15T10:30:00Z", end_time="2025-04-15T11:30:00Z", limit=100
    )
    expected_timestamp = int(datetime(2025, 4, 15, 10, 30, tzinfo=timezone.utc).timestamp() * 1000)
    assert input_data.start_timestamp == expected_timestamp


def test_end_timestamp():
    input_data = GetCloudWatchLogsInputBase(
        start_time="2025-04-15T10:30:00Z", end_time="2025-04-15T11:30:00Z", limit=100
    )
    expected_timestamp = int(datetime(2025, 4, 15, 11, 30, tzinfo=timezone.utc).timestamp() * 1000)
    assert input_data.end_timestamp == expected_timestamp


def test_pagination_config():
    input_data = GetCloudWatchLogsInputBase(
        start_time="2025-04-15T10:30:00Z", end_time="2025-04-15T11:30:00Z", limit=500
    )
    assert input_data.pagination_config == {"MaxItems": 500, "PageSize": 500}


def test_pagination_config_limit_exceeds():
    input_data = GetCloudWatchLogsInputBase(
        start_time="2025-04-15T10:30:00Z", end_time="2025-04-15T11:30:00Z", limit=1500
    )
    assert input_data.pagination_config == {"MaxItems": 1500, "PageSize": 1000}


def test_valid_insights_query():
    input_data = GetCloudWatchLogsInsightsQueryInput(
        start_time="2023-04-15T10:30:00Z",
        end_time="2023-04-15T11:30:00Z",
        limit=100,
        insights_query="fields @timestamp, @message | filter @message like /ERROR/",
    )
    assert input_data.insights_query == "fields @timestamp, @message | filter @message like /ERROR/"


def test_invalid_insights_query_start_command():
    with pytest.raises(ValidationError):
        GetCloudWatchLogsInsightsQueryInput(
            start_time="2023-04-15T10:30:00Z",
            end_time="2023-04-15T11:30:00Z",
            limit=100,
            insights_query="invalid_command @timestamp, @message | filter @message like /ERROR/",
        )


def test_unbalanced_double_quotes():
    with pytest.raises(ValidationError):
        GetCloudWatchLogsInsightsQueryInput(
            start_time="2023-04-15T10:30:00Z",
            end_time="2023-04-15T11:30:00Z",
            limit=100,
            insights_query='fields @timestamp, @message | filter @message like "ERROR',
        )


def test_unbalanced_single_quotes():
    with pytest.raises(ValidationError):
        GetCloudWatchLogsInsightsQueryInput(
            start_time="2023-04-15T10:30:00Z",
            end_time="2023-04-15T11:30:00Z",
            limit=100,
            insights_query="fields @timestamp, @message | filter @message like 'ERROR",
        )


def test_unbalanced_regex_delimiters():
    with pytest.raises(ValidationError):
        GetCloudWatchLogsInsightsQueryInput(
            start_time="2023-04-15T10:30:00Z",
            end_time="2023-04-15T11:30:00Z",
            limit=100,
            insights_query="fields @timestamp, @message | filter @message like /ERROR",
        )


def test_valid_complex_insights_query():
    input_data = GetCloudWatchLogsInsightsQueryInput(
        start_time="2023-04-15T10:30:00Z",
        end_time="2023-04-15T11:30:00Z",
        limit=100,
        insights_query='filter level="ERROR" | stats count(*) by service | sort @timestamp desc | limit 20',
    )
    assert (
        input_data.insights_query
        == 'filter level="ERROR" | stats count(*) by service | sort @timestamp desc | limit 20'
    )


def test_parse_fields_simple_dict():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"name": "Alice", "age": 30}
    expected = ["name", "age"]
    assert set(instance._parse_fields(query_result)) == set(expected)


def test_parse_fields_nested_dict():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"person": {"name": "Alice", "age": 30}}
    expected = ["person.name", "person.age", "person"]
    assert set(instance._parse_fields(query_result)) == set(expected)


def test_parse_fields_list_of_dicts():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"people": [{"name": "Alice"}, {"name": "Bob"}]}
    expected = ["people.name", "people.name", "people"]
    assert set(instance._parse_fields(query_result)) == set(expected)


def test_parse_fields_json_string():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"data": json.dumps({"name": "Alice", "age": 30})}
    expected = ["data.name", "data.age", "data"]
    assert set(instance._parse_fields(query_result)) == set(expected)


def test_parse_fields_invalid_json_string():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"data": "invalid json"}
    expected = ["data"]
    assert set(instance._parse_fields(query_result)) == set(expected)


def test_parse_fields_with_prefix():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"name": "Alice", "age": 30}
    expected = ["prefix.name", "prefix.age"]
    assert set(instance._parse_fields(query_result, prefix="prefix")) == set(expected)


def test_parse_fields_with_at_symbol():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    query_result = {"@meta": {"name": "Alice", "age": 30}}
    expected = ["name", "age", "@meta"]
    assert set(instance._parse_fields(query_result)) == set(expected)


@pytest.mark.asyncio
async def test_fetch_insights_query_success():
    # Create an instance of the class containing _fetch_insights_query
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )

    # Mock input data
    input_data = GetCloudWatchLogsInsightsQueryInput(
        start_time="2025-04-15T10:30:00Z",
        end_time="2025-04-15T11:30:00+00:00",
        limit=100,
        insights_query="fields @timestamp, @message | sort @timestamp desc",
    )

    # Mock client
    mock_client = AsyncMock()
    mock_client.start_query.return_value = {"queryId": "test-query-id"}
    mock_client.get_query_results.side_effect = [
        {"status": "Running"},
        {
            "status": "Complete",
            "results": [
                [
                    {"field": "@timestamp", "value": "2021-06-01T12:00:00Z"},
                    {"field": "@message", "value": "Test message"},
                ]
            ],
        },
    ]

    # Call the method
    events = await instance._fetch_insights_query(input_data, mock_client, "test-log-group")

    # Assert the results
    assert len(events) == 1
    assert events[0]["message"] == "{'@timestamp': '2021-06-01T12:00:00Z', '@message': 'Test message'}"
    assert events[0]["timestamp"] == 1622548800000  # Converted timestamp
    assert events[0]["insights_result"] == {"@timestamp": "2021-06-01T12:00:00Z", "@message": "Test message"}


@pytest.mark.asyncio
async def test_fetch_insights_query_failure():
    # Create an instance of the class containing _fetch_insights_query
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )

    # Mock input data
    input_data = GetCloudWatchLogsInsightsQueryInput(
        start_time="2025-04-15T10:30:00Z",
        end_time="2025-04-15T11:30:00+00:00",
        limit=100,
        insights_query="fields @timestamp, @message | sort @timestamp desc",
    )

    # Mock client
    mock_client = AsyncMock()
    mock_client.start_query.return_value = {"queryId": "test-query-id"}
    mock_client.get_query_results.return_value = {"status": "Failed"}

    # Call the method
    events = await instance._fetch_insights_query(input_data, mock_client, "test-log-group")

    # Assert the results
    assert len(events) == 1
    assert events[0]["message"] == "Query failed with status: Failed"
    assert events[0]["error"] is True


@pytest.mark.asyncio
async def test_fetch_standard_query_success():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )

    input_data = GetCloudWatchLogsFilterPatternInput(
        start_time="2025-04-15T10:30:00Z",
        end_time="2025-04-15T11:30:00+00:00",
        limit=10,
        filter_pattern="ERROR",
        pagination_config={"MaxItems": 10},
    )

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value.__aiter__.return_value = [
        {"events": [{"message": "ERROR", "timestamp": 1622548800000}]},
    ]

    events = await instance._fetch_standard_query(input_data, mock_client, "test-log-group")

    assert len(events) == 1
    assert events[0]["message"] == "ERROR"
    assert events[0]["timestamp"] == 1622548800000


@pytest.mark.asyncio
async def test_fetch_standard_query_with_filter_pattern():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )

    input_data = GetCloudWatchLogsFilterPatternInput(
        start_time="2025-04-15T10:30:00Z",
        end_time="2025-04-15T11:30:00+00:00",
        limit=10,
        filter_pattern="INFO",
        pagination_config={"MaxItems": 10},
    )

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value.__aiter__.return_value = [
        {"events": [{"message": "INFO hey hey hey", "timestamp": 1622548800000}]},
    ]

    events = await instance._fetch_standard_query(input_data, mock_client, "test-log-group")

    assert len(events) == 1
    assert events[0]["message"] == "INFO hey hey hey"
    assert events[0]["timestamp"] == 1622548800000


@pytest.mark.asyncio
async def test_fetch_standard_query_error_handling():
    instance = CloudWatchConnectorTools(
        config=CloudWatchConnectorConfig(id=ConnectorIdEnum.CLOUDWATCH),
        target=CloudWatchTarget(),
        secrets=CloudWatchSecrets(),
    )
    input_data = GetCloudWatchLogsFilterPatternInput(
        start_time="2025-04-15T10:30:00Z",
        end_time="2025-04-15T11:30:00+00:00",
        limit=10,
        filter_pattern=None,
        pagination_config={"MaxItems": 10},
    )

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value.__aiter__.side_effect = Exception("Test exception")

    events = await instance._fetch_standard_query(input_data, mock_client, "test-log-group")

    assert len(events) == 0  # Assuming empty list is returned on error
