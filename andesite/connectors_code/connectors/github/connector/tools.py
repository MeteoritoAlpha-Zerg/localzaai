import asyncio

import httpx
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool, ToolResult
from pydantic import BaseModel, Field

from connectors.github.connector.config import GithubConnectorConfig
from connectors.github.connector.target import GithubTarget
from connectors.github.connector.secrets import GithubSecrets
from connectors.tools import ConnectorToolsInterface


class GetGithubRepositoriesInput(BaseModel):
    """Input model for retrieving GitHub repositories. No parameters are required."""

    pass


class GetGithubIssuesInput(BaseModel):
    """Input model for retrieving GitHub issues for a repository."""

    repository_id: str = Field(..., description="The ID of the repository for which to retrieve issues")


class GithubConnectorTools(ConnectorToolsInterface[GithubSecrets]):
    """
    A collection of tools used to interact with the GitHub Issues Connector.
    Implements methods for retrieving repositories and issues with proper retry and rate limiting logic.
    """

    def __init__(self, config: GithubConnectorConfig, target: GithubTarget, secrets: GithubSecrets):
        self._config = config
        self._target: GithubTarget = target
        super().__init__(connector=ConnectorIdEnum.GITHUB, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        """Returns the list of tool instances for GitHub operations."""
        return [
            Tool(connector=ConnectorIdEnum.GITHUB, name="get_github_repositories", execute_fn=self.get_github_repositories_async),
            Tool(connector=ConnectorIdEnum.GITHUB, name="get_github_issues", execute_fn=self.get_github_issues_async),
        ]

    async def get_github_repositories_async(self, input: GetGithubRepositoriesInput) -> ToolResult:
        """
        Retrieves GitHub repositories for the authenticated user.
        Implements retry logic to handle API rate limiting responses.
        """
        retries = 3
        async with httpx.AsyncClient(timeout=30) as client:
            response = None
            for attempt in range(retries):
                response = await client.get(
                    f"{self._config.url}/user/repos",
                    headers={"Authorization": f"token {self._secrets.access_token.get_secret_value()}"},
                )
                if response.status_code in (429, 403):
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                repos = response.json()
                if self._target and self._target.repository_ids:
                    allowed = {str(rid) for rid in self._target.repository_ids}
                    repos = [repo for repo in repos if str(repo.get("id")) in allowed]
                for repo in repos:
                    repo["id"] = str(repo.get("id"))
                return ToolResult(result=repos)
            repos = response.json() if response is not None else []
            if self._target and self._target.repository_ids:
                allowed = {str(rid) for rid in self._target.repository_ids}
                repos = [repo for repo in repos if str(repo.get("id")) in allowed]
            for repo in repos:
                repo["id"] = str(repo.get("id"))
            return ToolResult(result=repos)

    async def get_github_issues_async(self, input: GetGithubIssuesInput) -> ToolResult:
        """
        Retrieves issues for a given GitHub repository using its repository ID.
        Implements retry logic to handle API rate limiting responses.
        """
        repository_id = input.repository_id
        retries = 3
        async with httpx.AsyncClient(timeout=30) as client:
            repo_resp = await client.get(
                f"{self._config.url}/repositories/{repository_id}",
                headers={"Authorization": f"token {self._secrets.access_token.get_secret_value()}"},
            )
            if repo_resp.status_code != 200:
                return ToolResult(result=[])
            repo_data = repo_resp.json()
            full_name = repo_data.get("full_name")
            if not full_name:
                return ToolResult(result=[])
            issues_resp = None
            for attempt in range(retries):
                issues_resp = await client.get(
                    f"{self._config.url}/repos/{full_name}/issues?state=all",
                    headers={"Authorization": f"token {self._secrets.access_token.get_secret_value()}"},
                )
                if issues_resp.status_code in (429, 403):
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                issues = issues_resp.json()
                return ToolResult(result=issues)
            issues = issues_resp.json() if issues_resp is not None else []
            return ToolResult(result=issues)
