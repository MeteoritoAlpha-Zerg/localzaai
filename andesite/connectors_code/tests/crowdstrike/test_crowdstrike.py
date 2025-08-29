from unittest.mock import patch

import pytest
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.secret import StorableSecret
from httpx import Request, Response
from pydantic import SecretStr

from connectors.crowdstrike.connector.config import CrowdstrikeConnectorConfig
from connectors.crowdstrike.connector.secrets import CrowdstrikeSecrets
from connectors.crowdstrike.connector.target import CrowdstrikeTarget
from connectors.crowdstrike.connector.tools import CrowdstrikeConnectorTools, GetSecurityAlertsInput


def test_crowdstrike_target():
    target = CrowdstrikeTarget()
    assert target.get_dataset_paths() == []


def test_crowdstrike_connector_tools():
    config = CrowdstrikeConnectorConfig(
        id=ConnectorIdEnum.CROWDSTRIKE,
        host="test_host",
        url="https://test_url.com",
        client_id="test_client_id",
        client_secret=StorableSecret.model_validate("test_client_secret", context={"encryption_key": "mock"}),
    )
    target = CrowdstrikeTarget()

    tools = CrowdstrikeConnectorTools(
        config, target, secrets=CrowdstrikeSecrets(client_secret=SecretStr("a"))
    ).get_tools()

    assert len(tools) == 1
    assert tools[0].name == "get_security_alerts"


@pytest.mark.anyio
@patch(
    "connectors.crowdstrike.connector.tools.AsyncClient.get",
    side_effect=[
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "resources": [
                    {"device_id": "device1"},
                    {"device_id": "device2"},
                ]
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "resources": [
                    "detection1",
                    "detection2",
                    "detection3",
                ]
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "resources": [
                    {"alert_name": "alert1", "tactic_name": "hacking", "technique_name": "phishing"},
                    {"alert_name": "alert2", "tactic_name": "more hacking", "technique_name": "breaking and entering"},
                    {
                        "alert_name": "alert3",
                        "tactic_name": "its a false positive",
                        "technique_name": "looking at hackernews",
                    },
                ]
            },
        ),
    ],
)
@patch(
    "connectors.crowdstrike.connector.utils.AsyncClient.post",
    side_effect=[
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={"access_token": "access_token"},
        ),
    ],
)
async def test_crowdstrike_connector_tools_get_security_alerts_async(
    mocker,
    mocked_fetch_token,
):
    config = CrowdstrikeConnectorConfig(
        id=ConnectorIdEnum.CROWDSTRIKE,
        host="test_host",
        url="https://test_url.com",
        client_id="test_client_id",
        client_secret=StorableSecret.model_validate("test_client_secret", context={"encryption_key": "mock"}),
    )
    target = CrowdstrikeTarget()

    tools = CrowdstrikeConnectorTools(config, target, secrets=CrowdstrikeSecrets(client_secret=SecretStr("a")))

    input_data = GetSecurityAlertsInput.model_validate(
        {
            "hostnames": ["device1.hostname.com", "device2.hostname.com"],
        }
    )
    tool_result = await tools.get_security_alerts_async(input_data)
    assert tool_result.result == [
        {"detection_name": "alert1", "tactic": "hacking", "technique": "phishing"},
        {"detection_name": "alert2", "tactic": "more hacking", "technique": "breaking and entering"},
        {
            "detection_name": "alert3",
            "tactic": "its a false positive",
            "technique": "looking at hackernews",
        },
    ]


def test_format_device_lookup_filter_expression():
    # Test with a single hostname
    hostnames = ["device1.hostname.com"]
    ips = []
    expected = "hostname:['device1.hostname.com']"
    result = CrowdstrikeConnectorTools._format_device_lookup_filter_expression(hostnames, ips)
    assert result == expected

    # Test with multiple hostnames
    hostnames = ["device1.hostname.com", "device2.hostname.com"]
    ips = []
    expected = "hostname:['device1.hostname.com','device2.hostname.com']"
    result = CrowdstrikeConnectorTools._format_device_lookup_filter_expression(hostnames, ips)
    assert result == expected

    # Test with multiple hostnames and IPs
    hostnames = ["device1.hostname.com", "device2.hostname.com"]
    ips = ["10.5.15.95"]
    expected = "(hostname:['device1.hostname.com','device2.hostname.com'] OR local_ip:['10.5.15.95'])"
    result = CrowdstrikeConnectorTools._format_device_lookup_filter_expression(hostnames, ips)
    assert result == expected

    # Test None
    hostnames = []
    ips = []
    expected = None
    result = CrowdstrikeConnectorTools._format_device_lookup_filter_expression(hostnames, ips)
    assert result == expected


@pytest.mark.anyio
@patch(
    "connectors.crowdstrike.connector.tools.AsyncClient.get",
    side_effect=[
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "meta": {
                    "pagination": {
                        "offset": 0,
                    }
                },
                "resources": [
                    {"device_id": "device1"},
                    {"device_id": "device2"},
                ],
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "resources": [
                    {"device_id": "device3"},
                    {"device_id": "device4"},
                ]
            },
        ),
    ],
)
async def test_get_all_device_ids(mocker):
    result = await CrowdstrikeConnectorTools._get_all_device_ids(
        "http://test_url.com", "crowdstrike_access_token", "test_expression"
    )
    assert result == [
        "device1",
        "device2",
        "device3",
        "device4",
    ]
