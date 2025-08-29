import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.task_metadata.task_metadata_manager import (
    TaskMetadataManager,
)
from common.managers.task_metadata.task_metadata_model import (
    TaskMetadata,
    TaskStatusEnum,
)


@pytest.fixture(autouse=True)
async def task_metadata_manager():
    manager = TaskMetadataManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["task_metadatas"]
    # Uncomment for testing against local MongoDB
    # from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
    # await MongoDbClient.initialize(MongoDbConfig())
    # collection = MongoDbClient.get_collection("metamorph_test", "task_metadatas")
    await manager.initialize(collection)
    return manager


@pytest.mark.asyncio
async def test_metadatas_not_exist(
    task_metadata_manager: TaskMetadataManager,
) -> None:
    metadatas = await task_metadata_manager.get_task_metadatas_async()
    assert len(metadatas) == 0


@pytest.mark.asyncio
async def test_get_all_metadatas(
    task_metadata_manager: TaskMetadataManager,
) -> None:
    task_id = "test_id"
    task_name = "test_name"
    metadata = TaskMetadata(task_id=task_id, task_name=task_name)
    await task_metadata_manager.upsert_task_metadata_async(metadata)

    m = await task_metadata_manager.get_task_metadatas_async()
    assert len(m) == 1


@pytest.mark.asyncio
async def test_set_metadata(task_metadata_manager) -> None:
    task_id = "test_id"
    task_name = "test_name"
    metadata = TaskMetadata(task_id=task_id, task_name=task_name)
    await task_metadata_manager.upsert_task_metadata_async(metadata)
    task = await task_metadata_manager.get_task_metadata_async(task_id)

    assert task.status == TaskStatusEnum.PENDING

    metadata.status = TaskStatusEnum.SUCCESS
    new_metadata = await task_metadata_manager.upsert_task_metadata_async(metadata)
    assert new_metadata.status == TaskStatusEnum.SUCCESS


@pytest.mark.asyncio
async def test_delete_metadatas(task_metadata_manager) -> None:
    task_id = "test_id"
    task_name = "test_name"
    metadata = TaskMetadata(task_id=task_id, task_name=task_name)
    task = await task_metadata_manager.upsert_task_metadata_async(metadata)

    await task_metadata_manager.delete_task_metadatas_async(task_ids=[task.task_id])

    all_metadatas = await task_metadata_manager.get_task_metadatas_async()
    assert len(all_metadatas) == 0
