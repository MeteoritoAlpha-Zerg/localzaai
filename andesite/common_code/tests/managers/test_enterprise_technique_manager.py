from unittest.mock import AsyncMock, Mock

import pytest
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from pymongo import UpdateOne

from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)
from common.models.mitre import (
    MitreEnterpriseTechnique,
    MitreEnterpriseTechniquePage,
    MitreEnterpriseTechniqueUpdate,
)

technique_model = MitreEnterpriseTechnique(
    tid="AN-1001",
    priority=10,
    matrix_tactic="Multiple Possible",
    name="test",
    description="test",
    created="23 April 2025",
    last_modified="23 April 2026",
    version="1.0",
    is_sub_technique="false",
    stix_id="none",
)

technique_document = technique_model.to_mongo()


@pytest.fixture()
def etm_instance():
    return EnterpriseTechniqueManager()


async def test_no_initialization_error(etm_instance):
    with pytest.raises(ValueError, match="MongoDb client is not initialized."):
        await etm_instance.get_technique("id")


@pytest.fixture()
async def mongo_collection(etm_instance):
    collection = AsyncMock(spec=AgnosticCollection)
    collection.insert_many = AsyncMock()
    collection.create_index = AsyncMock()
    await etm_instance.initialize(collection)
    return collection


@pytest.mark.parametrize(
    "document,expected_result",
    [
        (technique_document, technique_model),
        (None, None),
    ],
)
async def test_get_technique(etm_instance, mongo_collection, document, expected_result):
    mock = AsyncMock(return_value=document)
    mongo_collection.find_one = mock
    technique = await etm_instance.get_technique("AN-1001")
    mock.assert_awaited_once_with({"tid": "AN-1001"})
    assert technique == expected_result


async def test_list_techniques(etm_instance, mongo_collection):
    find_mock = Mock()
    find_mock.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[technique_document])
    mongo_collection.find = find_mock
    mongo_collection.count_documents = AsyncMock(return_value=1)

    page, page_size, expected_skip = 2, 3, 3
    result = await etm_instance.list_techniques(page, page_size)
    skip_call = mongo_collection.find.return_value.skip
    skip_call.assert_called_once_with(expected_skip)
    skip_call.return_value.limit.assert_called_once_with(page_size)
    skip_call.return_value.limit.return_value.to_list.assert_awaited_once()
    assert result == MitreEnterpriseTechniquePage(
        page=page, page_size=page_size, total_count=1, results=[technique_model]
    )


async def test_list_techniques_priorities(etm_instance, mongo_collection):
    cursor_mock = AsyncMock()
    cursor_mock.__aiter__.return_value = [
        {"tid": "A", "priority": "200"},
        {"tid": "B", "priority": "100"},
    ]
    find_mock = Mock(return_value=cursor_mock)
    mongo_collection.find = find_mock

    result = await etm_instance.get_technique_priorities(1000)
    mongo_collection.find.assert_called_once_with(projection={"tid": True, "priority": True, "_id": False})
    cursor_mock.limit.assert_called_once_with(1000)
    assert result.mapping == {"A": 200, "B": 100}


async def test_list_techniques_priorities_no_limit(etm_instance, mongo_collection):
    cursor_mock = AsyncMock()
    cursor_mock.limit = AsyncMock()
    cursor_mock.__aiter__.return_value = [
        {"tid": "A", "priority": "200"},
        {"tid": "B", "priority": "100"},
    ]
    find_mock = Mock(return_value=cursor_mock)
    mongo_collection.find = find_mock
    result = await etm_instance.get_technique_priorities()
    mongo_collection.find.assert_called_once_with(projection={"tid": True, "priority": True, "_id": False})
    cursor_mock.limit.assert_not_called()
    assert result.mapping == {"A": 200, "B": 100}


@pytest.mark.parametrize(
    "acknowledgment,expected_result",
    [
        (True, {"tid": technique_model.tid, "status": "created"}),
        (False, None),
    ],
)
async def test_create_technique(etm_instance, mongo_collection, acknowledgment, expected_result):
    mongo_collection.insert_one = AsyncMock(return_value=Mock(acknowledged=acknowledgment))
    result = await etm_instance.create_technique(technique_model)
    assert result == expected_result


async def test_update_technique(etm_instance, mongo_collection):
    db_result = Mock()
    mock = AsyncMock(return_value=db_result)
    mongo_collection.find_one_and_update = mock
    result = await etm_instance.update_technique(technique_model.tid, technique_model)
    mock.assert_awaited_once_with({"tid": technique_model.tid}, {"$set": technique_document}, return_document=True)
    assert result == db_result


async def test_update_technique_batch(etm_instance, mongo_collection):
    document_count = 3
    mock = AsyncMock(
        return_value=Mock(
            matched_count=document_count,
            modified_count=document_count,
            upserted_count=0,
        )
    )
    mongo_collection.bulk_write = mock
    result = await etm_instance.update_technique_batch(techniques=[technique_model] * document_count)
    mock.assert_awaited_once_with(
        [
            UpdateOne(
                filter={"tid": technique_model.tid},
                update={"$set": technique_document},
                upsert=True,
            )
        ]
        * document_count
    )
    assert result == MitreEnterpriseTechniqueUpdate(
        message="Successfully updated documents.",
        matched_count=document_count,
        modified_count=document_count,
    )
