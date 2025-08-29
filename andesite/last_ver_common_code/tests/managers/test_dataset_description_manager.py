import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from connectors.connector_id_enum import ConnectorIdEnum
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)


@pytest.fixture(autouse=True)
async def dataset_description_manager() -> DatasetDescriptionManager:
    manager = DatasetDescriptionManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["dataset_descriptions"]
    # Uncomment for testing against local MongoDB
    # from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
    # await MongoDbClient.initialize(MongoDbConfig())
    # collection = MongoDbClient.get_collection("metamorph_test", "dataset_descriptions")
    await manager.initialize(collection)
    return manager


@pytest.mark.asyncio
async def test_dataset_description_not_exist(
    dataset_description_manager: DatasetDescriptionManager,
) -> None:
    descriptions = await dataset_description_manager.get_dataset_descriptions_async(
        connector="nonexistent"
    )
    assert len(descriptions) == 0

    descriptions = await dataset_description_manager.get_dataset_descriptions_async(
        connector="splunk", path_prefix=["idefinitelydonotexist12345"]
    )
    assert len(descriptions) == 0


@pytest.mark.asyncio
async def test_set_dataset_description(
    dataset_description_manager: DatasetDescriptionManager,
) -> None:
    connector = ConnectorIdEnum.RAPID7
    dataset_description = DatasetDescription(
        connector=connector,
        path=["test_dataset"],
        description="test description",
    )
    new_dataset_description = (
        await dataset_description_manager.set_dataset_description_async(
            dataset_description
        )
    )

    assert new_dataset_description.description == dataset_description.description

    # Check setting same dataset description
    new_dataset_description = (
        await dataset_description_manager.set_dataset_description_async(
            dataset_description.model_copy()
        )
    )
    assert new_dataset_description.description == dataset_description.description

    dataset_descriptons = (
        await dataset_description_manager.get_dataset_descriptions_async(connector)
    )
    assert len(dataset_descriptons) == 1


@pytest.mark.asyncio
async def test_delete_dataset_description(
    dataset_description_manager: DatasetDescriptionManager,
) -> None:
    connector = ConnectorIdEnum.RAPID7
    dataset_description = DatasetDescription(
        connector=connector,
        path=["test_dataset"],
        description="test description",
    )
    new_dataset_description = (
        await dataset_description_manager.set_dataset_description_async(
            dataset_description
        )
    )

    assert new_dataset_description.description == dataset_description.description

    await dataset_description_manager.delete_dataset_description_async(
        dataset_description.connector,
        dataset_description.path,
    )

    dataset_descriptions = (
        await dataset_description_manager.get_dataset_descriptions_async(connector)
    )
    assert len(dataset_descriptions) == 0
