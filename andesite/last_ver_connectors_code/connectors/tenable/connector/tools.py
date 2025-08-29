import json
from typing import Any, Optional

from common.jsonlogging.jsonlogger import Logging
from common.models.metadata import QueryResultMetadata
from common.models.tool import Tool, ToolResult
from httpx import AsyncClient, HTTPStatusError
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.connector_id_enum import ConnectorIdEnum
from connectors.tenable.connector.config import TenableConnectorConfig
from connectors.tenable.connector.target import TenableTarget
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)

TENABLE_URL = "https://cloud.tenable.com"


class TenableConnectorTools(ConnectorToolsInterface):
    """
    A collection of tools used by agents that query Tenable.
    """

    def __init__(
        self,
        tenable_config: TenableConnectorConfig,
        target: TenableTarget,
        connector_display_name: str,
    ):
        """
        Initializes the tool collection for a specific splunk target.

        :param target: The Tenable target the tools will target.
        """
        self.access_key = tenable_config.access_key
        self.secret_key = tenable_config.secret_key
        super().__init__(ConnectorIdEnum.TENABLE, target=target, connector_display_name=connector_display_name)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="get_asset_filters",
                connector=self._connector_display_name,
                execute_fn=self.get_asset_filters_async,
            )
        )
        tools.append(
            Tool(
                name="get_vulnerability_filters",
                connector=self._connector_display_name,
                execute_fn=self.get_vulnerability_filters_async,
            )
        )
        tools.append(
            Tool(
                name="get_assets",
                connector=self._connector_display_name,
                execute_fn=self.get_assets_async,
            )
        )
        tools.append(
            Tool(
                name="get_asset_info",
                connector=self._connector_display_name,
                execute_fn=self.get_asset_info_async,
            )
        )
        tools.append(
            Tool(
                name="get_asset_vulnerabilities",
                connector=self._connector_display_name,
                execute_fn=self.get_asset_vulnerabilities_async,
            )
        )
        tools.append(
            Tool(
                name="get_vulnerabilities",
                connector=self._connector_display_name,
                execute_fn=self.get_vulnerabilities_async,
            )
        )
        tools.append(
            Tool(
                name="get_vulnerability_info",
                connector=self._connector_display_name,
                execute_fn=self.get_vulnerability_info_async,
            )
        )
        tools.append(
            Tool(
                name="get_vulnerable_assets",
                connector=self._connector_display_name,
                execute_fn=self.get_vulnerable_assets_async,
            )
        )
        tools.append(
            Tool(
                name="get_vulnerability_info_for_specific_asset",
                connector=self._connector_display_name,
                execute_fn=self.get_vulnerability_info_for_specific_asset_async,
            )
        )
        return tools

    @classmethod
    @tracer.start_as_current_span("_get_filters_query_params")
    def _get_filters_query_params(
        cls,
        filters: Optional[list[tuple]] = [],
        filter_type: Optional[str] = None,
    ) -> list[str]:
        query_params: list[str] = []
        if filters:
            for index, filter in enumerate(filters):
                filter_name, filter_quality, filter_value = filter
                query_params.append(f"filter.{index}.filter={filter_name}")
                query_params.append(f"filter.{index}.quality={filter_quality}")
                query_params.append(f"filter.{index}.value={filter_value}")
            if len(filters) > 1 and filter_type:
                query_params.append(f"filter.search_type={filter_type}")
        return query_params

    @classmethod
    @tracer.start_as_current_span("_get_full_url")
    def _get_full_url(cls, path: str, query_params: Optional[list[str]] = None) -> str:
        base_url = f"{TENABLE_URL}/{path}"
        if query_params and len(query_params) > 0:
            return f"{base_url}?{'&'.join(query_params)}"
        return base_url

    @tracer.start_as_current_span("_call_tenable_api")
    async def call_tenable_api(
        self,
        path: str,
        query_params: Optional[list[str]] = None,
        has_filters: bool = False,
    ) ->  tuple[dict[str, Any], QueryResultMetadata]:
        url = TenableConnectorTools._get_full_url(path, query_params)
        async with AsyncClient() as client:
            response = None
            try:
                response = await client.get(
                    url=url,
                    headers={
                        "accept": "application/json",
                        "X-ApiKeys": f"accessKey={self.access_key.get_secret_value()};secretKey={self.secret_key.get_secret_value()}",
                    },
                )
                response.raise_for_status()
            except HTTPStatusError:
                error_message = f"API Error. Response: {response.json() if response else ''}"
                if has_filters:
                    error_message += " Check the filters passed in (call the get filters tools) and try again."
                raise Exception(error_message)

            try:
                response_body: dict[str, Any] = response.json()
            except json.JSONDecodeError:
                response_body = {}
            return response_body, QueryResultMetadata(
                query_format="Tenable API",
                query=url,
                column_headers=[path],
                results=[[json.dumps(response_body)]],
            )

    class GetAssetFiltersInput(BaseModel):
        """
        Lists the filtering, sorting, and pagination capabilities available for assets on tools that support them.
        You should call this function BEFORE get_assets() tool
        """

        pass

    @tracer.start_as_current_span("get_asset_filters_async")
    async def get_asset_filters_async(
        self, input: GetAssetFiltersInput
    ) -> QueryResultMetadata:
        (_, metadata) = await self.call_tenable_api(
            path="filters/workbenches/assets", has_filters=False
        )
        return metadata

    class GetVulnerabilityFiltersInput(BaseModel):
        """
        Returns the filters available for the Vulnerabilities Workbench.
        You should call this function BEFORE any vulnerability-related tool that specifies it needs filters.
        """

        pass

    @tracer.start_as_current_span("get_vulnerability_filters_async")
    async def get_vulnerability_filters_async(
        self, input: GetVulnerabilityFiltersInput
    ) -> QueryResultMetadata:
        (_, metadata) = await self.call_tenable_api(
            path="filters/workbenches/vulnerabilities", has_filters=False
        )
        return metadata

    class GetAssetsInput(BaseModel):
        """
        The assets workbench allows for filtering and interactively querying the
        asset data stored within Tenable Vulnerability Management. There are a wide variety of
        filtering options available to find specific pieces of data. This tool will return a maximum of 5000 vulnerabilities.
        You cannot handle that much data at once, so you should use filters to narrow down the results.
        If more than 100 results are returned, only the first 100 will be shown.
        You will have to use filters to narrow down the results.
        If you are asked about a specific asset, try to use this tool to grab the asset ID and use that in other tools.

        :example:
            Query for all of the asset information:

            >>> get_assets()

        :example:
            Query for just the Windows assets:

            >>> get_assets(filters=[("operating_system", "match", "Windows")])
        """

        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_assets_async")
    async def get_assets_async(
        self,
        input: GetAssetsInput,
    ) -> ToolResult:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-assets
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        query_params.append("all_fields=default")
        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        response, metadata = await self.call_tenable_api(
            path="workbenches/assets", query_params=query_params, has_filters=True
        )
        additional_context = None
        if response.get("total", 0) > 100:
            if "assets" in response and isinstance(response["assets"], list):
                response["assets"] = response["assets"][:100]
                metadata.results = [[json.dumps(response)]]
                additional_context = "Only the first 100 results are shown. Narrow down your query."
        return ToolResult(
            result=metadata,
            additional_context=additional_context
        )

    class GetAssetInfoInput(BaseModel):
        """
        Query for the information for a specific asset within the asset workbench.

        :example:
            Retrieve information for a specific asset:

            >>> asset = get_asset_info("00000000-0000-0000-0000-000000000000")
        """

        id: str = Field(description="The unique identifier (UUID) of the asset.")
        all_fields: bool = Field(
            description="If set to `True` (default), an expanded dataset is returned as defined by the API documentation.",
            default=False,
        )

    @tracer.start_as_current_span("get_asset_info_async")
    async def get_asset_info_async(
        self, input: GetAssetInfoInput
    ) -> QueryResultMetadata:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-asset-info
        all_fields = input.all_fields
        id = input.id

        query_params: list[str] = []
        if all_fields:
            query_params.append("all_fields=full")

        _, metadata = await self.call_tenable_api(
            path=f"workbenches/assets/{id}/info",
            query_params=query_params,
            has_filters=False,
        )
        return metadata

    class GetAssetVulnerabilitiesInput(BaseModel):
        """
        Return the vulnerabilities for a specific asset. This tool will return a maximum of 5000 vulnerabilities.
        You cannot handle that much data at once, so you should use filters to narrow down the results.
        If more than 100 results are returned, only the first 100 will be shown.
        You will have to use filters to narrow down the results.

        :example:
            Retrieve vulnerabilities for a specific asset:

            >>> asset_id = "00000000-0000-0000-0000-000000000000"
            >>> get_asset_vulnerabilities(asset_id)
        """

        id: str = Field(description="The unique identifier of the asset to query.")
        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_asset_vulnerabilities_async")
    async def get_asset_vulnerabilities_async(
        self,
        input: GetAssetVulnerabilitiesInput,
    ) -> ToolResult:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-asset-vulnerabilities
        id = input.id
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        response, metadata = await self.call_tenable_api(
            path=f"workbenches/assets/{id}/vulnerabilities",
            query_params=query_params,
            has_filters=True,
        )
        additional_context = None
        if response.get("total_vulnerability_count", 0) > 100:
            if "vulnerabilities" in response and isinstance(
                response["vulnerabilities"], list
            ):
                response["vulnerabilities"] = response["vulnerabilities"][:100]
                metadata.results = [
                    [json.dumps(response)]
                ]
                additional_context = "Only the first 100 results are shown. Narrow down your query."
        return ToolResult(
            result=metadata,
            additional_context=additional_context
        )

    class GetVulnerabilitiesInput(BaseModel):
        """
        The vulnerability workbench allows for filtering and interactively querying the vulnerability data
        stored within Tenable Vulnerability Management. There are a wide variety of filtering options
        available to find specific pieces of data. This tool will return a maximum of 5000 vulnerabilities.
        You cannot handle that much data at once, so you should use filters to narrow down the results.
        If more than 100 results are returned, only the first 100 will be shown.
        You will have to use filters to narrow down the results.

        :example:
            Query for all of the vulnerability information:

            >>> get_vulnerabilities()

        :example:
            Query for just the critical vulnerabilities:

            >>> get_vulnerabilities(filters=[("severity", "eq", "critical")])
        """

        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_vulnerabilities_async")
    async def get_vulnerabilities_async(
        self,
        input: GetVulnerabilitiesInput,
    ) -> ToolResult:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-vulnerabilities
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        response, metadata = await self.call_tenable_api(
            path="workbenches/vulnerabilities",
            query_params=query_params,
            has_filters=True,
        )
        additional_context = None
        if response.get("total_vulnerability_count", 0) > 100:
            if "vulnerabilities" in response and isinstance(
                response["vulnerabilities"], list
            ):
                response["vulnerabilities"] = response["vulnerabilities"][:100]
                metadata.results = [[json.dumps(response)]]
                additional_context = "Only the first 100 results are shown. Narrow down your query."
        return ToolResult(
            result=metadata,
            additional_context=additional_context
        )

    class GetVulnerabilityInfoInput(BaseModel):
        """
        Retrieve the vulnerability information for a specific vulnerability.

        :example:
            Retrieve information for a specific vulnerability:

            >>> get_vulnerability_info(19506)
        """

        plugin_id: int = Field(
            description="The ID of the plugin. You can find the plugin ID by examining the output of get_vulnerabilities tool."
        )
        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_vulnerability_info_async")
    async def get_vulnerability_info_async(
        self,
        input: GetVulnerabilityInfoInput,
    ) -> QueryResultMetadata:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-vulnerability-info
        plugin_id = input.plugin_id
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        _, metadata = await self.call_tenable_api(
            path=f"workbenches/vulnerabilities/{plugin_id}/info",
            query_params=query_params,
            has_filters=True,
        )
        return metadata

    class GetVulnerableAssetsInput(BaseModel):
        """
        Retrieve assets based on the vulnerability data. This tool will return a maximum of 5000 vulnerabilities.
        You cannot handle that much data at once, so you should use filters to narrow down the results.
        If more than 100 results are returned, only the first 100 will be shown.
        You will have to use filters to narrow down the results.

        :example:
            Retrieve assets based on vulnerabilities:

            >>> vuln_assets():
        """

        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_vulnerable_assets_async")
    async def get_vulnerable_assets_async(
        self,
        input: GetVulnerableAssetsInput,
    ) -> ToolResult:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-assets-vulnerabilities
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        response, metadata = await self.call_tenable_api(
            path="workbenches/assets/vulnerabilities",
            query_params=query_params,
            has_filters=True,
        )

        additional_context = None
        if response.get("total_asset_count", 0) > 100:
            if "assets" in response and isinstance(response["assets"], list):
                response["assets"] = response["assets"][:100]
                metadata.results = [
                    [
                        json.dumps(response),
                    ]
                ]
                additional_context = "Only the first 100 results are shown. Narrow down your query."
        return ToolResult(
            result=metadata,
            additional_context=additional_context
        )

    class GetVulnerabilityInfoForSpecificAssetInput(BaseModel):
        """
        Retrieve the vulnerability information for a specific plugin on a specific asset within Tenable Vulnerability Management.

        :example:
            Retrieve vulnerability information for a specific plugin on an asset:

            >>> asset_id = "00000000-0000-0000-0000-000000000000"
            >>> get_vulnerability_info_for_specific_asset(asset_id, 19506)
        """

        uuid: str = Field(description="The unique identifier of the asset to query.")
        plugin_id: int = Field(description="The unique identifier of the plugin.")
        age: Optional[int] = Field(
            description="The number of days of data prior to and including today that should be returned.",
            default=None,
        )
        filters: Optional[list[tuple]] = Field(
            description="A list of tuples (max amount 10 filters) detailing the filters to be applied to the response data.",
            default=[],
        )
        filter_type: Optional[str] = Field(
            description="Defines whether the filters are exclusive (`and`: this AND this AND this) or inclusive (`or`: this OR this OR this). Valid values are `and` and `or`. Defaults to `and`. Only include this if passing in multiple filters.",
            default=None,
        )

    @tracer.start_as_current_span("get_vulnerability_info_for_specific_asset_async")
    async def get_vulnerability_info_for_specific_asset_async(
        self,
        input: GetVulnerabilityInfoForSpecificAssetInput,
    ) -> QueryResultMetadata:
        # Based on API docs found here: https://developer.tenable.com/reference/workbenches-asset-vulnerability-info
        uuid = input.uuid
        plugin_id = input.plugin_id
        age = input.age
        filters = input.filters
        filter_type = input.filter_type

        query_params: list[str] = []

        if age:
            query_params.append(f"date_range={age}")
        query_params.extend(
            TenableConnectorTools._get_filters_query_params(filters, filter_type)
        )

        _, metadata = await self.call_tenable_api(
            path=f"workbenches/assets/{uuid}/vulnerabilities/{plugin_id}/info",
            query_params=query_params,
            has_filters=True,
        )
        return metadata
