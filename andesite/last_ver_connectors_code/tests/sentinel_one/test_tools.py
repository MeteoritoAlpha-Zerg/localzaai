from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from common.models.tool import ToolResult
from pydantic import SecretStr

from connectors.connector_id_enum import ConnectorIdEnum
from connectors.sentinel_one.connector.config import SentinelOneConnectorConfig
from connectors.sentinel_one.connector.tools import (
    SentinelOneConnectorException,
    SentinelOneConnectorTools,
    SentinelOneResource,
)
from tests.sentinel_one.util import read_json_file_for_resource

TEST_API_ENDPOINT = "foo"
TEST_API_SECRET = SecretStr("secret")


@pytest.fixture
def sentinel_one_api():
    def mock_get(url, *args, **kwargs):
        json_response = read_json_file_for_resource(url)
        mock = Mock(spec=httpx.Response)
        mock.json.return_value = json_response
        return mock

    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(side_effect=mock_get)) as mock:
        yield mock


@pytest.fixture
def tools():
    config = SentinelOneConnectorConfig(
        id=ConnectorIdEnum.SENTINEL_ONE, api_endpoint=TEST_API_ENDPOINT, token=TEST_API_SECRET
    )
    return SentinelOneConnectorTools(display_name="test_connector", config=config)


def test_convert_to_tools_response(tools):
    result = tools.convert_to_tool_response(
        SentinelOneResource.ALERTS,
        {"data": [{"agentDetectionInfo": {"machineType": "laptop"}}], "pagination": {"totalItems": 123}},
    )
    response = '{"data": [{"agentDetectionInfo": {"machineType": "laptop"}}], "pagination": {"totalItems": 123}}'
    assert result == ToolResult(
        additional_context=None,
        result=response,
    )


@pytest.mark.parametrize(
    "resource", [SentinelOneResource.ENDPOINT, SentinelOneResource.THREAT, SentinelOneResource.ALERTS]
)
async def test_get_resource_correct_args(tools, sentinel_one_api, resource):
    result = await tools._get_s1_resource_async(resource, SentinelOneConnectorTools.GetResourceInput())
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + resource.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET.get_secret_value()}"},
    )


async def test_get_resource_uses_pagination_token(tools, sentinel_one_api):
    pagination_token = "next_page"
    result = await tools._get_s1_resource_async(
        SentinelOneResource.ALERTS, SentinelOneConnectorTools.GetResourceInput(cursor=pagination_token)
    )
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET.get_secret_value()}"},
        params={"cursor": pagination_token},
    )


@pytest.mark.parametrize(
    "resource_input,expected_params",
    [
        (SentinelOneConnectorTools.GetResourceInput(limit=20), {"limit": 20}),
        (SentinelOneConnectorTools.GetResourceInput(skip=25), {"skip": 25}),
        (SentinelOneConnectorTools.GetResourceInput(cursor="foo"), {"cursor": "foo"}),
        (
            SentinelOneConnectorTools.GetResourceInput(sort_by="foo", sort_order="desc"),
            {"sortBy": "foo", "sortOrder": "desc"},
        ),
    ],
)
async def test_get_resource_uses_params(tools, sentinel_one_api, resource_input, expected_params):
    result = await tools._get_s1_resource_async(SentinelOneResource.ALERTS, resource_input)
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET.get_secret_value()}"},
        params=expected_params,
    )


async def test_get_resource_does_not_pass_params(tools, sentinel_one_api):
    result = await tools._get_s1_resource_async(
        SentinelOneResource.ALERTS, SentinelOneConnectorTools.GetResourceInput()
    )
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET.get_secret_value()}"},
    )


def test_sort_order_without_sort_by():
    with pytest.raises(ValueError, match="sortBy is required when sortOrder is set"):
        SentinelOneConnectorTools.GetResourceInput(sort_order="desc")


def test_sort_order_invalid():
    with pytest.raises(ValueError):
        SentinelOneConnectorTools.GetResourceInput(sort_order="foo")


@pytest.mark.parametrize("error", [httpx.HTTPStatusError, httpx.RequestError, Exception])
async def test_get_resource_returns_none_on_error(tools, error):
    with patch.object(httpx.AsyncClient, "get", new=AsyncMock(side_effect=error)), pytest.raises(
        SentinelOneConnectorException
    ):
        await tools._get_s1_resource_async(SentinelOneResource.ALERTS, SentinelOneConnectorTools.GetResourceInput())
