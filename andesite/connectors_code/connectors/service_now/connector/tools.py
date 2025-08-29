from typing import Any
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.service_now.connector.config import ServiceNowConnectorConfig
import httpx
import asyncio
from common.jsonlogging.jsonlogger import Logging
from connectors.service_now.connector.secrets import ServiceNowSecrets
from connectors.tools import ConnectorToolsInterface
from connectors.service_now.connector.target import ServiceNowTarget
from pydantic import BaseModel, Field
from common.models.tool import Tool, ToolResult

logger = Logging.get_logger(__name__)

async def _get_with_retries(url: str, auth: tuple[Any, ...], timeout: int = 10, retries: int = 3):
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise e
    raise Exception("Failed to get a successful response after retries")

class ServiceNowConnectorTools(ConnectorToolsInterface[ServiceNowSecrets]):
    """A collection of tools used to interact with ServiceNow.
    Implements methods to list tables, retrieve records, and get record content from ServiceNow.
    """
    def __init__(self, target: ServiceNowTarget, config: ServiceNowConnectorConfig, secrets: ServiceNowSecrets):
        self.target = target
        self.config = config
        super().__init__(connector=ConnectorIdEnum.SERVICE_NOW, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                connector=ConnectorIdEnum.SERVICE_NOW,
                name="get_servicenow_tables",
                execute_fn=self.get_servicenow_tables
            ),
            Tool(
                connector=ConnectorIdEnum.SERVICE_NOW,
                name="get_servicenow_records",
                execute_fn=self.get_servicenow_records
            ),
            Tool(
                connector=ConnectorIdEnum.SERVICE_NOW,
                name="get_servicenow_record_content",
                execute_fn=self.get_servicenow_record_content
            )
        ]

    class GetTablesInput(BaseModel):
        """Input model for retrieving ServiceNow tables; no parameters needed."""
        pass

    async def get_servicenow_tables(self, input: GetTablesInput) -> ToolResult:
        """Retrieves a list of ServiceNow tables based on the table names provided in the target.

        Returns:
            ToolResult: Contains the list of tables with their details.
        """
        tables: list[Any] = []
        # For each table specified in the target, query its details from ServiceNow
        for table in self.target.table_names:
            url = f"{self.config.instance_url}/api/now/table/sys_db_object?sysparm_query=name={table}&sysparm_limit=1"
            response = await _get_with_retries(url, auth=(self.config.username, self.config.password))
            data = response.json().get("result", [])
            if data:
                tables.append(data[0])
        return ToolResult(result=tables)

    class GetRecordsInput(BaseModel):
        """Input model for retrieving records from a specified ServiceNow table."""
        table_name: str = Field(..., description="Table name to fetch records from")

    async def get_servicenow_records(self, input: GetRecordsInput) -> ToolResult:
        """Retrieves records from a specified ServiceNow table.

        Args:
            input (GetRecordsInput): Input model containing the table name.

        Returns:
            ToolResult: Contains the list of records retrieved.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{self.config.instance_url}/api/now/table/{input.table_name}?sysparm_limit=100"
            response = await client.get(url, auth=(self.config.username, self._secrets.password.get_secret_value()))
            response.raise_for_status()
            records = response.json().get("result", [])
        return ToolResult(result=records)

    class GetRecordContentInput(BaseModel):
        """Input model for retrieving detailed content of a specific ServiceNow record."""
        table_name: str = Field(..., description="Table name")
        record_id: str = Field(..., description="Record sys_id")

    async def get_servicenow_record_content(self, input: GetRecordContentInput) -> ToolResult:
        """Retrieves detailed content of a specific record from a ServiceNow table.

        Args:
            input (GetRecordContentInput): Input model containing the table name and record sys_id.

        Returns:
            ToolResult: Contains the detailed record content.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{self.config.instance_url}/api/now/table/{input.table_name}/{input.record_id}"
            response = await client.get(url, auth=(self.config.username, self._secrets.password.get_secret_value()))
            response.raise_for_status()
            record = response.json().get("result", {})
        return ToolResult(result=record)
