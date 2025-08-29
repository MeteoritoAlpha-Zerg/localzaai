import asyncio
import base64
from typing import Any

import httpx
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool, ToolResult
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.confluence.connector.config import ConfluenceConnectorConfig
from connectors.confluence.connector.target import ConfluenceTarget
from connectors.confluence.connector.secrets import ConfluenceSecrets
from connectors.tools import ConnectorToolsInterface


async def make_request_with_retry(url: str, auth: tuple[Any, ...], params: dict[Any, Any], timeout: int, max_retries: int):
    """Helper function to make an HTTP GET request with retry logic for rate limiting."""
    retries = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, auth=auth, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429 and retries < max_retries:
                await asyncio.sleep(2**retries)
                retries += 1
                continue
            raise


class ConfluenceConnectorTools(ConnectorToolsInterface[ConfluenceSecrets]):
    """A collection of tools for interacting with Confluence APIs."""

    def __init__(self, target: ConfluenceTarget, config: ConfluenceConnectorConfig, secrets: ConfluenceSecrets):
        """
        Initialize the Confluence connector tools.
        :param target: The Confluence query target (ConfluenceTarget) instance specifying space keys.
        :param config: The ConfluenceConnectorConfig with configuration details.
        """
        self.target = target
        self.config = config
        super().__init__(ConnectorIdEnum.CONFLUENCE, target, secrets)

    def get_tools(self) -> list[Tool]:
        """
        Returns a list of tools available for the Confluence connector.
        """
        tools: list[Tool] = []
        tools.append(Tool(connector=ConnectorIdEnum.CONFLUENCE, name="get_confluence_spaces", execute_fn=self.get_confluence_spaces_async))
        tools.append(Tool(connector=ConnectorIdEnum.CONFLUENCE, name="get_confluence_pages", execute_fn=self.get_confluence_pages_async))
        tools.append(Tool(connector=ConnectorIdEnum.CONFLUENCE, name="get_confluence_page_content", execute_fn=self.get_confluence_page_content_async))
        return tools

    class GetConfluenceSpacesInput(BaseModel):
        """Input model for retrieving Confluence spaces. No input is required."""

        pass

    @trace.get_tracer(__name__).start_as_current_span("get_confluence_spaces_async")
    async def get_confluence_spaces_async(self, input: GetConfluenceSpacesInput) -> ToolResult:
        """
        Retrieves a list of Confluence spaces using the Confluence REST API.
        Calls GET {config.url}/rest/api/space with basic authentication and returns the spaces.
        If the tool's target has specified space_keys, then only return spaces whose key matches those in target.space_keys.
        """
        url = f"{self.config.url.rstrip('/')}/rest/api/space"
        auth = (self.config.email, self._secrets.api_key.get_secret_value())
        params = {"limit": 50}
        data = await make_request_with_retry(
            url, auth, params, self.config.api_request_timeout, self.config.api_max_retries
        )
        spaces = data.get("results", [])
        if self.target.space_keys:
            spaces = [space for space in spaces if space.get("key") in self.target.space_keys]
        return ToolResult(result=spaces)

    class GetConfluencePagesInput(BaseModel):
        """Input model for retrieving Confluence pages."""

        space_key: str = Field(..., description="The key of the Confluence space to retrieve pages from.")

    @trace.get_tracer(__name__).start_as_current_span("get_confluence_pages_async")
    async def get_confluence_pages_async(self, input: GetConfluencePagesInput) -> ToolResult:
        """
        Retrieves a list of Confluence pages for a specified space using the Confluence REST API.
        Calls GET {config.url}/rest/api/content with query parameters spaceKey and expand=body.storage.
        """
        url = f"{self.config.url.rstrip('/')}/rest/api/content"
        auth = (self.config.email, self._secrets.api_key.get_secret_value())
        params: dict[str, Any] = {"spaceKey": input.space_key, "expand": "body.storage", "limit": 50}
        data = await make_request_with_retry(
            url, auth, params, self.config.api_request_timeout, self.config.api_max_retries
        )
        pages = data.get("results", [])
        return ToolResult(result=pages)

    class GetConfluencePageContentInput(BaseModel):
        """Input model for retrieving a specific Confluence page content."""

        page_id: str = Field(..., description="ID of the Confluence page")

    async def get_confluence_page_content_async(self, input: GetConfluencePageContentInput) -> ToolResult:
        """Retrieves the content of a specific Confluence page."""
        page_id = input.page_id
        if not page_id:
            return ToolResult(result="Error: 'page_id' parameter is required")
        url = f"{self.config.url.rstrip('/')}/rest/api/content/{page_id}?expand=body.storage"
        try:
            credentials = f"{self.config.email}:{self._secrets.api_key.get_secret_value()}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers = {"Authorization": f"Basic {encoded}"}
            async with httpx.AsyncClient(timeout=self.config.api_request_timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data.get("body", {}).get("storage", {}).get("value", "")
                return ToolResult(result=content)
        except Exception as e:
            return ToolResult(result=str(e))
