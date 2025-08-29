import os
from pathlib import Path
from common.models.tool import Tool
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.archer.connector.config import ArcherConnectorConfig
from connectors.archer.connector.target import ArcherTarget
from connectors.archer.connector.secrets import ArcherSecrets
from connectors.archer.connector.tools import ArcherConnectorTools
from connectors.cache import Cache
from connectors.connector import Connector
from pydantic import SecretStr


# Function to get tools via the dedicated Archer tools class
def get_tools(config: ArcherConnectorConfig, target: ArcherTarget, secrets: ArcherSecrets, cache: Cache | None) -> list[Tool]:
    # Here, token is not used because credentials are provided in the config
    return ArcherConnectorTools(config, target, secrets).get_tools()


# Function to check connection by calling the 'myself' endpoint
async def check_connection(config: ArcherConnectorConfig, secrets: ArcherSecrets) -> bool:
    return False


# Function to get query target options by listing projects
# TODO: understand this is it in scope? How does this interact
async def get_query_target_options(config: ArcherConnectorConfig, secrets: ArcherSecrets):
    from connectors.query_target_options import ConnectorQueryTargetOptions
    return ConnectorQueryTargetOptions(definitions=[], selectors=[])


async def _get_secrets(config: ArcherConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> ArcherSecrets | None:
    return ArcherSecrets()

ArcherConnector = Connector(
    display_name="Archer",
    beta=True,
    id=ConnectorIdEnum.ARCHER,
    config_cls=ArcherConnectorConfig,
    query_target_type=ArcherTarget,
    get_secrets=_get_secrets,
    description="Archer connector to interface with the Archer API",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "archer.svg")),
    get_tools=get_tools,
    check_connection=check_connection,
    get_query_target_options=get_query_target_options
)
