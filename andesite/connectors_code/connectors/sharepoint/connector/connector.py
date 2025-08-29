import os
from pathlib import Path

from pydantic import SecretStr

from common.models.connector_id_enum import ConnectorIdEnum
import httpx
from connectors.sharepoint.connector.config import SharePointConnectorConfig
from connectors.query_target_options import ScopeTargetDefinition, ScopeTargetSelector, ConnectorQueryTargetOptions
from connectors.sharepoint.connector.target import SharePointTarget
from connectors.connector import Connector
from connectors.cache import Cache

from connectors.sharepoint.connector.secrets import SharePointSecrets

async def _get_access_token(config: SharePointConnectorConfig, client_secret: SecretStr) -> str:
    """Retrieve an access token from Microsoft identity platform using client credentials.

    Returns:
        A valid access token as a string.

    Raises:
        httpx.HTTPError: If the token request fails.
    """
    import httpx
    token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": config.client_id,
        "client_secret": client_secret.get_secret_value(),
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    async with httpx.AsyncClient(timeout=config.request_timeout) as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        json_resp = response.json()
        return json_resp.get("access_token")

async def _get_query_target_options(config: SharePointConnectorConfig, secrets: SharePointSecrets) -> ConnectorQueryTargetOptions:
    """
    Retrieve query target options listing SharePoint sites using Microsoft Graph API.

    This method authenticates with SharePoint using the provided configuration to obtain an access token,
    then queries the Microsoft Graph API for sites. If no sites are retrieved, it falls back to the default site name
    provided in the configuration.

    Returns:
        ConnectorQueryTargetOptions: The target options containing site definitions and selectors.
    """
    try:
        headers = {"Authorization": f"Bearer {secrets.access_token.get_secret_value()}"}
        url = f"https://graph.microsoft.com/{config.api_version}/sites?search="
        async with httpx.AsyncClient(timeout=config.request_timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            sites = response.json().get("value", [])
            site_names = [site.get("name", "") for site in sites if site.get("name")]
    except Exception:
        site_names = []
    definitions = [ScopeTargetDefinition(name="site", multiselect=True)]
    selectors = [ScopeTargetSelector(type="site", values=site_names)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


def _get_tools(config: SharePointConnectorConfig, target: SharePointTarget, secrets: SharePointSecrets, cache: Cache | None):
    """
    Return the list of tools for the SharePoint connector by delegating to the tools class.
    """
    from connectors.sharepoint.connector.tools import SharePointConnectorTools
    return SharePointConnectorTools(config, target, secrets).get_tools()


async def _check_connection(config: SharePointConnectorConfig, secrets: SharePointSecrets) -> bool:
    """
    Checks the connection by obtaining an access token from SharePoint via Microsoft Graph API.
    """
    try:
        return bool(secrets and secrets.access_token)
    except Exception:
        return False


async def _get_secrets(config: SharePointConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> SharePointSecrets | None:
    client_secret = user_token if user_token is not None else config.client_secret.decrypt(encryption_key=encryption_key)

    if client_secret is None:
        return None

    access_token = await _get_access_token(config, client_secret=client_secret)
    return SharePointSecrets(access_token=SecretStr(access_token))



SharePointConnector = Connector(
    display_name="SharePoint",
    id=ConnectorIdEnum.SHAREPOINT,
    config_cls=SharePointConnectorConfig,
    query_target_type=SharePointTarget,
    beta=True,
    description="Microsoft SharePoint Connector",
    get_secrets=_get_secrets,
    logo_path=Path(os.path.join(os.path.dirname(__file__), "sharepoint.svg")),
    get_tools=_get_tools,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options
)
