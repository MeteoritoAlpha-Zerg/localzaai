import os
from pathlib import Path
import base64
from common.models.tool import Tool
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.jira.connector.config import JIRAConnectorConfig
from connectors.jira.connector.target import JIRATarget
from connectors.jira.connector.secrets import JIRASecrets
from connectors.jira.connector.tools import JIRAConnectorTools
import httpx
from connectors.connector import Connector
from connectors.cache import Cache
from pydantic import SecretStr


# Function to get tools via the dedicated JIRA tools class
def get_tools(config: JIRAConnectorConfig, target: JIRATarget, secrets: JIRASecrets, cache: Cache | None) -> list[Tool]:
    # Here, token is not used because credentials are provided in the config
    return JIRAConnectorTools(config, target, secrets).get_tools()


# Function to check connection by calling the 'myself' endpoint
async def check_connection(config: JIRAConnectorConfig, secrets: JIRASecrets) -> bool:
    base_url = config.url.rstrip("/")
    auth_header = {
        "Authorization": "Basic " + base64.b64encode(f"{config.email}:{secrets.api_key.get_secret_value()}".encode()).decode()
    }
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/rest/api/3/myself"
        try:
            response = await client.get(url, headers=auth_header, timeout=30)
            response.raise_for_status()
            return True
        except Exception:
            return False


# Function to get query target options by listing projects
async def get_query_target_options(config: JIRAConnectorConfig, secrets: JIRASecrets):
    from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector
    base_url = config.url.rstrip("/")
    auth_header = {
        "Authorization": "Basic " + base64.b64encode(f"{config.email}:{secrets.api_key.get_secret_value()}".encode()).decode()
    }
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/rest/api/3/project"
        response = await client.get(url, headers=auth_header, timeout=30)
        response.raise_for_status()
        projects = response.json()
    project_keys = [p.get("key") for p in projects]

    # This must be the same as the property in the JIRA Query Target
    QUERY_TARGET_KEY = "project_keys"
    definitions = [ScopeTargetDefinition(name=QUERY_TARGET_KEY, multiselect=True)]
    selectors = [ScopeTargetSelector(type=QUERY_TARGET_KEY, values=project_keys)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


async def _get_secrets(config: JIRAConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> JIRASecrets | None:
    api_key = user_token if user_token is not None else config.api_key.decrypt(encryption_key=encryption_key)

    if api_key is None:
        return None

    return JIRASecrets(api_key=api_key)

JIRAConnector = Connector(
    display_name="JIRA",
    id=ConnectorIdEnum.JIRA,
    config_cls=JIRAConnectorConfig,
    query_target_type=JIRATarget,
    description="JIRA connector to interface with the JIRA API",
    get_secrets=_get_secrets,
    logo_path=Path(os.path.join(os.path.dirname(__file__), "jira.svg")),
    get_tools=get_tools,
    check_connection=check_connection,
    get_query_target_options=get_query_target_options
)
