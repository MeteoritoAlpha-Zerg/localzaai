from unittest.mock import MagicMock, patch

import httpx
import pytest
from common.models.metadata import QueryResultMetadata
from common.models.tool import ToolResult
from pydantic import SecretStr

from connectors.tenable.connector.config import TenableConnectorConfig
from connectors.tenable.connector.secrets import TenableSecrets
from connectors.tenable.connector.target import TenableTarget
from connectors.tenable.connector.tools import TenableConnectorTools

mock_config = MagicMock(spec=TenableConnectorConfig)
mock_config.access_key = MagicMock()
mock_config.access_key.get_secret_value.return_value = "mock_access_key"
mock_config.secret_key = MagicMock()
mock_config.secret_key.get_secret_value.return_value = "mock_secret_key"


@pytest.mark.parametrize(
    "response_json,tool_name,tool_input,expected_return,expected_http_args",
    [
        (
            {"filters": ["filter1", "filter2"]},
            "get_asset_filters_async",
            None,
            QueryResultMetadata(
                query_format="Tenable API",
                query="https://cloud.tenable.com/filters/workbenches/assets",
                column_headers=["filters/workbenches/assets"],
                results=[['{"filters": ["filter1", "filter2"]}']],
            ),
            {
                "url": "https://cloud.tenable.com/filters/workbenches/assets",
            },
        ),
        (
            {"test": "json"},
            "get_assets_async",
            TenableConnectorTools.GetAssetsInput(age=2, filters=[("a", "b", "c")]),
            ToolResult(
                result=QueryResultMetadata(
                    query_format="Tenable API",
                    query="https://cloud.tenable.com/workbenches/assets?all_fields=default&date_range=2&filter.0.filter=a&filter.0.quality=b&filter.0.value=c",
                    column_headers=["workbenches/assets"],
                    results=[['{"test": "json"}']],
                ),
                additional_context=None,
            ),
            {
                "url": "https://cloud.tenable.com/workbenches/assets?all_fields=default&date_range=2&filter.0.filter=a&filter.0.quality=b&filter.0.value=c",
            },
        ),
        (
            {"test": "json"},
            "get_asset_info_async",
            TenableConnectorTools.GetAssetInfoInput(id="test", all_fields=True),
            QueryResultMetadata(
                query_format="Tenable API",
                query="https://cloud.tenable.com/workbenches/assets/test/info?all_fields=full",
                column_headers=["workbenches/assets/test/info"],
                results=[['{"test": "json"}']],
            ),
            {
                "url": "https://cloud.tenable.com/workbenches/assets/test/info?all_fields=full",
            },
        ),
        (
            {"total_vulnerability_count": 2, "vulnerabilities": ["a", "b"]},
            "get_asset_vulnerabilities_async",
            TenableConnectorTools.GetAssetVulnerabilitiesInput(id="test"),
            ToolResult(
                result=QueryResultMetadata(
                    query_format="Tenable API",
                    query="https://cloud.tenable.com/workbenches/assets/test/vulnerabilities",
                    column_headers=["workbenches/assets/test/vulnerabilities"],
                    results=[['{"total_vulnerability_count": 2, "vulnerabilities": ["a", "b"]}']],
                ),
                additional_context=None,
            ),
            {
                "url": "https://cloud.tenable.com/workbenches/assets/test/vulnerabilities",
            },
        ),
        (
            {"filters": ["filter1", "filter2"]},
            "get_vulnerability_filters_async",
            TenableConnectorTools.GetAssetVulnerabilitiesInput(id="test"),
            QueryResultMetadata(
                query_format="Tenable API",
                query="https://cloud.tenable.com/filters/workbenches/vulnerabilities",
                column_headers=["filters/workbenches/vulnerabilities"],
                results=[['{"filters": ["filter1", "filter2"]}']],
            ),
            {
                "url": "https://cloud.tenable.com/filters/workbenches/vulnerabilities",
            },
        ),
        (
            {"filters": ["filter1", "filter2"]},
            "get_vulnerabilities_async",
            TenableConnectorTools.GetVulnerabilitiesInput(),
            ToolResult(
                result=QueryResultMetadata(
                    query_format="Tenable API",
                    query="https://cloud.tenable.com/workbenches/vulnerabilities",
                    column_headers=["workbenches/vulnerabilities"],
                    results=[['{"filters": ["filter1", "filter2"]}']],
                ),
                additional_context=None,
            ),
            {
                "url": "https://cloud.tenable.com/workbenches/vulnerabilities",
            },
        ),
    ],
)
@patch("httpx.AsyncClient.get")
async def test_tools(mock_get, response_json, tool_name, tool_input, expected_return, expected_http_args):
    mock_response = MagicMock()
    expected_response = response_json
    mock_response.json.return_value = expected_response
    mock_get.return_value = mock_response

    mock_target = MagicMock(spec=TenableTarget)
    tools = TenableConnectorTools(
        tenable_config=mock_config,
        target=mock_target,
        secrets=TenableSecrets(access_key=SecretStr("mock_access_key"), secret_key=SecretStr("mock_secret_key")),
    )
    result = await getattr(tools, tool_name)(input=tool_input)

    assert result == expected_return
    mock_get.assert_called_once_with(
        **expected_http_args,
        headers={
            "accept": "application/json",
            "X-ApiKeys": "accessKey=mock_access_key;secretKey=mock_secret_key",
        },
    )


@patch("httpx.AsyncClient.get")
async def test_call_tenable(mock_get):
    mock_get.side_effect = httpx.HTTPStatusError(
        message="error",
        request=httpx.Request(method="get", url="test"),
        response=httpx.Response(status_code=404, text="error"),
    )
    tools = TenableConnectorTools(
        tenable_config=mock_config,
        target=MagicMock(spec=TenableTarget),
        secrets=TenableSecrets(access_key=SecretStr("mock_access_key"), secret_key=SecretStr("mock_secret_key")),
    )
    with pytest.raises(Exception, match="API Error. Code=404,Response=error"):
        await tools.call_tenable_api("")


def test_filter_query_params():
    tools = TenableConnectorTools(
        tenable_config=mock_config,
        target=MagicMock(spec=TenableTarget),
        secrets=TenableSecrets(access_key=SecretStr("mock_access_key"), secret_key=SecretStr("mock_secret_key")),
    )
    params = tools._get_filters_query_params([("a", "b", 1), ("c", "d", 2)])
    assert params == [
        "filter.0.filter=a",
        "filter.0.quality=b",
        "filter.0.value=1",
        "filter.1.filter=c",
        "filter.1.quality=d",
        "filter.1.value=2",
    ]


def test_url_building():
    tools = TenableConnectorTools(
        tenable_config=mock_config,
        target=MagicMock(spec=TenableTarget),
        secrets=TenableSecrets(access_key=SecretStr("mock_access_key"), secret_key=SecretStr("mock_secret_key")),
    )
    url = tools._get_full_url("path", ["param"])
    assert url == "https://cloud.tenable.com/path?param"
