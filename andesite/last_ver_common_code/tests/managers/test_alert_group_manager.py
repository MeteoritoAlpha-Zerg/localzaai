from datetime import datetime
from unittest.mock import AsyncMock, Mock
from common.models.alerts import AbbreviatedAlert
import pytest
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from connectors.connector_id_enum import ConnectorIdEnum

from common.managers.alert_groups.alert_group_manager import (
    AlertGroupException,
    AlertGroupManager,
)
from common.managers.alert_groups.alert_group_model import (
    AlertGroup,
    AlertGroupDeleteResult,
    AlertGroupStatus,
)


def get_test_alert_group(id: str, title: str = "test"):
    return AlertGroup(
        id=id,
        title=title,
        total_alerts_all_time=1,
        description="test3",
        time=datetime.now(),
        priority=1,
        alerts=[
            AbbreviatedAlert(
                id="1234",
                connector=ConnectorIdEnum.SPLUNK,
                time=datetime.now(),
                description="foo",
                title="test1",
            )
        ],
        alert_ids=["1234"],
        similarity_score=2.0,
        explanation="test5",
    )


@pytest.fixture
async def mongo_collection():
    return AsyncMock(autospec=AgnosticCollection)


@pytest.fixture
async def manager(mongo_collection):
    manager = AlertGroupManager()
    mongo_collection.create_index = AsyncMock()
    await manager.initialize(mongo_collection)
    return manager


async def test_group_does_not_exist(manager, mongo_collection):
    mongo_collection.find_one = AsyncMock(return_value=None)
    result = await manager.get_alert_group_async("foo")
    assert result is None


async def test_get_group_exists(manager, mongo_collection):
    test_group = get_test_alert_group("test1")
    mock = AsyncMock(return_value=test_group.to_mongo())
    mongo_collection.find_one = mock
    result = await manager.get_alert_group_async("test1")
    mock.assert_awaited_once_with({"_id": "test1"})
    assert result == test_group


@pytest.mark.parametrize(
    "mock,expected_result",
    [
        (
            AsyncMock(return_value=Mock(deleted_count=1)),
            AlertGroupDeleteResult(deleted_count=1, total_count=1),
        ),
        (
            AsyncMock(return_value=Mock(deleted_count=0)),
            AlertGroupDeleteResult(deleted_count=0, total_count=1),
        ),
    ],
)
async def test_delete_group_exists(manager, mongo_collection, mock, expected_result):
    mongo_collection.delete_many = mock
    result = await manager.delete_alert_groups_async(["test1"])
    mock.assert_awaited_once_with({"_id": {"$in": ["test1"]}})
    assert result == expected_result


async def test_delete_group_no_groups(manager, mongo_collection):
    result = await manager.delete_alert_groups_async([])
    assert result == AlertGroupDeleteResult(deleted_count=0, total_count=0)


async def test_delete_group_unacknowledged(manager, mongo_collection):
    mock = AsyncMock(return_value=Mock(acknowledged=False))
    mongo_collection.delete_many = mock
    with pytest.raises(
        AlertGroupException, match="MongoDB did not acknowledge delete request"
    ):
        await manager.delete_alert_groups_async("test1")
        mock.assert_awaited_once_with({"$in": ["test1"]})


async def test_get_alert_groups(manager, mongo_collection):
    test_group1 = get_test_alert_group("test1")
    test_group2 = get_test_alert_group("test2")
    aggregate_mock = Mock()
    aggregate_mock.return_value.to_list = AsyncMock(
        return_value=[test_group1.to_mongo(), test_group2.to_mongo()]
    )
    mongo_collection.aggregate = aggregate_mock
    current_time = datetime.now()
    result = await manager.get_alert_groups_async(skip=1, limit=20, before=current_time)
    aggregate_mock.assert_called_once_with(
        [{"$skip": 1}, {"$limit": 20}, {"$match": {"time": {"$lt": current_time}}}]
    )
    assert result == [test_group1, test_group2]


async def test_get_alert_groups_no_documents(manager, mongo_collection):
    aggregate_mock = Mock()
    aggregate_mock.return_value.to_list = AsyncMock(return_value=None)
    mongo_collection.aggregate = aggregate_mock
    current_time = datetime.now()
    result = await manager.get_alert_groups_async(skip=1, limit=20, after=current_time)
    aggregate_mock.assert_called_once_with(
        [{"$skip": 1}, {"$limit": 20}, {"$match": {"time": {"$gte": current_time}}}]
    )
    assert result == []


async def test_upsert_group(manager, mongo_collection):
    test_group = get_test_alert_group("test1", title="original")
    mock = AsyncMock(return_value=test_group.to_mongo())
    mongo_collection.find_one_and_update = mock
    result = await manager.upsert_alert_group_async(test_group)
    mock.assert_awaited_once_with(
        {"_id": "test1"},
        {"$set": test_group.to_mongo()},
        upsert=True,
        return_document=True,
    )
    assert result == test_group


async def test_update_alert_group_status(manager, mongo_collection):
    test_group = get_test_alert_group("test1", title="original")
    mock = AsyncMock(return_value=test_group.to_mongo())
    mongo_collection.find_one_and_update = mock
    await manager.upsert_alert_group_async(test_group)
    await manager.update_alert_group_status("test1", "read")
    mock.assert_awaited_with(
        {"_id": "test1"},
        {"$set": {"status": "read"}},
        return_document=True,
    )


async def test_alert_group_model_to_mongo():
    current_time = datetime.now()
    group = {
        "id": "test1",
        "status": "open",
        "title": "testTitle",
        "description": "Test2",
        "time": str(current_time),
        "priority": 1,
        "total_alerts_all_time": 1,
        "alerts": [
            {
                "connector": "splunk",
                "description": "foo",
                "doc_id": None,
                "doc_name": None,
                "id": "1234",
                "priority": 999,
                "time": current_time,
                "title": "splunk alert",
            }
        ],
        "alert_ids": ["1234"],
        "similarity_score": 2.0,
        "explanation": "test5",
    }
    model = AlertGroup(**group)
    assert model == AlertGroup(
        id="test1",
        title="testTitle",
        status=AlertGroupStatus.OPEN,
        description="Test2",
        time=current_time,
        priority=1,
        total_alerts_all_time=1,
        alerts=[
            AbbreviatedAlert(
                id="1234",
                connector=ConnectorIdEnum.SPLUNK,
                time=current_time,
                description="foo",
                title="splunk alert",
            )
        ],
        alert_ids=["1234"],
        similarity_score=2.0,
        explanation="test5",
    )


async def test_alert_group_model_from_mongo():
    current_time = datetime.now()
    group = AlertGroup(
        id="test1",
        title="testTitle",
        description="Test2",
        time=current_time,
        priority=1,
        total_alerts_all_time=1,
        alerts=[
            AbbreviatedAlert(
                id="1234",
                connector=ConnectorIdEnum.SPLUNK,
                time=current_time,
                description="foo",
                title="splunk alert",
            )
        ],
        alert_ids=["1234"],
        similarity_score=2.0,
        explanation="test5",
    )
    assert group.to_mongo() == {
        "_id": "test1",
        "title": "testTitle",
        "description": "Test2",
        "status": "open",
        "time": current_time,
        "priority": 1,
        "alert_ids": ["1234"],
        "total_alerts_all_time": 1,
        "alerts": [
            {
                "connector": "splunk",
                "description": "foo",
                "doc_id": None,
                "doc_name": None,
                "id": "1234",
                "priority": 999,
                "time": current_time,
                "title": "splunk alert",
            }
        ],
        "similarity_score": 2.0,
        "explanation": "test5",
    }
