import json
from unittest.mock import MagicMock, patch

from connectors.tenable.connector.config import TenableConnectorConfig
from connectors.tenable.connector.target import TenableTarget
from connectors.tenable.connector.tools import TenableConnectorTools

from common.models.metadata import QueryResultMetadata

mock_config = MagicMock(spec=TenableConnectorConfig)
mock_config.access_key = MagicMock()
mock_config.access_key.get_secret_value.return_value = "mock_access_key"
mock_config.secret_key = MagicMock()
mock_config.secret_key.get_secret_value.return_value = "mock_secret_key"


@patch("httpx.AsyncClient.get")
async def test_get_asset_filters(mock_get):
    mock_response = MagicMock()
    expected_response = {"filters": ["filter1", "filter2"]}
    mock_response.json.return_value = expected_response
    mock_get.return_value = mock_response

    mock_target = MagicMock(spec=TenableTarget)

    tools = TenableConnectorTools(tenable_config=mock_config, target=mock_target, connector_display_name="Tenable")

    result = await tools.get_asset_filters_async(input=None)

    assert result == QueryResultMetadata(
        query_format="Tenable API",
        query="https://cloud.tenable.com/filters/workbenches/assets",
        column_headers=['filters/workbenches/assets'],
        results=[[json.dumps(expected_response)]],
    )

    mock_get.assert_called_once_with(
        url="https://cloud.tenable.com/filters/workbenches/assets",
        headers={
            "accept": "application/json",
            "X-ApiKeys": "accessKey=mock_access_key;secretKey=mock_secret_key",
        },
    )


@patch("httpx.AsyncClient.get")
async def test_get_vulnerability_filters(mock_get):
    mock_response = MagicMock()
    expected_response = {"filters": ["filter1", "filter2"]}
    mock_response.json.return_value = expected_response
    mock_get.return_value = mock_response

    mock_target = MagicMock(spec=TenableTarget)

    tools = TenableConnectorTools(tenable_config=mock_config, target=mock_target, connector_display_name="Tenable")

    result = await tools.get_vulnerability_filters_async(input=None)
    assert result == QueryResultMetadata(
        query_format="Tenable API",
        query="https://cloud.tenable.com/filters/workbenches/vulnerabilities",
        column_headers=['filters/workbenches/vulnerabilities'],
        results=[[json.dumps(expected_response)]],
    )

    mock_get.assert_called_once_with(
        url="https://cloud.tenable.com/filters/workbenches/vulnerabilities",
        headers={
            "accept": "application/json",
            "X-ApiKeys": "accessKey=mock_access_key;secretKey=mock_secret_key",
        },
    )
