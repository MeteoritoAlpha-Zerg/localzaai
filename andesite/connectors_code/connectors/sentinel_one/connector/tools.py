import json
from enum import Enum
from typing import Any, Literal, Optional

import httpx
from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool, ToolResult
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.sentinel_one.connector.config import SentinelOneConnectorConfig
from connectors.sentinel_one.connector.target import SentinelOneTarget
from connectors.sentinel_one.connector.secrets import SentinelOneSecrets
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)


class SentinelOneResource(Enum):
    ENDPOINT = "/web/api/v2.1/xdr/assets/surface/endpoint"
    THREAT = "/web/api/v2.1/threats"
    ALERTS = "/web/api/v2.1/cloud-detection/alerts"

    def __init__(self, api_path: str):
        self.api_path = api_path

class NoNoneEncoder(json.JSONEncoder):
    def encode(self, obj):
        return super().encode(self._remove_none(obj))

    def _remove_none(self, obj):
        if isinstance(obj, dict):
            return {k: self._remove_none(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._remove_none(item) for item in obj if item is not None]
        return obj

class SentinelOneConnectorException(Exception):
    pass

RESULT_LIMIT = 10

class SentinelOneConnectorTools(ConnectorToolsInterface[SentinelOneSecrets]):
    QUERY_RESULT_METADATA_FORMAT = "SentinelOne API"

    def __init__(self, config: SentinelOneConnectorConfig, secrets: SentinelOneSecrets):
        super().__init__(connector=ConnectorIdEnum.SENTINEL_ONE, target=SentinelOneTarget(), secrets=secrets)
        self.api_endpoint = config.api_endpoint
        self.headers = {"Authorization": f"ApiToken {self._secrets.token.get_secret_value()}"}

    class GetResourceInput(BaseModel):
        pass


    class GetEndpointsAgentInfoInput(GetResourceInput):
        """
        This tool provides information about agents installed on SentinelOne endpoints.
        """
        agentAgentVersion: Optional[str] = Field(
            default=None,
            description="Filter on specific agent version. Agent versions are typically numbers separated by dots.",
        )
        agentAgentVersion__contains: Optional[str] = Field(
            default=None,
            description="Filter on agent versions containing certain text.",
        )
        agentAgentVersion__nin: Optional[str] = Field(
            default=None,
            description="Exclude agents with a specific version.",
        )
        agentConsoleConnectivity: Optional[str] = Field(
            default=None,
            description="Filter on whether the agent is connected to the console, e.g. 'true'.",
        )
        agentDvConnectivity: Optional[str] = Field(
            default=None,
            description="Filter endpoints on event search connectivity",
        )
        agentDvConnectivity__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints that do not have a specific event search connectivity value",
        )
        agentHealthStatus: Optional[str] = Field(
            default=None,
            description="Filter endpoints by an agent health status, such as 'Healthy' or 'Infected'.",
        )
        agentHealthStatus__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints by an agent health status, such as 'Healthy' or 'Infected'.",
        )
        agentLastLoggedInUser__contains: Optional[str] = Field(
            default=None,
            description="Filter agents by user who was last logged in",
        )
        agentNetworkStatus: Optional[str] = Field(
            default=None,
            description="Filter agents by network status, e.g. 'connected'",
        )
        agentNetworkStatus__nin: Optional[str] = Field(
            default=None,
            description="Exclude agents by network status, e.g. 'connected'",
        )
        agentUninstalled: Optional[str] = Field(
            default=None,
            description="Filter agents on their uninstalled status, such as 'true' or 'false'",
        )
        agentUuid: Optional[str] = Field(
            default=None,
            description="Filter agents on their UUID",
        )
        agentUuid__contains: Optional[str] = Field(
            default=None,
            description="Filter agents on UUID that contains certain text.",
        )
        countOnly: Optional[Literal['true']] = Field(
            default=None,
            description="Set this value to true if the user is only asking for a count of items.",
        )

    class GetEndpointsInput(GetResourceInput):
        """
        Endpoints are assets monitored by SentinelOne. This tool does not provide information about agents installed on the host.

        In the response, the field "applications" will tell you what is installed on that endpoint.
        """
        assetEnvironment: Optional[str] = Field(
            default=None,
            description="Filter endpoints the asset environment, such as 'AWS, 'Azure', 'GCP', 'Active Directory'",
        )
        assetEnvironment__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints the asset environment, such as 'AWS, 'Azure', 'GCP', 'Active Directory'",
        )
        assetStatus: Optional[Literal['Active', 'Inactive']] = Field(
            default=None,
            description="Filter assets based on a status.",
        )
        applicationName: Optional[str] = Field(
            default=None,
            description="Filter endpoints by an application installed.",
        )
        internalIps__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints by an internal IP address.",
        )
        id__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints where the ID contains specific text.",
        )
        ipAddress__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints by a public IP address.",
        )
        countOnly: Optional[Literal['true']] = Field(
            default=None,
            description="Set this value to true if the user is only asking for a count of items.",
        )
        cpu__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints by their CPU type.",
        )
        names: Optional[str] = Field(
            default=None,
            description="Filter endpoints by a specific name.",
        )
        name__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints that contain specific text in their name.",
        )
        names__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints by their name",
        )
        osFamily: Optional[str] = Field(
            default=None,
            description="Filter endpoints by operating system family. This is case sensitive.",
        )
        osFamily__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints with a specific operating system family. This is case sensitive.",
        )
        osVersion__contains: Optional[str] = Field(
            default=None,
            description="Search for endpoints with a operating system version",
        )
        osVersion__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints with a specific operating system version.",
        )
        osNameVersion: Optional[str] = Field(
            default=None,
            description="Filter endpoints with a specific operating system name version.",
        )
        resourceType: Optional[str] = Field(
            default=None,
            description="Filter endpoints with a specific resource type, such as 'AWS EC2 Instance'. This is case sensitive.",
        )
        resourceType__contains: Optional[str] = Field(
            default=None,
            description="Filter endpoints with a resource type that contains certain text.",
        )
        resourceType__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints with a specific resource type, such as 'AWS EC2 Instance'. This is case sensitive.",
        )
        subCategory: Optional[str] = Field(
            default=None,
            description="Filter endpoints with a specific subCategory type, such as 'Laptop' or 'Desktop'.",
        )
        subCategory__nin: Optional[str] = Field(
            default=None,
            description="Exclude endpoints with a specific subCategory type, such as 'Laptop' or 'Desktop'.",
        )
        tool_application_limit: Optional[int] = Field(
            default=0,
            ge=0,
            le=30,
            description="Determines how many applications to include for each endpoint in the result.",
            exclude=True
        )


    class GetThreatsInput(GetResourceInput):
        """
        Threats are generated by SentinelOne when:
            - The SentinelOne Agent engines detect suspicious or malicious activity.
            - A user marks events as suspicious or malicious.
        SentinelOne maintains a list of specific threats to monitor. Threats are also generated based on the policy set for the organization.
        To understand what caused a threat, look at the "indicators" field in the response.
        """

        agentMachineTypes: Optional[Literal["desktop", "laptop", "server", "storage"]] = Field(
            default=None,
            description="Filter the threats by an agent machine type.",
        )
        agentMachineTypesNin: Optional[Literal["desktop", "laptop", "server", "storage"]] = Field(
            default=None,
            description="Exclude threats by an agent machine type.",
        )
        commandLineArguments__contains: Optional[str] = Field(
            default=None,
            description="Filter the threats by a command or process.",
        )
        computerName__contains: Optional[str] = Field(
            default=None,
            description="Filter the threats with computer names containing certain text.",
        )
        confidenceLevels: Optional[Literal["malicious", "suspicious"]] = Field(
            default=None,
            description="Filter the threats by a confidence status such as 'malicious' or 'suspicious'.",
        )
        countOnly: Optional[Literal['true']] = Field(
            default=None,
            description="Set this value to true if the user is only asking for a count of items.",
        )
        classifications: Optional[str] = Field(
            default=None,
            description="Filter threats by a type of classification, such as 'Malware' or 'Ransomware.",
        )
        createdAt__gte: Optional[str] = Field(
            default=None,
            description="Filter threats that reported on and after a certain date, such as 2018-02-27T04:49:26.257525Z",
        )
        createdAt__lte: Optional[str] = Field(
            default=None,
            description="Filter threats that reported on and before a certain date, such as 2018-02-27T04:49:26.257525Z",
        )
        mitigationStatuses: Optional[Literal["marked_as_benign", "mitigated", "not_mitigated"]] = Field(
            default=None,
            description="Filter the threats by a mitigation status.",
        )
        incidentStatuses: Optional[Literal["in_progress", "resolved", "unresolved"]] = Field(
            default=None,
            description="Filter threats by their resolution status, such as 'in_progress', 'resolved', or 'unresolved'.",
        )


    class GetAlertsInput(GetResourceInput):
        """
        Alerts are generated by SentinelOne based on custom rules the user has configured.
        The "rule_info" field in the response will denote which rule triggered the alert.
        """

        analystVerdict: Optional[Literal["TRUE_POSITIVE", "SUSPICIOUS", "FALSE_POSITIVE", "UNDEFINED"]] = Field(
            default=None,
            description="Filter alerts by analyst verdicts.",
        )
        countOnly: Optional[Literal['true']] = Field(
            default=None,
            description="Set this value to true if the user is only asking for a count of items.",
        )
        incidentStatus: Optional[Literal["IN_PROGRESS", "RESOLVED", "UNRESOLVED"]] = Field(
            default=None,
            description="Filter alerts by their incident status.",
        )
        machineType: Optional[str] = Field(
            default=None,
            description="Filter alerts by machine type, such as 'laptop' or 'server'.",
        )
        osType: Optional[Literal["linux", "macos", "windows"]] = Field(
            default=None,
            description="Filter alerts by operating systems.",
        )
        query: Optional[str] = Field(
            default=None,
            description="You should use this parameter to perform free-text searches of information that cannot be filtered on the other parameters.",
        )
        createdAt__gte: Optional[str] = Field(
            default=None,
            description="Filter alerts that reported on and after a certain date, such as 2018-02-27T04:49:26.257525Z",
        )
        createdAt__lte: Optional[str] = Field(
            default=None,
            description="Filter alerts that reported on and before a certain date, such as 2018-02-27T04:49:26.257525Z",
        )
        ruleName__contains: Optional[str] = Field(
            default=None,
            description="Filter alerts triggered by certain rule names.",
        )
        severity: Optional[Literal["Critical", "High", "Low", "Medium"]] = Field(
            default=None,
            description="Filter alerts by severity level.",
        )
        sourceProcessFilePath__contains: Optional[str] = Field(
            default=None,
            description="Filter alerts that contain a source process file path.",
        )
        sourceProcessName__contains: Optional[str] = Field(
            default=None,
            description="Filter alerts that contain a source process name.",
        )

    def get_tools(self) -> list[Tool]:
        return [
            Tool(connector=ConnectorIdEnum.SENTINEL_ONE, name="get_endpoints", execute_fn=self.get_endpoints_async),
            Tool(connector=ConnectorIdEnum.SENTINEL_ONE, name="get_endpoints_agent_info", execute_fn=self.get_endpoints_agent_info_async),
            Tool(connector=ConnectorIdEnum.SENTINEL_ONE, name="get_threats", execute_fn=self.get_threats_async),
            Tool(connector=ConnectorIdEnum.SENTINEL_ONE, name="get_alerts", execute_fn=self.get_alerts_async),
        ]

    async def get_endpoints_agent_info_async(self, input: GetEndpointsAgentInfoInput) -> ToolResult:
        api_request: dict[str, Any] = self.generate_params(input)
        response_json = await self._get_s1_resource_async(SentinelOneResource.ENDPOINT, api_request)
        for endpoint in response_json["data"]:
            if "applications" in endpoint:
                del endpoint["applications"]
        return ToolResult(
            result=json.dumps(response_json),
            additional_context="This tool can only return the first page of results",
        )

    async def get_endpoints_async(self, input: GetEndpointsInput) -> ToolResult:
        api_request: dict[str, Any] = self.generate_params(input)
        response_json = await self._get_s1_resource_async(SentinelOneResource.ENDPOINT, api_request)
        for endpoint in response_json["data"]:
            if "applications" in endpoint:
                if input.tool_application_limit == 0:
                    del endpoint["applications"]
                else:
                    endpoint["applications"] = endpoint["applications"][:input.tool_application_limit]
            if "agent" in endpoint:
                del endpoint["agent"]

        if input.tool_application_limit == 0:
            return ToolResult(
                result=json.dumps(response_json),
                additional_context="This tool can only return the first page of results and by default does not include application information.",
            )
        return ToolResult(
            result=json.dumps(response_json),
            additional_context=f"This tool can only return the first page of results and up to {input.tool_application_limit} applications per result.",
        )

    async def get_threats_async(self, input: GetThreatsInput) -> ToolResult:
        api_request: dict[str, Any] = self.generate_params(input)
        response_json = await self._get_s1_resource_async(SentinelOneResource.THREAT, api_request)
        return ToolResult(result=json.dumps(response_json, cls=NoNoneEncoder), additional_context=None)

    async def get_alerts_async(self, input: GetAlertsInput) -> ToolResult:
        api_request: dict[str, Any] = self.generate_params(input)
        response_json = await self._get_s1_resource_async(SentinelOneResource.ALERTS, api_request)
        return ToolResult(result=json.dumps(response_json, cls=NoNoneEncoder), additional_context=None)

    @tracer.start_as_current_span("get_s1_resource_async")
    async def _get_s1_resource_async(self, resource: SentinelOneResource, api_request: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{self.api_endpoint}{resource.api_path}", headers=self.headers, **api_request
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError:
                logger().exception(f"An error occurred while requesting {resource.name}.")
                raise SentinelOneConnectorException("Unable to connect to SentinelOne")  # noqa: B904
            except httpx.HTTPStatusError as e:
                logger().exception(f"Error response {e.response.status_code} while requesting {resource.name}.")
                if e.response.status_code == 401:
                    raise SentinelOneConnectorException("SentinelOne API token is not set or unauthorized")  # noqa: B904
                raise SentinelOneConnectorException(
                    f"SentinelOne returned an HTTP error {e.response.status_code}, {e.response.text}"
                ) from None
            except Exception:
                logger().exception("Unknown error from S1")
                raise SentinelOneConnectorException("Unknown error from SentinelOne")  # noqa: B904


    def generate_params(self, input: GetResourceInput) -> dict[str, dict[str, str]]:
        params = input.model_dump(exclude_unset=True, exclude_defaults=True)
        params["limit"] = RESULT_LIMIT
        return {"params": params}
