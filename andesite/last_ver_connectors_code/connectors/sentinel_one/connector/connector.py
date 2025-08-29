import os
from pathlib import Path

from common.jsonlogging.jsonlogger import Logging
from common.models.tool import Tool
from opentelemetry import trace

from connectors.connector import (
    Connector,
)
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.sentinel_one.connector.config import SentinelOneConnectorConfig
from connectors.sentinel_one.connector.target import SentinelOneTarget
from connectors.sentinel_one.connector.tools import SentinelOneConnectorTools
from pydantic import SecretStr

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)



def _get_tools(display_name: str, config: SentinelOneConnectorConfig, target: SentinelOneTarget, token: SecretStr | None) -> list[Tool]:
    config = SentinelOneConnectorConfig(**config.model_dump())
    return SentinelOneConnectorTools(display_name=display_name, config=config).get_tools()

SentinelOneConnector = Connector(
    display_name="SentinelOne",
    id=ConnectorIdEnum.SENTINEL_ONE,
    config_cls=SentinelOneConnectorConfig,
    query_target_type=SentinelOneTarget,
    description="SentinelOne is a platform to manage endpoint detection and response.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "sentinel_one.svg")),

    get_tools=_get_tools,
)
