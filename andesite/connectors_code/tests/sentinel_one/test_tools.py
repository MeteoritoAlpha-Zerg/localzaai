import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.secret import StorableSecret
from pydantic import SecretStr

from connectors.sentinel_one.connector.config import SentinelOneConnectorConfig
from connectors.sentinel_one.connector.secrets import SentinelOneSecrets
from connectors.sentinel_one.connector.target import SentinelOneTarget
from connectors.sentinel_one.connector.tools import (
    SentinelOneConnectorException,
    SentinelOneConnectorTools,
    SentinelOneResource,
)
from tests.sentinel_one.util import read_json_file_for_resource, read_json_to_dict

TEST_API_ENDPOINT = "foo"
TEST_API_SECRET = "secret"


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
        id=ConnectorIdEnum.SENTINEL_ONE,
        api_endpoint=TEST_API_ENDPOINT,
        token=StorableSecret.model_validate(TEST_API_SECRET, context={"encryption_key": "mock"}),
    )
    return SentinelOneConnectorTools(config=config, secrets=SentinelOneSecrets(token=SecretStr(TEST_API_SECRET)))


@pytest.mark.parametrize("resource", [SentinelOneResource.THREAT, SentinelOneResource.ALERTS])
async def test_get_resource_correct_http_args(tools, sentinel_one_api, resource):
    result = await tools._get_s1_resource_async(resource, {})
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + resource.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
    )


@pytest.mark.parametrize("tool_name", [("get_threats_async"), ("get_alerts_async")])
async def test_get_resource_returns_tool(tools, sentinel_one_api, tool_name):
    tool_result = await getattr(tools, tool_name)(SentinelOneConnectorTools.GetResourceInput())
    assert tool_result.result


async def test_get_resource_uses_pagination_token(tools, sentinel_one_api):
    pagination_token = "next_page"
    result = await tools._get_s1_resource_async(SentinelOneResource.ALERTS, {"params": {"cursor": pagination_token}})
    assert result["data"]
    assert result["pagination"]
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"cursor": pagination_token},
    )


async def test_get_alerts_uses_params(tools, sentinel_one_api):
    tool_result = await tools.get_alerts_async(
        SentinelOneConnectorTools.GetAlertsInput(sourceProcessName__contains="chown", ruleName__contains="some rule")
    )
    assert tool_result.result
    assert tool_result.additional_context is None
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"sourceProcessName__contains": "chown", "ruleName__contains": "some rule", "limit": 10},
    )


async def test_get_threats_uses_params(tools, sentinel_one_api):
    tool_result = await tools.get_threats_async(
        SentinelOneConnectorTools.GetThreatsInput(
            commandLineArguments__contains="chown", mitigationStatuses="marked_as_benign"
        )
    )
    assert tool_result.result
    assert tool_result.additional_context is None
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.THREAT.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"limit": 10, "mitigationStatuses": "marked_as_benign", "commandLineArguments__contains": "chown"},
    )


@pytest.mark.parametrize(
    "error_to_raise,error_message",
    [
        (
            httpx.HTTPStatusError(
                response=httpx.Response(status_code=401), message="foo", request=httpx.Request(method="get", url="foo")
            ),
            "SentinelOne API token is not set or unauthorized",
        ),
        (
            httpx.HTTPStatusError(
                response=httpx.Response(text="response text", status_code=404),
                message="foo",
                request=httpx.Request(method="get", url="foo"),
            ),
            "SentinelOne returned an HTTP error 404, response text",
        ),
        (httpx.RequestError(message="foo"), "Unable to connect to SentinelOne"),
        (Exception, "Unknown error from SentinelOne"),
    ],
)
async def test_get_resource_returns_none_on_error(tools, error_to_raise, error_message):
    with (
        patch.object(httpx.AsyncClient, "get", new=AsyncMock(side_effect=error_to_raise)),
        pytest.raises(SentinelOneConnectorException, match=error_message),
    ):
        await tools._get_s1_resource_async(SentinelOneResource.ALERTS, {})


async def test_get_endpoints_no_args(tools, sentinel_one_api):
    tool_result = await tools.get_endpoints_async(SentinelOneConnectorTools.GetEndpointsInput())
    assert tool_result
    assert json.loads(tool_result.result) == read_json_to_dict("endpoints_expected_output.json")
    assert (
        tool_result.additional_context
        == "This tool can only return the first page of results and by default does not include application information."
    )
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ENDPOINT.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"limit": 10},
    )


@pytest.mark.parametrize(
    "limit, expected_context, expected_response",
    [
        (
            0,
            "This tool can only return the first page of results and by default does not include application information.",
            "endpoints_expected_output.json",
        ),
        (
            3,
            "This tool can only return the first page of results and up to 3 applications per result.",
            "endpoints_expected_output_2.json",
        ),
    ],
)
async def test_get_endpoints_limits(tools, sentinel_one_api, limit, expected_context, expected_response):
    tool_result = await tools.get_endpoints_async(
        SentinelOneConnectorTools.GetEndpointsInput(tool_application_limit=limit)
    )
    assert tool_result
    assert json.loads(tool_result.result) == read_json_to_dict(expected_response)
    assert tool_result.additional_context == expected_context
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ENDPOINT.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"limit": 10},
    )


async def test_get_threats(tools, sentinel_one_api):
    tool_result = await tools.get_threats_async(SentinelOneConnectorTools.GetThreatsInput())
    assert tool_result
    assert json.loads(tool_result.result) == read_json_to_dict("threats_expected_output.json")
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.THREAT.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"limit": 10},
    )


async def test_get_alerts(tools, sentinel_one_api):
    tool_result = await tools.get_alerts_async(SentinelOneConnectorTools.GetAlertsInput())
    assert tool_result
    assert json.loads(tool_result.result) == read_json_to_dict("alerts_expected_output.json")
    sentinel_one_api.assert_awaited_with(
        TEST_API_ENDPOINT + SentinelOneResource.ALERTS.api_path,
        headers={"Authorization": f"ApiToken {TEST_API_SECRET}"},
        params={"limit": 10},
    )


def test_s1_target():
    target = SentinelOneTarget()
    assert target.get_dataset_paths() == []
