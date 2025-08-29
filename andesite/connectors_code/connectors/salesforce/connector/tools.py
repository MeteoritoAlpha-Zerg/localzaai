from typing import Any, List
import time
from pydantic import BaseModel, Field
from common.models.tool import Tool
from connectors.salesforce.connector.target import SalesforceTarget
from connectors.salesforce.connector.secrets import SalesforceSecrets
from connectors.tools import ConnectorToolsInterface
from common.models.connector_id_enum import ConnectorIdEnum
from opentelemetry import trace
from simple_salesforce.exceptions import SalesforceGeneralError
from common.models.tool import ToolResult
from simple_salesforce.api import Salesforce

tracer = trace.get_tracer(__name__)

class SalesforceConnectorTools(ConnectorToolsInterface[SalesforceSecrets]):
    """
    A collection of tools used by agents that query Salesforce.
    """

    def __init__(
        self,
        client: Salesforce,
        target: SalesforceTarget,
        secrets: SalesforceSecrets
    ):
        """
        Initializes the tool collection for a specific Salesforce target.

        :param client: The Salesforce client instance.
        :param target: The SalesforceTarget specifying objects list.
        """
        self.client = client
        self.target = target
        super().__init__(ConnectorIdEnum.SALESFORCE, target=target, secrets=secrets)

    def get_tools(self) -> List[Tool]:
        """
        Returns a list of Tool objects for querying Salesforce.
        """
        tools: List[Tool] = []
        tools.append(
            Tool(
                connector=ConnectorIdEnum.SALESFORCE,
                name="list_salesforce_objects",
                execute_fn=self.list_salesforce_objects_async,
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.SALESFORCE,
                name="list_salesforce_records",
                execute_fn=self.list_salesforce_records_async,
            )
        )
        return tools

    class ListSalesforceObjectsInput(BaseModel):
        """
        Retrieves the list of Salesforce objects available in the organization.
        No inputs required.
        """
        pass

    @tracer.start_as_current_span("list_salesforce_objects_async")
    async def list_salesforce_objects_async(
        self, input: ListSalesforceObjectsInput
    ) -> ToolResult:
        """
        Retrieves metadata for all selected Salesforce objects that are accessible via the authenticated account.

        This tool queries the Salesforce schema using the describe API and returns metadata for available objects.
        Each object entry includes fields such as object name, label, creation capability, update capability, and other attributes.

        Returns:
            A list of metadata dictionaries, each representing a Salesforce object
        """
        max_retries = getattr(self.client, "max_retries", 1)
        backoff = 1
        for attempt in range(max_retries):
            try:
                desc: Any = self.client.describe() or []
                all_objects = desc.get("sobjects", [])

                target_objects = set(self.target.objects)
                filtered = [obj for obj in all_objects if obj.get("name") in target_objects]

                return ToolResult(result=filtered)
            except SalesforceGeneralError as e:
                if "REQUEST_LIMIT_EXCEEDED" in str(e):
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
            except Exception:
                if attempt == max_retries - 1:
                    break
                continue

        return ToolResult(result="Failed to retrieve Salesforce objects after retries")

    class ListSalesforceRecordsInput(BaseModel):
        """
        Input model for retrieving records from a specific Salesforce object.

        Fields:
            object_name: The name of the Salesforce object to query (e.g., "Account", "Case").
        """
        object_name: str = Field(
            description="The name of the Salesforce object to retrieve records from."
        )

    @tracer.start_as_current_span("list_salesforce_records_async")
    async def list_salesforce_records_async(
        self, input: ListSalesforceRecordsInput
    ) -> ToolResult:
        """
        Retrieves records for a specified Salesforce object.

        This tool runs a basic SOQL query to select record IDs from the provided object. It returns a list of record entries containing identifiers and attributes.

        Returns:
            A list of record dictionaries retrieved from the Salesforce object
        """
        max_retries = getattr(self.client, "max_retries", 1)
        backoff = 1
        for attempt in range(max_retries):
            try:
                desc: Any = self.client.describe() or []
                return ToolResult(result=desc.get("sobjects", []))
            except SalesforceGeneralError as e:
                error_str = str(e)
                if "REQUEST_LIMIT_EXCEEDED" in error_str:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
            except Exception:
                if attempt == max_retries - 1:
                    break
                continue

        return ToolResult(result="Failed to retrieve Salesforce objects after retries")
