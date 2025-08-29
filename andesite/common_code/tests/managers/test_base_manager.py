from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from pymongo.errors import DuplicateKeyError, PyMongoError

from common.managers.base.base_manager import Manager
from common.models.mongo import DbDocument, DbError, DbException


class Document(DbDocument):
    data: str


test_id = ObjectId()
test_id_str = str(test_id)
test_document: dict[str, Any] = {"_id": test_id, "data": "test"}
test_model = Document(id=test_document["_id"], data=test_document["data"])
collection_name = "test_collection"


@pytest.fixture()
async def collection():
    collection = AsyncMock(spec=AgnosticCollection)
    collection.name = collection_name
    return collection


@pytest.mark.parametrize(
    "document,expected_result",
    [
        (test_document, test_model),
        (None, None),
    ],
)
async def test_find_one(collection, document, expected_result):
    mock = AsyncMock(return_value=document)
    collection.find_one = mock
    manager = Manager(collection, Document)
    document = await manager.find_one(test_id_str)
    mock.assert_awaited_once_with(filter={"_id": test_id}, projection=None)
    assert document == expected_result


async def test_find_one_projection(collection):
    mock = AsyncMock(return_value=test_document)
    collection.find_one = mock
    manager = Manager(collection, Document)
    expected_projection = {"data": 1}
    document = await manager.find_one_projection(
        object_id=test_id_str, projection=expected_projection, document_cls=Document
    )
    mock.assert_awaited_once_with(filter={"_id": test_id}, projection=expected_projection)
    assert document == test_model


async def test_find_many(collection):
    length = 3
    cursor_mock = AsyncMock()
    cursor_mock.__aiter__.return_value = [test_document] * length
    mock = Mock(return_value=cursor_mock)
    collection.find = mock
    manager = Manager(collection, Document)
    query = {"data": "test"}

    documents = await manager.find_many(query)
    mock.assert_called_once_with(query, None)
    assert documents == [test_model] * length


async def test_find_many_no_results(collection):
    cursor_mock = AsyncMock()
    cursor_mock.__aiter__.return_value = []
    mock = Mock(return_value=cursor_mock)
    collection.find = mock
    manager = Manager(collection, Document)
    documents = await manager.find_many({})
    mock.assert_called_once_with({}, None)
    assert len(documents) == 0


async def test_find_many_projection(collection):
    length = 3
    cursor_mock = AsyncMock()
    cursor_mock.__aiter__.return_value = [test_document] * length
    mock = Mock(return_value=cursor_mock)
    collection.find = mock
    manager = Manager(collection, Document)
    expected_projection = {"data": 1}
    documents = await manager.find_many_projection({}, expected_projection, Document)
    mock.assert_called_once_with({}, expected_projection)
    assert documents == [test_model] * length


async def test_insert_one(collection):
    mock = AsyncMock(return_value=Mock(inserted_id=test_id))
    collection.insert_one = mock
    manager = Manager(collection, Document)
    id = await manager.insert_one(Document(id=test_id, data="test"))
    mock.assert_awaited_once_with(test_document)
    assert id == test_id_str


async def test_insert_one_duplicate(collection):
    mock = AsyncMock(side_effect=DuplicateKeyError("foo"))
    collection.insert_one = mock
    manager = Manager(collection, Document)
    with pytest.raises(DbException, match="Document already exists") as excinfo:
        await manager.insert_one(Document(id=test_id, data="test"))
        mock.assert_awaited_once_with(test_document)
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.resource_found


async def test_update_one_duplicate(collection):
    mock = AsyncMock(side_effect=DuplicateKeyError("foo"))
    collection.update_one = mock
    manager = Manager(collection, Document)
    with pytest.raises(DbException, match="Document already exists") as excinfo:
        await manager.update_one(Document(id=test_id, data="test"))
        mock.assert_awaited_once_with(test_document)
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.resource_found


async def test_delete_one(collection):
    mock = AsyncMock(return_value=Mock(deleted_count=1))
    collection.delete_one = mock
    manager = Manager(collection, Document)
    id = await manager.delete_one(test_id_str)
    mock.assert_awaited_once_with({"_id": test_id})
    assert id == test_id_str


async def test_delete_one_not_found(collection):
    mock = AsyncMock(return_value=Mock(deleted_count=0))
    collection.delete_one = mock
    manager = Manager(collection, Document)
    with pytest.raises(DbException, match="Failed to delete document Id=") as excinfo:
        await manager.delete_one(test_id_str)
        mock.assert_awaited_once_with({"_id": test_id})
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.resource_not_found


async def test_update_one(collection):
    mock = AsyncMock(return_value=Mock(matched_count=1))
    collection.update_one = mock
    manager = Manager(collection, Document)
    id = await manager.update_one(test_model)
    mock.assert_awaited_once_with({"_id": test_id}, {"$set": test_document}, upsert=False)
    assert id == test_id_str


async def test_update_one_not_found(collection):
    mock = AsyncMock(return_value=Mock(matched_count=0))
    collection.update_one = mock
    manager = Manager(collection, Document)
    with pytest.raises(DbException, match="Failed to update document Id=") as excinfo:
        await manager.update_one(test_model)
        mock.assert_awaited_once_with({"_id": test_id}, {"$set": test_document}, upsert=False)
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.resource_not_found


@pytest.mark.parametrize(
    "manager_function,db_function,args",
    [
        ("find_one", "find_one", [test_id_str]),
        ("insert_one", "insert_one", [test_model]),
        ("delete_one", "delete_one", [test_id_str]),
        ("update_one", "update_one", [test_model]),
    ],
)
async def test_pymongo_error_handling(collection, manager_function, db_function, args):
    mock = AsyncMock(side_effect=PyMongoError("Some error"))
    with (
        patch.object(collection, db_function, mock),
        pytest.raises(DbException, match="Unexpected DB error") as excinfo,
    ):
        manager = Manager(collection, Document)
        await getattr(manager, manager_function)(*args)
        mock.assert_awaited_once()
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.unknown


async def test_pymongo_error_handling_find(collection):
    cursor_mock = AsyncMock()
    cursor_mock.__aiter__.side_effect = PyMongoError("Some error")
    mock = Mock(return_value=cursor_mock)
    collection.find = mock
    manager = Manager(collection, Document)
    with pytest.raises(DbException, match="Unexpected DB error") as excinfo:
        await manager.find_many({})
        cursor_mock.assert_called_once()
    assert excinfo.value.collection_name == collection_name
    assert excinfo.value.error_type == DbError.unknown
