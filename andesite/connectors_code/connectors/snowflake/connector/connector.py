import asyncio
import os
from pathlib import Path

import snowflake.connector
from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from opentelemetry import trace
from pydantic import SecretStr
from snowflake.connector import SnowflakeConnection

from connectors.connector import Connector
from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector
from connectors.snowflake.connector.config import SnowflakeConnectorConfig
from connectors.snowflake.connector.target import SnowflakeTarget
from connectors.snowflake.connector.secrets import SnowflakeSecrets
from connectors.snowflake.connector.tools import SnowflakeConnectorTools

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_connection(config: SnowflakeConnectorConfig, secrets: SnowflakeSecrets) -> SnowflakeConnection:
    """Establish a connection to Snowflake using provided credentials."""
    return snowflake.connector.connect(
        account=config.account_id,
        user=config.user,
        password=secrets.password.get_secret_value(),
        timeout=config.api_request_timeout,
        client_session_keep_alive=True,
    )


async def _get_query_target_options_async(config: SnowflakeConnectorConfig, secrets: SnowflakeSecrets) -> ConnectorQueryTargetOptions:
    """Retrieve Snowflake database names as query target options using a synchronous helper via asyncio.to_thread."""

    def sync_get_options():
        conn = _get_connection(config, secrets)
        cs = conn.cursor()
        cs.execute("SHOW DATABASES")
        rows = cs.fetchall()
        cs.close()
        conn.close()
        db_names = [row[1] for row in rows if row and len(row) >= 2]
        definitions = [ScopeTargetDefinition(name="databases", multiselect=True)]
        selectors = [ScopeTargetSelector(type="databases", values=db_names)]
        return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)

    try:
        return await asyncio.to_thread(sync_get_options)
    except Exception as e:
        logger().exception("Failed to obtain query target options synchronously")
        raise e


async def _check_connection(config: SnowflakeConnectorConfig, secrets: SnowflakeSecrets) -> bool:
    """Checks connection by running a simple query on Snowflake."""
    try:
        client = _get_connection(config, secrets)
        cs = client.cursor()
        cs.execute("SELECT current_date()")
        cs.fetchone()
        cs.close()
        client.close()
        return True
    except Exception:
        logger().exception("Snowflake connection check failed")
        return False

async def _get_secrets(config: SnowflakeConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> SnowflakeSecrets | None:
    password = user_token if user_token is not None else config.password.decrypt(encryption_key=encryption_key)

    if password is None:
        return None
    return SnowflakeSecrets(password=password)


SnowflakeConnector = Connector(
    display_name="Snowflake",
    beta=True,
    id=ConnectorIdEnum.SNOWFLAKE,
    config_cls=SnowflakeConnectorConfig,
    query_target_type=SnowflakeTarget,
    description="Snowflake is a cloud data warehouse.",
    get_secrets=_get_secrets,
    logo_path=Path(os.path.join(os.path.dirname(__file__), "snowflake.svg")),
    get_tools=lambda config, target, secrets, cache: SnowflakeConnectorTools(config, target, secrets).get_tools(),
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options_async,
)
