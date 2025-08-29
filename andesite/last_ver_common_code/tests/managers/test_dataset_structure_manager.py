import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure


@pytest.fixture(autouse=True)
async def dataset_structure_manager():
    manager = DatasetStructureManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["dataset_structures"]
    # Uncomment for testing against local MongoDB
    # from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
    # await MongoDbClient.initialize(MongoDbConfig())
    # collection = MongoDbClient.get_collection("metamorph_test", "dataset_structures")
    await manager.initialize(collection)
    return manager


@pytest.mark.asyncio
async def test_dataset_structure_not_exist(
    dataset_structure_manager: DatasetStructureManager,
) -> None:
    ds = await dataset_structure_manager.get_dataset_structure_async(
        "nonexistent", "nonexistent"
    )
    assert ds is None


@pytest.mark.asyncio
async def test_get_all_dataset_structures(
    dataset_structure_manager: DatasetStructureManager,
) -> None:
    connector = "test_connector"
    dataset = "test_dataset"
    dataset_structure = DatasetStructure(
        connector=connector, dataset=dataset, attributes="test attributes"
    )
    await dataset_structure_manager.set_dataset_structure_async(dataset_structure)

    ds = await dataset_structure_manager.get_all_dataset_structures_async(connector)
    assert len(ds) == 1


@pytest.mark.asyncio
async def test_set_dataset_structure(dataset_structure_manager) -> None:
    connector = "test_connector"
    dataset = "test_dataset"
    dataset_structure = DatasetStructure(
        connector=connector, dataset=dataset, attributes="test attributes"
    )
    new_dataset_structure = await dataset_structure_manager.set_dataset_structure_async(
        dataset_structure
    )

    assert new_dataset_structure.attributes == dataset_structure.attributes

    # Check setting same dataset structure
    new_dataset_structure = await dataset_structure_manager.set_dataset_structure_async(
        dataset_structure.model_copy()
    )
    assert new_dataset_structure.attributes == dataset_structure.attributes

    dataset_structure = await dataset_structure_manager.get_dataset_structure_async(
        connector, dataset
    )
    assert dataset_structure is not None


@pytest.mark.asyncio
async def test_delete_dataset_structure(dataset_structure_manager) -> None:
    connector = "test_connector"
    dataset = "test_dataset"
    dataset_structure = DatasetStructure(
        connector=connector, dataset=dataset, attributes="test structure"
    )
    new_dataset_structure = await dataset_structure_manager.set_dataset_structure_async(
        dataset_structure
    )

    assert new_dataset_structure.attributes == dataset_structure.attributes

    # Check setting same dataset structure
    new_dataset_structure = (
        await dataset_structure_manager.delete_dataset_structures_async(
            dataset_structure.connector, [dataset_structure.dataset]
        )
    )

    assert (
        await dataset_structure_manager.get_dataset_structure_async(connector, dataset)
        is None
    )
