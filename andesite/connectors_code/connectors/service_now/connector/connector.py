import os
from pathlib import Path
from typing import Any
import httpx
import asyncio

from connectors.connector import Connector
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.query_target_options import ConnectorQueryTargetOptions
from connectors.service_now.connector.config import ServiceNowConnectorConfig
from connectors.service_now.connector.target import ServiceNowTarget
from connectors.service_now.connector.secrets import ServiceNowSecrets
from connectors.service_now.connector.tools import ServiceNowConnectorTools
from pydantic import SecretStr


async def _get_query_target_options(config: ServiceNowConnectorConfig, secrets: ServiceNowSecrets) -> ConnectorQueryTargetOptions:
    """
    Retrieve available ServiceNow tables as query target options.
    """
    from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector
    tables: list[Any] = []
    retries = 3
    url = f"{config.instance_url}/api/now/table/sys_db_object?sysparm_fields=name,label&sysparm_limit=100"
    async with httpx.AsyncClient(timeout=10) as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, auth=(config.username, secrets.password.get_secret_value()))
                response.raise_for_status()
                result = response.json().get("result", [])
                for obj in result:
                    if "name" in obj and obj["name"]:
                        tables.append(obj["name"])
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise e
    definitions = [ScopeTargetDefinition(name="table_names", multiselect=True)]
    selectors = [ScopeTargetSelector(type="table_names", values=tables)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


async def _check_connection(config: ServiceNowConnectorConfig, secrets: ServiceNowSecrets):
    url = f"{config.instance_url}/api/now/table/sys_db_object?sysparm_limit=1"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, auth=(config.username, secrets.password.get_secret_value()))
            response.raise_for_status()
            return True
        except Exception:
            return False

async def _get_secrets(config: ServiceNowConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> ServiceNowSecrets | None:
    password = user_token if user_token is not None else config.password.decrypt(encryption_key=encryption_key)

    if password is None:
        return None

    return ServiceNowSecrets(password=password)


ServiceNowConnector = Connector(
    id=ConnectorIdEnum.SERVICE_NOW,
    beta=True,
    display_name="ServiceNow",
    description="Connector for ServiceNow API integration",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "servicenow.svg")),
    config_cls=ServiceNowConnectorConfig,
    query_target_type=ServiceNowTarget,
    get_secrets=_get_secrets,
    get_tools=lambda config, target, secrets, cache: ServiceNowConnectorTools(target, config, secrets).get_tools(),
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options
)
