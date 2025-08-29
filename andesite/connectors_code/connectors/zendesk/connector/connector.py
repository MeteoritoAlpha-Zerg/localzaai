import asyncio
import os
from pathlib import Path

import httpx
from common.models.connector_id_enum import ConnectorIdEnum
from pydantic import SecretStr

from connectors.connector import Connector
from connectors.cache import Cache
from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector
from connectors.zendesk.connector.config import ZendeskConnectorConfig
from connectors.zendesk.connector.target import ZendeskTarget
from connectors.zendesk.connector.secrets import ZendeskSecrets
from connectors.zendesk.connector.tools import ZendeskConnectorTools

async def _check_connection(config: ZendeskConnectorConfig, secrets: ZendeskSecrets) -> bool:
    """Checks whether the Zendesk connector can successfully connect to Zendesk."""
    url = f"https://{config.subdomain}.zendesk.com/api/v2/users/me.json"
    auth = (f"{config.email}/token", secrets.api_token.get_secret_value())
    for _ in range(config.api_max_retries):
        try:
            async with httpx.AsyncClient(timeout=config.api_request_timeout) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                return True
        except Exception:
            await asyncio.sleep(1)
    return False


async def _get_query_target_options(config: ZendeskConnectorConfig, secrets: ZendeskSecrets) -> ConnectorQueryTargetOptions:
    """Retrieves Zendesk view options for query target."""
    url = f"https://{config.subdomain}.zendesk.com/api/v2/views.json"
    auth = (f"{config.email}/token", secrets.api_token.get_secret_value())
    try:
        async with httpx.AsyncClient(timeout=config.api_request_timeout) as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            data = response.json()
            views = data.get("views", [])
            view_ids = [str(view["id"]) for view in views if "id" in view]
    except Exception:
        view_ids = []
    definitions = [ScopeTargetDefinition(name="view_ids", multiselect=True)]
    selectors = [ScopeTargetSelector(type="view_ids", values=view_ids)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


def _get_tools(config: ZendeskConnectorConfig, target: ZendeskTarget, secrets: ZendeskSecrets, cache: Cache | None):
    return ZendeskConnectorTools(target=target, config=config, secrets=secrets).get_tools()

async def _get_secrets(config: ZendeskConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> ZendeskSecrets | None:
    api_token = user_token if user_token is not None else config.api_token.decrypt(encryption_key=encryption_key)

    if api_token is None:
        return None
    return ZendeskSecrets(api_token=api_token)


ZendeskConnector = Connector(
    id=ConnectorIdEnum.ZENDESK,
    query_target_type=ZendeskTarget,
    config_cls=ZendeskConnectorConfig,
    beta=True,
    display_name="Zendesk",
    description="Zendesk is a customer support platform that integrates with external Zendesk API.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "zendesk.svg")),
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options,
)
