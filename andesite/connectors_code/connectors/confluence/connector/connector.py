import os
from pathlib import Path
from typing import Optional

import httpx
from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from pydantic import SecretStr

from connectors.cache import Cache
from connectors.confluence.connector.config import ConfluenceConnectorConfig
from connectors.confluence.connector.secrets import ConfluenceSecrets
from connectors.confluence.connector.target import ConfluenceTarget
from connectors.confluence.connector.tools import ConfluenceConnectorTools
from connectors.connector import Connector
from connectors.query_target_options import ConnectorQueryTargetOptions

logger = Logging.get_logger(__name__)


async def _check_confluence_connection(config: ConfluenceConnectorConfig, secrets: ConfluenceSecrets) -> bool:
    """Check connection to Confluence by retrieving one space using the REST API."""
    url = f"{config.url.rstrip('/')}/rest/api/space"
    auth = (config.email, secrets.api_key.get_secret_value())
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, auth=auth, params={"limit": 1})
            response.raise_for_status()
        return True
    except Exception:
        return False


async def _get_query_target_options(
    config: ConfluenceConnectorConfig, secrets: ConfluenceSecrets
) -> ConnectorQueryTargetOptions:
    """Retrieve query target options by listing Confluence spaces."""
    url = f"{config.url.rstrip('/')}/rest/api/space"
    auth = (config.email, secrets.api_key.get_secret_value())
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, auth=auth, params={"limit": 50})
        response.raise_for_status()
        data = response.json()
        spaces = data.get("results", [])
        space_keys = [space.get("key") for space in spaces if "key" in space]
    from connectors.query_target_options import ConnectorQueryTargetOptions, ScopeTargetDefinition, ScopeTargetSelector

    definitions = [ScopeTargetDefinition(name="space_keys", multiselect=True)]
    selectors = [ScopeTargetSelector(type="space_keys", values=space_keys)]
    return ConnectorQueryTargetOptions(definitions=definitions, selectors=selectors)


def _get_tools(
    config: ConfluenceConnectorConfig, target: ConfluenceTarget, secrets: ConfluenceSecrets, cache: Cache | None
) -> list[Tool]:
    return ConfluenceConnectorTools(target, config, secrets).get_tools()


async def _get_space_keys(
    client: httpx.AsyncClient,
    config: ConfluenceConnectorConfig,
    auth: tuple[str, str],
    max_pages: int = 5000,
    limit: int = 100,
) -> list[str]:
    all_space_keys = []
    start = 0
    page_count = 0
    space_url = f"{config.url.rstrip('/')}/rest/api/space"

    while page_count < max_pages:
        params = {"limit": str(limit), "start": str(start)}
        try:
            resp = await client.get(space_url, auth=auth, params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                break

            all_space_keys.extend([s["key"] for s in results if "key" in s])

            if len(results) < limit:
                break

            start += limit
            page_count += 1

        except Exception as e:
            logger().warning(f"Failed to fetch space keys from Confluence: {e}")
            break

    if page_count == max_pages:
        logger().warning(f"Reached max page limit ({max_pages}) when fetching Confluence space keys")

    return all_space_keys


async def _get_page_descriptions_for_space(
    client: httpx.AsyncClient,
    config: ConfluenceConnectorConfig,
    auth: tuple[str, str],
    space_key: str,
    existing_desc_dict: dict[tuple[str, ...], str],
    max_pages: int = 5000,
    limit: int = 100,
) -> list[DatasetDescription]:
    page_descriptions: list[DatasetDescription] = []
    start = 0
    page_count = 0
    page_url = f"{config.url.rstrip('/')}/rest/api/content"

    while page_count < max_pages:
        params = {
            "spaceKey": space_key,
            "type": "page",
            "limit": str(limit),
            "start": str(start),
            "expand": "ancestors",
        }

        try:
            resp = await client.get(page_url, auth=auth, params=params)
            resp.raise_for_status()
            pages = resp.json().get("results", [])

            for page in pages:
                page_id = page.get("id")
                title = page.get("title", f"Page {page_id}")
                ancestors = page.get("ancestors", [])
                path = [space_key] + [a["title"] for a in ancestors] + [title]

                description = existing_desc_dict.get(tuple(path), "")

                page_descriptions.append(
                    DatasetDescription(
                        connector=ConnectorIdEnum.CONFLUENCE,
                        path=path,
                        description=description,
                    )
                )

            if len(pages) < limit:
                break

            start += limit
            page_count += 1

        except Exception as e:
            logger().warning(f"Failed to retrieve pages for space {space_key} at start={start}: {e}")
            break

    if page_count == max_pages:
        logger().warning(f"Reached max page limit ({max_pages}) for space {space_key}")

    return page_descriptions


async def _merge_data_dictionary(
    config: ConfluenceConnectorConfig,
    secrets: ConfluenceSecrets,
    existing_dataset_descriptions: list[DatasetDescription],
    path_prefix: Optional[list[str]] = None,
) -> list[DatasetDescription]:
    auth = (config.email, secrets.api_key.get_secret_value())
    existing_descriptions_dict = {tuple(desc.path): desc.description or "" for desc in existing_dataset_descriptions}

    async with httpx.AsyncClient(timeout=5) as client:
        all_space_keys = await _get_space_keys(client, config, auth)
        data_dictionary: list[DatasetDescription] = []

        normalized_path_prefix = [p.strip().lower() for p in path_prefix or []]

        for space_key in all_space_keys:
            normalized_space_key = space_key.strip().lower()

            if normalized_path_prefix and (normalized_space_key,) != tuple(normalized_path_prefix):
                continue

            space_path = [space_key]
            space_description = existing_descriptions_dict.get(tuple(space_path), "")
            data_dictionary.append(
                DatasetDescription(
                    connector=ConnectorIdEnum.CONFLUENCE,
                    path=space_path,
                    description=space_description,
                )
            )

            page_descriptions = await _get_page_descriptions_for_space(
                client, config, auth, space_key, existing_descriptions_dict
            )
            data_dictionary.extend(page_descriptions)

        return data_dictionary


async def _get_secrets(
    config: ConfluenceConnectorConfig, encryption_key: str, user_token: SecretStr | None
) -> ConfluenceSecrets | None:
    api_key = user_token if user_token is not None else config.api_key.decrypt(encryption_key=encryption_key)

    if api_key is None:
        return None

    return ConfluenceSecrets(
        api_key=api_key,
    )


ConfluenceConnector = Connector(
    id=ConnectorIdEnum.CONFLUENCE,
    display_name="Confluence",
    description="Confluence is a collaboration wiki tool that enables teams to share knowledge.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "confluence.svg")),
    config_cls=ConfluenceConnectorConfig,
    query_target_type=ConfluenceTarget,
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    check_connection=_check_confluence_connection,
    get_query_target_options=_get_query_target_options,
    merge_data_dictionary=_merge_data_dictionary,
)
