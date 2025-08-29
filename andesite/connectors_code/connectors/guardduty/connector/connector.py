import os
import asyncio
import boto3
from botocore.config import Config as BotoConfig
from pathlib import Path

from opentelemetry import trace
from pydantic import SecretStr
from common.jsonlogging.jsonlogger import Logging

from connectors.connector import Connector
from connectors.cache import Cache
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.guardduty.connector.config import GuarddutyConnectorConfig
from connectors.guardduty.connector.target import GuarddutyTarget
from connectors.guardduty.connector.secrets import GuarddutySecrets
from connectors.guardduty.connector.tools import GuarddutyConnectorTools

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

def _get_tools(config: GuarddutyConnectorConfig, target: GuarddutyTarget, secrets: GuarddutySecrets, cache: Cache | None):
    """
    Provides tool collection for the GuardDuty connector.
    """
    return GuarddutyConnectorTools(
        config=config,
        target=target,
        secrets=secrets
    ).get_tools()

@tracer.start_as_current_span("check_connection")
async def _check_connection(config: GuarddutyConnectorConfig, secrets: GuarddutySecrets) -> bool:
    """
    Verifies connectivity to AWS GuardDuty by listing detectors.
    """
    try:
        boto_config = BotoConfig(
            retries={
                'max_attempts': config.api_max_retries,
                'mode': 'standard'
            },
            connect_timeout=config.api_request_timeout,
            read_timeout=config.api_request_timeout
        )
        client = boto3.client(
            "guardduty",
            region_name=config.aws_region,
            aws_access_key_id=secrets.aws_access_key_id.get_secret_value(),
            aws_secret_access_key=secrets.aws_secret_access_key.get_secret_value(),
            aws_session_token=(secrets.aws_session_token.get_secret_value() if secrets.aws_session_token else None),
            config=boto_config
        )
        # Confirm connectivity by listing detectors
        await asyncio.to_thread(lambda: client.list_detectors())
        return True
    except Exception:
        logger().exception("GuardDuty connection failed")
        return False


async def _get_secrets(config: GuarddutyConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> GuarddutySecrets | None:
    if user_token is not None:
        raise ValueError("User token is not supported for salesforce at this time")

    aws_access_key_id = config.aws_access_key_id.decrypt(encryption_key=encryption_key)
    aws_secret_access_key = config.aws_secret_access_key.decrypt(encryption_key=encryption_key)
    aws_session_token = config.aws_session_token.decrypt(encryption_key=encryption_key) if config.aws_session_token else None

    if aws_access_key_id is None or aws_secret_access_key is None:
        return None

    return GuarddutySecrets(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )

GuarddutyConnector = Connector(
    id=ConnectorIdEnum.GUARDDUTY,
    display_name="AWS GuardDuty",
    beta=True,
    description="AWS GuardDuty detects threats in your AWS environment.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "guardduty.svg")),
    config_cls=GuarddutyConnectorConfig,
    query_target_type=GuarddutyTarget,
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    check_connection=_check_connection,
)
