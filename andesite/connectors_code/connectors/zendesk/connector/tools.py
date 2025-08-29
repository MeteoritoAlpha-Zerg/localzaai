from typing import Any, List

from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.tools import ConnectorToolsInterface
from connectors.zendesk.connector.api import get_ticket_details, get_tickets
from connectors.zendesk.connector.config import ZendeskConnectorConfig
from connectors.zendesk.connector.target import ZendeskTarget
from connectors.zendesk.connector.secrets import ZendeskSecrets

tracer = trace.get_tracer(__name__)


class GetZendeskTicketsInput(BaseModel):
    """Input model for retrieving Zendesk tickets.

    Attributes:
        view_id (str): The ID of the Zendesk view to retrieve tickets from.
    """

    view_id: str = Field(..., description="ID of the Zendesk view to retrieve tickets from")


class GetZendeskTicketDetailsInput(BaseModel):
    """Input model for retrieving details of a specific Zendesk ticket.

    Attributes:
        ticket_id (str): The ID of the Zendesk ticket.
    """

    ticket_id: str = Field(..., description="The ID of the Zendesk ticket")


class ZendeskConnectorTools(ConnectorToolsInterface[ZendeskSecrets]):
    """A collection of tools used to interact with Zendesk."""

    def __init__(self, target: ZendeskTarget, config: ZendeskConnectorConfig, secrets: ZendeskSecrets):
        """
        Initializes the tool collection for the Zendesk connector.

        Args:
            target (ZendeskTarget): The Zendesk target with view IDs.
            config (ZendeskConnectorConfig): Configuration for Zendesk.
        """
        self.config = config
        super().__init__(connector=ConnectorIdEnum.ZENDESK, target=target, secrets=secrets)

    @tracer.start_as_current_span("get_zendesk_tickets_async")
    async def get_zendesk_tickets_async(self, input: GetZendeskTicketsInput) -> List[Any]:
        """
        Asynchronously retrieves a list of Zendesk tickets for the specified view.

        Args:
            input (GetZendeskTicketsInput): Input model containing the view ID.

        Returns:
            List[Any]: A list of ticket objects retrieved from Zendesk.
        """
        tickets = await get_tickets(self.config, self._secrets.api_token, input.view_id)
        return tickets

    @tracer.start_as_current_span("get_zendesk_ticket_details_async")
    async def get_zendesk_ticket_details_async(self, input: GetZendeskTicketDetailsInput) -> dict[str, Any]:
        """
        Asynchronously retrieves detailed information for a specific Zendesk ticket.

        Args:
            input (GetZendeskTicketDetailsInput): Input model containing the ticket ID.

        Returns:
            dict: A dictionary containing detailed information of the ticket.
        """
        details = await get_ticket_details(self.config, self._secrets.api_token, input.ticket_id)
        return details

    def get_tools(self) -> List[Tool]:
        """
        Constructs and returns a list of Tool instances for Zendesk operations.

        Returns:
            List[Tool]: A list of tools for retrieving tickets and ticket details.
        """
        return [
            Tool(connector=ConnectorIdEnum.ZENDESK, name="get_zendesk_tickets", execute_fn=self.get_zendesk_tickets_async),
            Tool(connector=ConnectorIdEnum.ZENDESK, name="get_zendesk_ticket_details", execute_fn=self.get_zendesk_ticket_details_async),
        ]
