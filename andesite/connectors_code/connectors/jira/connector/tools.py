from typing import Any
import base64
from connectors.jira.connector.config import JIRAConnectorConfig
from connectors.jira.connector.target import JIRATarget
import httpx
import asyncio
from pydantic import BaseModel

from common.models.connector_id_enum import ConnectorIdEnum
from connectors.jira.connector.secrets import JIRASecrets
from connectors.tools import ConnectorToolsInterface
from common.models.tool import Tool, ToolResult


class GetJIRAProjectsInput(BaseModel):
    """Input model for retrieving JIRA projects. No fields are required."""
    pass


class GetJIRAIssuesInput(BaseModel):
    """Input model for retrieving JIRA issues for a specific project."""
    project_key: str


class JIRAConnectorTools(ConnectorToolsInterface[JIRASecrets]):
    """A collection of tools for interacting with the JIRA API."""

    def __init__(self, config: JIRAConnectorConfig, target: JIRATarget, secrets: JIRASecrets):
        """Initializes the JIRA connector tools with the given configuration and target.

        :param config: The JIRA connector configuration containing url, api_key, and email.
        :param target: The target containing specific project keys (if any).
        """
        self.config = config
        self.target = target
        super().__init__(ConnectorIdEnum.JIRA, target, secrets)

    async def _get_jira_projects_async(self, input: GetJIRAProjectsInput) -> list[dict[str, Any]]:
        """Retrieves a list of JIRA projects, optionally filtering by target project keys.

        :param input: An instance of GetJIRAProjectsInput.
        :return: A ToolResult containing the list of projects.
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.config.url.rstrip('/')}/rest/api/3/project"
            headers = {
                "Authorization": "Basic " + base64.b64encode(f"{self.config.email}:{self._secrets.api_key.get_secret_value()}".encode()).decode()
            }
            response = await client.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            projects: list[dict[str, Any]] = response.json()
            projects = [p for p in projects if p.get("key") in self.target.project_keys]
            return projects

    async def _get_jira_issues_async(self, input: GetJIRAIssuesInput) -> ToolResult:
        """Retrieves a list of JIRA issues for the specified project.

        Implements a retry mechanism in case of rate limiting (HTTP 429).

        :param input: An instance of GetJIRAIssuesInput containing the project key.
        :return: A ToolResult containing the list of issues.
        """
        async with httpx.AsyncClient() as client:
            base_url = self.config.url.rstrip('/')
            jql = f"project={input.project_key}"
            url = f"{base_url}/rest/api/3/search"
            headers = {
                "Authorization": "Basic " + base64.b64encode(f"{self.config.email}:{self._secrets.api_key.get_secret_value()}".encode()).decode()
            }
            params = {"jql": jql}
            retries = 3
            attempt = 0
            response = None
            issues: list[Any] = []
            while attempt < retries:
                response = await client.get(url, params=params, headers=headers, timeout=30)
                if response.status_code == 429:
                    await asyncio.sleep(1)
                    attempt += 1
                    continue
                response.raise_for_status()
                issues = response.json().get("issues", [])
                return ToolResult(result=issues)
            # If retries exhausted, raise an exception
            if response is not None:
                response.raise_for_status()
                issues = response.json().get("issues", [])
            return ToolResult(result=issues)

    def get_tools(self) -> list[Tool]:
        """Returns a list of Tool objects for JIRA operations.

        The returned tools include the ability to list projects and retrieve issues for a project.
        :return: A list of Tool instances.
        """
        tools: list[Tool] = []

        tools.append(
            Tool(
                connector=ConnectorIdEnum.JIRA,
                name="get_jira_projects",
                execute_fn=self._get_jira_projects_async
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.JIRA,
                name="get_jira_issues",
                execute_fn=self._get_jira_issues_async
            )
        )
        return tools
