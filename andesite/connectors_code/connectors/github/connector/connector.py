import os
from pathlib import Path

import httpx
from common.models.connector_id_enum import ConnectorIdEnum
from pydantic import SecretStr

from connectors.connector import Connector
from connectors.cache import Cache
from connectors.github.connector.config import GithubConnectorConfig
from connectors.github.connector.target import GithubTarget
from connectors.github.connector.secrets import GithubSecrets
from connectors.github.connector.tools import GithubConnectorTools
from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector


async def _check_connection(config: GithubConnectorConfig, secrets: GithubSecrets):
    """
    Checks the GitHub connection by invoking the '/user' endpoint.
    Returns True if the response status code is 200.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{config.url}/user", headers={"Authorization": f"token {secrets.access_token.get_secret_value()}"}
            )
        return response.status_code == 200
    except Exception:
        return False


async def _get_query_target_options(config: GithubConnectorConfig, secrets: GithubSecrets) -> ConnectorQueryTargetOptions:
    """
    Retrieves query target options by listing the GitHub repositories for the authenticated user.
    Each repository's ID is used as a dataset path.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{config.url}/user/repos", headers={"Authorization": f"token {secrets.access_token.get_secret_value()}"}
        )
    if response.status_code == 200:
        repos = response.json()
    else:
        repos = []
    repo_ids = [
        str(repo.get("id")) for repo in repos if repo.get("has_issues") and repo.get("open_issues_count", 0) > 0
    ]
    definitions = [ScopeTargetDefinition(name="repository_ids", multiselect=True)]
    selectors = [ScopeTargetSelector(type="repository_ids", values=repo_ids)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


def _get_tools(config: GithubConnectorConfig, target: GithubTarget, secrets: GithubSecrets, cache: Cache | None):
    return GithubConnectorTools(config, target, secrets).get_tools()

async def _get_secrets(config: GithubConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> GithubSecrets | None:
    access_token = user_token if user_token is not None else config.access_token.decrypt(encryption_key=encryption_key)

    if access_token is None:
        return None

    return GithubSecrets(
        access_token=access_token,
    )

GithubConnector = Connector(
    beta=True,
    display_name="GitHub",
    id=ConnectorIdEnum.GITHUB,
    config_cls=GithubConnectorConfig,
    query_target_type=GithubTarget,
    description="GitHub Issues Connector",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "github.svg")),
    get_tools=_get_tools,
    get_secrets=_get_secrets,
    check_connection=_check_connection,
    get_query_target_options=_get_query_target_options,
)
