"""
Crowdstrike Connector Tools Implementation.
Defines tools for querying security alerts from Crowdstrike.

Based on documentation found here: https://www.falconpy.io/Operations/Operations-Overview.html
"""

import asyncio
from typing import Any

from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool, ToolResult
from httpx import AsyncClient, HTTPStatusError
from opentelemetry import trace
from pydantic import BaseModel, Field, model_validator

from connectors.crowdstrike.connector.config import CrowdstrikeConnectorConfig
from connectors.crowdstrike.connector.target import CrowdstrikeTarget
from connectors.crowdstrike.connector.secrets import CrowdstrikeSecrets
from connectors.crowdstrike.connector.utils import fetch_token
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)


class GetSecurityAlertsInput(BaseModel):
    """
    Input model for retrieving security alerts from specific Crowdstrike endpoints.
    Either one or both of the fields must be provided.
    Results are the detections/alerts in the union of the input hostnames and ips.
    """

    hostnames: list[str] = Field(default_factory=list, description="List of hostnames to query for security alerts.")
    ips: list[str] = Field(default_factory=list, description="List of IP addresses to query for security alerts.")

    @model_validator(mode="after")
    def validate_input(self) -> "GetSecurityAlertsInput":
        """
        Validates that at least one of hostnames or ips is provided.
        """
        if not self.hostnames and not self.ips:
            raise ValueError("At least one of hostnames or ips must be provided.")
        return self


class CrowdstrikeConnectorTools(ConnectorToolsInterface[CrowdstrikeSecrets]):
    """
    A collection of tools used by agents that query Crowdstrike.
    """

    def __init__(
        self,
        config: CrowdstrikeConnectorConfig,
        target: CrowdstrikeTarget,
        secrets: CrowdstrikeSecrets,
    ):
        """
        Initializes the Crowdstrike tools.

        :param config: Connector configuration with authentication details.
        :param target: Crowdstrike target specifying endpoints to query.
        """
        self.config = config
        super().__init__(ConnectorIdEnum.CROWDSTRIKE, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        """
        Returns a list of tools available for the Crowdstrike connector.
        """
        return [
            Tool(
                connector=ConnectorIdEnum.CROWDSTRIKE,
                name="get_security_alerts",
                execute_fn=self.get_security_alerts_async,
            )
        ]

    async def get_security_alerts_async(self, input: GetSecurityAlertsInput) -> ToolResult:
        """
        Retrieves security alerts for the specified hostname or ip.

        :param endpoint_id: The ID of the Crowdstrike endpoint.
        :return: ToolResult containing a list of alert dictionaries.
        """
        base_url = self.config.url or f"https://{self.config.host}"
        timeout = self.config.api_request_timeout
        max_retries = self.config.api_request_timeout if False else self.config.api_request_timeout
        max_retries = self.config.api_max_retries

        # Obtain OAuth2 token
        token = await fetch_token(self.config, self._secrets)
        headers = {"Authorization": f"Bearer {token}"}

        filter_expression = CrowdstrikeConnectorTools._format_device_lookup_filter_expression(
            hostnames=input.hostnames, ips=input.ips
        )
        device_ids = await CrowdstrikeConnectorTools._get_all_device_ids(base_url, token, filter_expression)
        formatted_device_ids = ",".join([f"'{device_id}'" for device_id in device_ids])

        # Step 1: Query detection IDs
        detection_ids: list[str] = []
        detect_url = f"{base_url}/detects/queries/detects/v1?filter=device_id:[{formatted_device_ids}]&limit=100"
        for attempt in range(max_retries):
            async with AsyncClient(timeout=timeout) as client:
                try:
                    resp = await client.get(detect_url, headers=headers)
                    resp.raise_for_status()
                    response_json = resp.json()
                    detection_ids = response_json.get("resources", []) or []
                    break
                except HTTPStatusError as e:
                    if resp.status_code == 429:
                        await asyncio.sleep(1)
                        continue
                    raise e

        # Step 2: Fallback to alerts if no detections
        alert_ids: list[str] = []
        if not detection_ids:
            alerts_url = f"{base_url}/alerts/queries/alerts/v1?filter=device_id:[{formatted_device_ids}]&limit=100"
            for attempt in range(max_retries):
                async with AsyncClient(timeout=timeout) as client:
                    try:
                        resp = await client.get(alerts_url, headers=headers)
                        resp.raise_for_status()
                        response_json = resp.json()
                        alert_ids = response_json.get("resources", []) or []
                        break
                    except HTTPStatusError as e:
                        if resp.status_code == 429:
                            await asyncio.sleep(1)
                            continue
                        raise e

        ids_to_fetch = detection_ids or alert_ids
        # If no IDs found, return a placeholder alert
        if not ids_to_fetch:
            placeholder = {
                "id": "",
                "device_id": "",
                "severity": "",
                "status": "",
                "created_timestamp": "",
                "detection_name": "",
                "tactic": "",
                "technique": "",
            }
            return ToolResult(result=[placeholder])

        # Determine entity endpoint path
        if detection_ids:
            entity_path = "detects/entities/detects/v1"
        else:
            entity_path = "alerts/entities/alerts/v1"
        ids_param = ",".join(ids_to_fetch)

        details_url = f"{base_url}/{entity_path}?ids={ids_param}"

        # Step 3: Fetch details
        alerts_data: list[Any] = []
        for attempt in range(max_retries):
            async with AsyncClient(timeout=timeout) as client:
                try:
                    resp = await client.get(details_url, headers=headers)
                    resp.raise_for_status()
                    alerts_data = resp.json().get("resources", []) or []
                    break
                except HTTPStatusError as e:
                    if resp.status_code == 429:
                        await asyncio.sleep(1)
                        continue
                    raise e

        # Normalize fields for consistency
        normalized_alerts: list[Any] = []
        for alert in alerts_data:
            alert_data = dict(alert)
            if "alert_name" in alert_data:
                alert_data["detection_name"] = alert_data.pop("alert_name")
            elif "name" in alert_data and "detection_name" not in alert_data:
                alert_data["detection_name"] = alert_data.get("name")
            if "tactic_name" in alert_data:
                alert_data["tactic"] = alert_data.pop("tactic_name")
            if "technique_name" in alert_data:
                alert_data["technique"] = alert_data.pop("technique_name")
            normalized_alerts.append(alert_data)

        # If no alerts after normalization, return placeholder
        if not normalized_alerts:
            placeholder = {
                "id": "",
                "device_id": "",
                "severity": "",
                "status": "",
                "created_timestamp": "",
                "detection_name": "",
                "tactic": "",
                "technique": "",
            }
            return ToolResult(result=[placeholder])

        return ToolResult(result=normalized_alerts)

    @staticmethod
    def _format_device_lookup_filter_expression(hostnames: list[str], ips: list[str]) -> str | None:
        """
        Helper function to get device IDs based on hostnames and IPs.
        Note: This is a hack to get an MVP. We don't want to be in the position of mediating all FQL queries between the agent and Crowdstrike.

        Returns a filter expression that can be used to query devices.
        """

        if hostnames:
            formatted_hostnames = ",".join([f"'{h}'" for h in hostnames])
            hostname_filter = f"hostname:[{formatted_hostnames}]"

        if ips:
            formatted_ips = ",".join([f"'{ip}'" for ip in ips])
            local_ip_filter = f"local_ip:[{formatted_ips}]"

        if hostnames and ips:
            return f"({hostname_filter} OR {local_ip_filter})"
        if hostnames and not ips:
            return f"{hostname_filter}"
        if ips and not hostnames:
            return f"{local_ip_filter}"
        return None

    @staticmethod
    async def _get_all_device_ids(base_url: str, token: str, filter_expression: str | None) -> list[str]:
        """
        Fetch all device IDs by paginating over results.
        """
        api_route = "devices/queries/devices-scroll/v1"
        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, Any] = {"limit": 100}

        if filter_expression:
            params["filter"] = filter_expression

        async with AsyncClient() as client:
            device_ids = []

            response = await client.get(f"{base_url}/{api_route}", headers=headers, params=params)
            response.raise_for_status()
            body = response.json()
            device_ids += [resource["device_id"] for resource in body.get("resources", [])]
            offset = body.get("meta", {}).get("pagination", {}).get("offset", -1)

            while offset + 1:
                response = await client.get(
                    f"{base_url}/{api_route}", headers=headers, params={"offset": offset, "limit": 100}
                )
                response.raise_for_status()
                body = response.json()

                if not body.get("resources"):
                    break

                device_ids += [resource["device_id"] for resource in body.get("resources", [])]
                offset = body.get("meta", {}).get("pagination", {}).get("offset", -1)

        return device_ids
