import asyncio
from typing import Any

import httpx
from pydantic import SecretStr

from connectors.zendesk.connector.config import ZendeskConnectorConfig


async def get_tickets(config: ZendeskConnectorConfig, token: SecretStr, view_id: str) -> list[Any]:
    """Retrieve tickets for a given Zendesk view from the Zendesk API."""
    url = f"https://{config.subdomain}.zendesk.com/api/v2/views/{view_id}/tickets.json"
    auth = (f"{config.email}/token", token.get_secret_value())
    for attempt in range(config.api_max_retries):
        try:
            async with httpx.AsyncClient(timeout=config.api_request_timeout) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                data = response.json()
                tickets = data.get("tickets", [])
                return tickets
        except Exception as e:
            if attempt == config.api_max_retries - 1:
                raise e
            await asyncio.sleep(1)
    return []


async def get_ticket_details(config: ZendeskConnectorConfig, token: SecretStr, ticket_id: str) -> dict[str, Any]:
    """Retrieve detailed information for a specific Zendesk ticket."""
    url = f"https://{config.subdomain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (f"{config.email}/token", token.get_secret_value())
    for attempt in range(config.api_max_retries):
        try:
            async with httpx.AsyncClient(timeout=config.api_request_timeout) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                data = response.json()
                return data.get("ticket", {})
        except Exception as e:
            if attempt == config.api_max_retries - 1:
                raise e
            await asyncio.sleep(1)
    return {}
