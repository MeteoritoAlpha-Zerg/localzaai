import os
from pathlib import Path

from pydantic import SecretStr

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace

from connectors.connector import Connector
from connectors.cache import Cache
from connectors.tenable.connector.config import TenableConnectorConfig
from connectors.tenable.connector.target import TenableTarget
from connectors.tenable.connector.secrets import TenableSecrets
from connectors.tenable.connector.tools import TenableConnectorTools

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_alert_enrichment_prompt() -> str:
    return """"
        "If there are are hosts in this alert, ask Tenable to find info on these hosts and any vulnerabilities that might be related.
        Try to remove the domain of hosts if Tenable fails to find the asset.
        Return a report of no more than 2 paragraphs acting as an enrichment for the alert.
        Don't offer followup.
        Don't summarize the alert, only give details as it relates to Tenable.
        """


def _get_tools(config: TenableConnectorConfig, target: TenableTarget, secrets: TenableSecrets, cache: Cache | None) -> list[Tool]:
    tenable_target = TenableTarget(**target.model_dump())
    return TenableConnectorTools(config, tenable_target, secrets).get_tools()

async def _get_secrets(config: TenableConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> TenableSecrets | None:
    if user_token is not None:
        raise ValueError("user token is not allowed for tenable at this time")

    access_key = config.access_key.decrypt(encryption_key=encryption_key)
    secret_key = config.secret_key.decrypt(encryption_key=encryption_key)

    if access_key and secret_key:
        return TenableSecrets(access_key=access_key, secret_key=secret_key)
    return None

TenableConnector = Connector(
    id=ConnectorIdEnum.TENABLE,
    query_target_type=TenableTarget,
    config_cls=TenableConnectorConfig,
    display_name="Tenable Vulnerability Management",
    description="Tenable Vulnerability Management identifies and manages security vulnerabilities to protect IT infrastructure.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "tenable.svg")),
    get_tools=_get_tools,
    get_secrets=_get_secrets,
    get_alert_enrichment_prompt=_get_alert_enrichment_prompt,
)
