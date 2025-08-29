import os
from pathlib import Path

from common.jsonlogging.jsonlogger import Logging
from common.models.tool import Tool
from opentelemetry import trace

from connectors.connector import (
    Connector,
)
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.domaintools.connector.config import DomainToolsConnectorConfig
from connectors.domaintools.connector.target import DomainToolsTarget
from connectors.domaintools.connector.tools import DomainToolsConnectorTools
from pydantic import SecretStr

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

def _get_alert_enrichment_prompt() -> str:
    return "If there are are domains or URLs in this alert ask domaintools to provide information on them and pivot whenever it suggests to. Return a report of no more than 2 paragraphs acting as an enrichment for the alert. Don't offer followup. Don't summarize the alert, only give details as it relates to DomainTools."

def _get_tools(display_name: str, config: DomainToolsConnectorConfig, target : DomainToolsTarget, token: SecretStr | None) -> list[Tool]:
    domain_tools_target = DomainToolsTarget(**target.model_dump())
    return DomainToolsConnectorTools(
        DomainToolsConnectorConfig(**config.model_dump()), domain_tools_target, connector_display_name=display_name,
    ).get_tools()

DomainToolsConnector = Connector(
    display_name="Domain Tools",
    id=ConnectorIdEnum.DOMAINTOOLS,
    query_target_type=DomainToolsTarget,
    config_cls=DomainToolsConnectorConfig,
    description="DomainTools: Domain and IP ownership intelligence.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "domaintools.svg")),

    get_tools=_get_tools,
    get_alert_enrichment_prompt=_get_alert_enrichment_prompt,
)
