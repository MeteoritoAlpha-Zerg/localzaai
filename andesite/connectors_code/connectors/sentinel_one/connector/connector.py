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
from connectors.sentinel_one.connector.config import SentinelOneConnectorConfig
from connectors.sentinel_one.connector.target import SentinelOneTarget
from connectors.sentinel_one.connector.secrets import SentinelOneSecrets
from connectors.sentinel_one.connector.tools import SentinelOneConnectorTools

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_tools(config: SentinelOneConnectorConfig, target: SentinelOneTarget, secrets: SentinelOneSecrets, cache: Cache | None) -> list[Tool]:
    config = SentinelOneConnectorConfig(**config.model_dump())
    return SentinelOneConnectorTools(config=config, secrets=secrets).get_tools()

async def _get_secrets(config: SentinelOneConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> SentinelOneSecrets | None:
    token = user_token if user_token is not None else config.token.decrypt(encryption_key=encryption_key)

    if token is None:
        return None

    return SentinelOneSecrets(token=token)


SentinelOneConnector = Connector(
    display_name="SentinelOne",
    beta=True,
    id=ConnectorIdEnum.SENTINEL_ONE,
    config_cls=SentinelOneConnectorConfig,
    query_target_type=SentinelOneTarget,
    get_secrets=_get_secrets,
    description="SentinelOne is a platform to manage endpoint detection and response.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "sentinel_one.svg")),
    get_tools=_get_tools,
)
