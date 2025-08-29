import os
from pathlib import Path

from opentelemetry import trace

from common.jsonlogging.jsonlogger import Logging
from connectors.connector import (
    Connector,
)
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.equinox.connector.config import EquinoxConnectorConfig
from connectors.equinox.connector.target import EquinoxTarget
from connectors.equinox.connector.tools import EquinoxConnectorTools
from connectors.equinox.database.equinox_instance import EquinoxInstance
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from common.models.tool import Tool
from pydantic import SecretStr

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)



async def _get_query_target_options(config: EquinoxConnectorConfig) -> ConnectorQueryTargetOptions:
    PROJECT = "project"
    definitions = [ScopeTargetDefinition(name=PROJECT)]
    selectors = [ScopeTargetSelector(type=PROJECT, values=["similarity"])]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )

def _get_tools(display_name: str, config: EquinoxConnectorConfig, target: EquinoxTarget, token: SecretStr | None) -> list[Tool]:
    equinox_target = EquinoxTarget(**target.model_dump())
    return EquinoxConnectorTools(equinox_target, connector_display_name=display_name).get_tools()

def _get_equinox_instance(config: EquinoxConnectorConfig) -> EquinoxInstance:
    return EquinoxInstance(
        protocol=config.protocol,
        host=config.host,
        port=config.port,
    )

async def _check_connection(config: EquinoxConnectorConfig, token: SecretStr | None) -> bool:
    client = _get_equinox_instance(config=config)
    health = client.health_check().get("health")
    return health == "ok"

EquinoxConnector = Connector(
    display_name="Equinox",
    id=ConnectorIdEnum.EQUINOX,
    query_target_type=EquinoxTarget,
    config_cls=EquinoxConnectorConfig,
    description="Equinox contains census data.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "equinox.svg")),

    get_tools=_get_tools,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options,
)
