from unittest.mock import AsyncMock, patch

import pytest
from common.managers.dataset_descriptions.dataset_description_model import DatasetDescription
from common.models.connector_id_enum import ConnectorIdEnum

from connectors.confluence.connector.config import ConfluenceConnectorConfig
from connectors.confluence.connector.connector import _merge_data_dictionary
from connectors.confluence.connector.secrets import ConfluenceSecrets


@pytest.mark.asyncio
async def test_merge_data_dictionary_filters_by_path_prefix():
    encryption_key = "dummy-key"

    config = ConfluenceConnectorConfig.model_validate(
        {
            "id": ConnectorIdEnum.CONFLUENCE,
            "url": "https://fake-confluence.com",
            "email": "fake-confluence@confluence.com",
            "api_key": "fake-api-key",
        },
        context={"encryption_key": encryption_key},
    )

    secrets = ConfluenceSecrets.model_validate(
        {"api_key": "fake-api-key"},
        context={"encryption_key": encryption_key},
    )

    existing = []

    with (
        patch("connectors.confluence.connector.connector._get_space_keys", AsyncMock(return_value=["Eng", "HR"])),
        patch(
            "connectors.confluence.connector.connector._get_page_descriptions_for_space",
            AsyncMock(
                return_value=[
                    DatasetDescription(
                        connector=ConnectorIdEnum.CONFLUENCE,
                        path=["Eng", "Overview"],
                        description="This is an overview page!",
                    )
                ]
            ),
        ),
    ):
        result = await _merge_data_dictionary(
            config=config,
            secrets=secrets,
            existing_dataset_descriptions=existing,
            path_prefix=["Eng"],
        )

        assert ["Eng"] in [r.path for r in result]
        assert ["Eng", "Overview"] in [r.path for r in result]
        assert all(path[0] == "Eng" for path in [r.path for r in result])


@pytest.mark.asyncio
async def test_merge_data_dictionary_returns_all_when_no_path_prefix():
    encryption_key = "dummy-key"

    config = ConfluenceConnectorConfig.model_validate(
        {
            "id": ConnectorIdEnum.CONFLUENCE,
            "url": "https://fake-confluence.com",
            "email": "fake-confluence@confluence.com",
            "api_key": "fake-api-key",
        },
        context={"encryption_key": encryption_key},
    )

    secrets = ConfluenceSecrets.model_validate(
        {"api_key": "fake-api-key"},
        context={"encryption_key": encryption_key},
    )

    existing = []

    with (
        patch("connectors.confluence.connector.connector._get_space_keys", AsyncMock(return_value=["Eng", "HR"])),
        patch(
            "connectors.confluence.connector.connector._get_page_descriptions_for_space",
            AsyncMock(
                side_effect=[
                    [
                        DatasetDescription(
                            connector=ConnectorIdEnum.CONFLUENCE, path=["Eng", "Overview"], description="Intro"
                        )
                    ],
                    [
                        DatasetDescription(
                            connector=ConnectorIdEnum.CONFLUENCE, path=["HR", "PTO"], description="HR info"
                        )
                    ],
                ]
            ),
        ),
    ):
        result = await _merge_data_dictionary(
            config=config,
            secrets=secrets,
            existing_dataset_descriptions=existing,
            path_prefix=None,
        )

        assert ["Eng"] in [r.path for r in result]
        assert ["HR"] in [r.path for r in result]
        assert ["Eng", "Overview"] in [r.path for r in result]
        assert ["HR", "PTO"] in [r.path for r in result]


@pytest.mark.asyncio
async def test_merge_data_dictionary_path_prefix_normalization():
    encryption_key = "dummy-key"

    config = ConfluenceConnectorConfig.model_validate(
        {
            "id": ConnectorIdEnum.CONFLUENCE,
            "url": "https://fake-confluence.com",
            "email": "fake-confluence@confluence.com",
            "api_key": "fake-api-key",
        },
        context={"encryption_key": encryption_key},
    )

    secrets = ConfluenceSecrets.model_validate(
        {"api_key": "fake-api-key"},
        context={"encryption_key": encryption_key},
    )

    existing = []

    with (
        patch("connectors.confluence.connector.connector._get_space_keys", AsyncMock(return_value=["Engineering"])),
        patch(
            "connectors.confluence.connector.connector._get_page_descriptions_for_space",
            AsyncMock(
                return_value=[
                    DatasetDescription(
                        connector=ConnectorIdEnum.CONFLUENCE, path=["Engineering", "VectorDB"], description="Some page"
                    )
                ]
            ),
        ),
    ):
        result = await _merge_data_dictionary(
            config=config,
            secrets=secrets,
            existing_dataset_descriptions=existing,
            path_prefix=["engineering"],  # lowercase only
        )

        assert ["Engineering"] in [r.path for r in result]
        assert ["Engineering", "VectorDB"] in [r.path for r in result]


@pytest.mark.asyncio
async def test_merge_data_dictionary_path_prefix_startswith_behavior():
    encryption_key = "dummy-key"

    config = ConfluenceConnectorConfig.model_validate(
        {
            "id": ConnectorIdEnum.CONFLUENCE,
            "url": "https://fake-confluence.com",
            "email": "fake-confluence@confluence.com",
            "api_key": "fake-api-key",
        },
        context={"encryption_key": encryption_key},
    )

    secrets = ConfluenceSecrets.model_validate(
        {"api_key": "fake-api-key"},
        context={"encryption_key": encryption_key},
    )

    existing = []

    with (
        patch(
            "connectors.confluence.connector.connector._get_space_keys",
            AsyncMock(return_value=["Eng", "Engineering", "EngTools", "HR"]),
        ),
        patch(
            "connectors.confluence.connector.connector._get_page_descriptions_for_space",
            AsyncMock(
                side_effect=[
                    [DatasetDescription(connector=ConnectorIdEnum.CONFLUENCE, path=["Eng", "Page"], description="")],
                    [
                        DatasetDescription(
                            connector=ConnectorIdEnum.CONFLUENCE, path=["Engineering", "Page"], description=""
                        )
                    ],
                    [
                        DatasetDescription(
                            connector=ConnectorIdEnum.CONFLUENCE, path=["EngTools", "Tooling"], description=""
                        )
                    ],
                    [DatasetDescription(connector=ConnectorIdEnum.CONFLUENCE, path=["HR", "PTO"], description="")],
                ]
            ),
        ),
    ):
        result = await _merge_data_dictionary(
            config=config,
            secrets=secrets,
            existing_dataset_descriptions=existing,
            path_prefix=["Eng"],
        )

        paths = [r.path for r in result]
        assert ["Eng"] in paths
        assert ["Eng", "Page"] in paths
        assert ["Engineering"] not in paths
        assert ["Engineering", "Page"] not in paths
        assert ["EngTools"] not in paths
        assert ["EngTools", "Tooling"] not in paths
