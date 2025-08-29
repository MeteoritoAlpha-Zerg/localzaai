import os
from pathlib import Path

from botocore.config import Config as BotoConfig
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from pydantic import SecretStr

from connectors.cloudwatch.connector.config import CloudWatchConnectorConfig
from connectors.cloudwatch.connector.target import CloudWatchTarget
from connectors.cloudwatch.connector.secrets import CloudWatchSecrets
from connectors.cloudwatch.connector.tools import CloudWatchConnectorTools
from connectors.connector import Connector
from connectors.cache import Cache
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from connectors.cloudwatch.connector.aws import get_client_context


async def _check_connection(config: CloudWatchConnectorConfig, secrets: CloudWatchSecrets) -> bool:
    """
    Check connectivity by calling a lightweight CloudWatch Logs API.
    """
    boto_config = BotoConfig(
        retries={"max_attempts": config.api_max_retries},
        read_timeout=config.api_request_timeout,
        connect_timeout=config.api_request_timeout,
    )
    async with await get_client_context("logs", boto_config) as client:
        try:
            # describe log groups to verify connectivity
            await client.describe_log_groups(limit=1) # type: ignore[attr-defined]
            return True
        except Exception:
            return False


async def _get_query_target_options(config: CloudWatchConnectorConfig, secrets: CloudWatchSecrets) -> ConnectorQueryTargetOptions:
    """
    Retrieve available CloudWatch log groups for user selection.
    """
    definitions = [ScopeTargetDefinition(name="log_groups", multiselect=True)]
    boto_config = BotoConfig(
        retries={"max_attempts": config.api_max_retries},
        read_timeout=config.api_request_timeout,
        connect_timeout=config.api_request_timeout,
    )

    async with await get_client_context("logs", boto_config) as client:
        paginator = client.get_paginator("describe_log_groups")
        log_groups: list[str] = []
        async for page in paginator.paginate():
            for lg in page.get("logGroups", []):
                name = lg.get("logGroupName")
                if name:
                    log_groups.append(name)
    selectors = [ScopeTargetSelector(type="log_groups", values=log_groups)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


def _get_tools(
    config: CloudWatchConnectorConfig,
    target: CloudWatchTarget,
    secrets: CloudWatchSecrets,
    cache: Cache | None
) -> list[Tool]:
    """
    Returns a list of tools for the CloudWatch connector.
    """
    target = CloudWatchTarget(**target.model_dump())
    return CloudWatchConnectorTools(
        config=config,
        target=target,
        secrets=secrets
    ).get_tools()

async def _get_secrets(config: CloudWatchConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> CloudWatchSecrets | None:
    if user_token is not None:
        raise ValueError("User token is not supported for salesforce at this time")

    return CloudWatchSecrets()


CloudWatchConnector = Connector(
    id=ConnectorIdEnum.CLOUDWATCH,
    display_name="CloudWatch",
    description="Amazon CloudWatch monitoring and observability service.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "cloudwatch.svg")),
    config_cls=CloudWatchConnectorConfig,
    query_target_type=CloudWatchTarget,
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options,
)
