"""
CrowdStrike Connector implementation.

This module defines the CrowdStrike connector for interacting with the CrowdStrike Falcon API,
including configuration, connection checking, query target enumeration, and tool dispatching.
"""

import os
from pathlib import Path

from pydantic import SecretStr

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from httpx import AsyncClient

from connectors.connector import Connector
from connectors.cache import Cache
from connectors.crowdstrike.connector.config import CrowdstrikeConnectorConfig
from connectors.crowdstrike.connector.target import CrowdstrikeTarget
from connectors.crowdstrike.connector.secrets import CrowdstrikeSecrets
from connectors.crowdstrike.connector.tools import CrowdstrikeConnectorTools

logger = Logging.get_logger(__name__)


async def _check_connection(config: CrowdstrikeConnectorConfig, secrets: CrowdstrikeSecrets) -> bool:
    """
    Check that the connector can authenticate with CrowdStrike.
    """
    base_url = config.url or f"https://{config.host}"
    timeout = config.api_request_timeout
    try:
        async with AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url}/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(config.client_id, secrets.client_secret.get_secret_value()),
            )
            resp.raise_for_status()
        return True
    except Exception:
        logger().exception("CrowdStrike connection check failed")
        return False


def _get_tools(config: CrowdstrikeConnectorConfig, target: CrowdstrikeTarget, secrets: CrowdstrikeSecrets, cache: Cache | None) -> list[Tool]:
    """
    Returns a list of tools for CrowdStrike connector.
    """
    return CrowdstrikeConnectorTools(config, target, secrets).get_tools()


async def _get_secrets(config: CrowdstrikeConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> CrowdstrikeSecrets | None:
    client_secret = user_token if user_token is not None else config.client_secret.decrypt(encryption_key=encryption_key)

    if client_secret is None:
        return None

    return CrowdstrikeSecrets(
        client_secret=client_secret,
    )

CrowdstrikeConnector = Connector(
    id=ConnectorIdEnum.CROWDSTRIKE,
    display_name="CrowdStrike",
    beta=True,
    config_cls=CrowdstrikeConnectorConfig,
    query_target_type=CrowdstrikeTarget,
    description="CrowdStrike Falcon API connector",
    get_secrets=_get_secrets,
    logo_path=Path(os.path.join(os.path.dirname(__file__), "crowdstrike.svg")),
    get_tools=_get_tools,
    check_connection=_check_connection,
)
