import os
from pathlib import Path

from common.jsonlogging.jsonlogger import Logging
from common.models.tool import Tool
from opentelemetry import trace

from connectors.connector import (
    Connector
)
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.tenable.connector.config import TenableConnectorConfig
from connectors.tenable.connector.target import TenableTarget
from connectors.tenable.connector.tools import TenableConnectorTools
from pydantic import SecretStr

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_alert_enrichment_prompt() -> str:
    return "If there are are hosts in this alert, ask Tenable to find info on these hosts and any vulnerabilities that might be related. Return a report of no more than 2 paragraphs acting as an enrichment for the alert. Don't offer followup. Don't summarize the alert, only give details as it relates to Tenable."

def _get_tools(display_name: str, config: TenableConnectorConfig, target: TenableTarget, token: SecretStr | None) -> list[Tool]:
    tenable_target = TenableTarget(**target.model_dump())
    return TenableConnectorTools(
        TenableConnectorConfig(**config.model_dump()), tenable_target, connector_display_name=display_name
    ).get_tools()

TenableConnector = Connector(
    id=ConnectorIdEnum.TENABLE,
    query_target_type=TenableTarget,
    config_cls=TenableConnectorConfig,
    display_name="Tenable Vulnerability Management",
    description="Tenable Vulnerability Management identifies and manages security vulnerabilities to protect IT infrastructure.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "tenable.svg")),

    get_tools=_get_tools,
    get_alert_enrichment_prompt=_get_alert_enrichment_prompt
)
