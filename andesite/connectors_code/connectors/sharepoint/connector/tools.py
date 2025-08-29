import asyncio
from typing import Any
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.sharepoint.connector.config import SharePointConnectorConfig
from connectors.sharepoint.connector.target import SharePointTarget
import httpx
from pydantic import BaseModel

from connectors.sharepoint.connector.secrets import SharePointSecrets
from connectors.tools import ConnectorToolsInterface
from common.models.tool import Tool


class GetDocumentLibrariesInput(BaseModel):
    """Input model for retrieving SharePoint document libraries.
    Currently, no parameters are required.
    """
    pass


class GetDocumentsInput(BaseModel):
    """Input model for retrieving SharePoint documents.
    Currently, no parameters are required.
    """
    pass


class SharePointConnectorTools(ConnectorToolsInterface[SharePointSecrets]):
    """Tools for SharePoint Connector"""
    def __init__(self, config: SharePointConnectorConfig, target: SharePointTarget,  secrets: SharePointSecrets):
        self.config = config
        self._target: SharePointTarget = target
        super().__init__(ConnectorIdEnum.SHAREPOINT, target, secrets)

    async def _request_with_retry(self, method: str, url: str, headers: dict[Any, Any], retries: int | None = None) -> httpx.Response | None:
        """Make an HTTP request with retry logic for handling rate limiting (HTTP 429)."""
        if retries is None:
            retries = self.config.api_max_retries
        attempt = 0
        response = None
        while attempt <= retries:
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.request(method, url, headers=headers)
            if response.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                attempt += 1
                continue
            return response
        return response

    async def _get_site_id(self, site_name: str, access_token: str) -> str:
        """Retrieve the site ID for a given site name using Microsoft Graph API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://graph.microsoft.com/{self.config.api_version}/sites?search={site_name}"
        async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("value", [])
        if data:
            return data[0].get("id")
        raise Exception(f"Site id not found for site: {site_name}")

    async def get_sharepoint_document_libraries_async(self, inp: GetDocumentLibrariesInput) -> list[Any]:
        """Retrieve document libraries (drives) from the specified SharePoint sites.

        :param inp: Input parameters (currently unused)
        :return: A ToolResult containing a list of document library objects
        """
        headers = {"Authorization": f"Bearer {self._secrets.access_token.get_secret_value()}"}
        libraries: list[Any] = []
        for site_name in self._target.site_names:
            site_id = await self._get_site_id(site_name, self._secrets.access_token.get_secret_value())
            drives_url = f"https://graph.microsoft.com/{self.config.api_version}/sites/{site_id}/drives"
            response = await self._request_with_retry("GET", drives_url, headers)
            if response is None:
                return []
            response.raise_for_status()
            drives = response.json().get("value", [])
            for drive in drives:
                drive_id = drive.get("id")
                if drive_id:
                    details_url = f"https://graph.microsoft.com/{self.config.api_version}/drives/{drive_id}/root?$select=serverRelativeUrl"
                    details_resp = await self._request_with_retry("GET", details_url, headers)
                    if details_resp is None:
                        continue
                    details_resp.raise_for_status()
                    details = details_resp.json()
                    drive["serverRelativeUrl"] = details.get("serverRelativeUrl", "")
                drive["siteUrl"] = site_name
                libraries.append(drive)
        return libraries

    async def get_sharepoint_documents_async(self, inp: GetDocumentsInput) -> list[Any]:
        """Retrieve documents from the specified document libraries in the selected SharePoint sites.

        :param inp: Input parameters (currently unused)
        :return: A ToolResult containing a list of document objects from the libraries
        """
        headers = {"Authorization": f"Bearer {self._secrets.access_token.get_secret_value()}"}
        documents: list[Any] = []
        for site_name in self._target.site_names:
            site_id = await self._get_site_id(site_name, self._secrets.access_token.get_secret_value())
            drives_url = f"https://graph.microsoft.com/{self.config.api_version}/sites/{site_id}/drives"
            response = await self._request_with_retry("GET", drives_url, headers)
            if response is None:
                return []
            response.raise_for_status()
            drives = response.json().get("value", [])
            for drive in drives:
                docs_url = f"https://graph.microsoft.com/{self.config.api_version}/drives/{drive.get('id')}/root/children"
                docs_response = await self._request_with_retry("GET", docs_url, headers)
                if docs_response is None:
                    continue
                docs_response.raise_for_status()
                docs = docs_response.json().get("value", [])
                for doc in docs:
                    doc["siteUrl"] = site_name
                    documents.append(doc)
        return documents

    def get_tools(self) -> list[Tool]:
        """Return a list of tools for SharePoint connector operations."""
        return [
            Tool(
                connector=ConnectorIdEnum.SHAREPOINT,
                name="get_sharepoint_document_libraries",
                execute_fn=self.get_sharepoint_document_libraries_async
            ),
            Tool(
                connector=ConnectorIdEnum.SHAREPOINT,
                name="get_sharepoint_documents",
                execute_fn=self.get_sharepoint_documents_async
            )
        ]
