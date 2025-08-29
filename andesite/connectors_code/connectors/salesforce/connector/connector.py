import os
from pathlib import Path

from pydantic import SecretStr
from common.models.tool import Tool
from connectors.connector import Connector
from connectors.cache import Cache
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.salesforce.connector.config import SalesforceConnectorConfig
from connectors.salesforce.connector.target import SalesforceTarget
from connectors.salesforce.connector.secrets import SalesforceSecrets
from connectors.salesforce.connector.tools import SalesforceConnectorTools
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from simple_salesforce.api import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed


def _get_instance(config: SalesforceConnectorConfig, secrets: SalesforceSecrets) -> Salesforce:
    """
    Create a Salesforce client instance using simple-salesforce.
    """
    client = Salesforce(
        username=secrets.username.get_secret_value(),
        password=secrets.password.get_secret_value(),
        security_token=secrets.security_token.get_secret_value(),
        domain=config.domain,
        version=config.api_version
    )
    return client

async def _check_connection(config: SalesforceConnectorConfig, secrets: SalesforceSecrets) -> bool:
    """
    Check that we can authenticate and describe the Salesforce schema.
    """
    try:
        client = _get_instance(config, secrets)
        client.describe()
        return True
    except SalesforceAuthenticationFailed:
        return False

async def _get_query_target_options(
    config: SalesforceConnectorConfig, secrets: SalesforceSecrets
) -> ConnectorQueryTargetOptions:
    """
    Retrieve the list of Salesforce objects available for querying.
    """
    client = _get_instance(config, secrets)
    desc = client.describe()
    if desc is None:
        raise ValueError("Failed to describe Salesforce schema: received None")
    sobjects = desc.get("sobjects", [])
    # Only include queryable objects
    object_names = [obj.get("name") for obj in sobjects if obj.get("queryable", False)]
    definitions = [ScopeTargetDefinition(name="objects", multiselect=True)]
    selectors = [ScopeTargetSelector(type="objects", values=object_names)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)

def _get_tools(
    config: SalesforceConnectorConfig,
    target: SalesforceTarget,
    secrets: SalesforceSecrets,
    cache: Cache | None
) -> list[Tool]:
    """
    Instantiate the tool set for Salesforce, passing the client into the tools.
    """
    client = _get_instance(config, secrets)
    return SalesforceConnectorTools(client, target, secrets).get_tools()

async def _get_secrets(config: SalesforceConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> SalesforceSecrets | None:
    if user_token is not None:
        raise ValueError("User token is not supported for salesforce at this time")

    username = config.username.decrypt(encryption_key=encryption_key)
    password = config.password.decrypt(encryption_key=encryption_key)
    security_token = config.security_token.decrypt(encryption_key=encryption_key)
    if username is None or password is None or security_token is None:
        return None

    return SalesforceSecrets(username=username, password=password, security_token=security_token,)



# Construct the SalesforceConnector with only query and tools capabilities
SalesforceConnector = Connector(
    id=ConnectorIdEnum.SALESFORCE,
    beta=True,
    display_name="Salesforce",
    description="Salesforce CRM connector providing object enumeration and record retrieval.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "salesforce.svg")),
    config_cls=SalesforceConnectorConfig,
    query_target_type=SalesforceTarget,
    get_tools=_get_tools,
    get_secrets=_get_secrets,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options,
)
