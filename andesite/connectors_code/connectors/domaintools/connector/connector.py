import os
from pathlib import Path

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import SecretStr

from connectors.connector import (
    Cache,
    Connector,
)
from connectors.domaintools.connector.config import DomainToolsConnectorConfig
from connectors.domaintools.connector.target import DomainToolsTarget
from connectors.domaintools.connector.secrets import DomainToolsSecrets
from connectors.domaintools.connector.tools import DomainToolsConnectorTools

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_alert_enrichment_prompt() -> str:
    return "If there are are domains or URLs in this alert ask domaintools to provide information on them and pivot whenever it suggests to. Return a report of no more than 2 paragraphs acting as an enrichment for the alert. Don't offer followup. Don't summarize the alert, only give details as it relates to DomainTools."


def _get_tools(config: DomainToolsConnectorConfig, target: DomainToolsTarget, secrets: DomainToolsSecrets, cache: Cache | None) -> list[Tool]:
    domain_tools_target = DomainToolsTarget(**target.model_dump())
    return DomainToolsConnectorTools(config, domain_tools_target, secrets).get_tools()

async def _get_secrets(config: DomainToolsConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> DomainToolsSecrets | None:
    if user_token is not None:
        raise ValueError("User secrets are not supported by domain tools at this time")

    api_key = config.api_key.decrypt(encryption_key=encryption_key)
    api_username = config.api_username.decrypt(encryption_key=encryption_key)

    if api_key is None or api_username is None:
        return None

    return DomainToolsSecrets(
        api_username=api_username,
        api_key=api_key,
    )

DomainToolsConnector = Connector(
    display_name="DomainTools",
    id=ConnectorIdEnum.DOMAINTOOLS,
    query_target_type=DomainToolsTarget,
    config_cls=DomainToolsConnectorConfig,
    description="DomainTools: Domain and IP ownership intelligence.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "domaintools.svg")),
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    get_alert_enrichment_prompt=_get_alert_enrichment_prompt,
)
