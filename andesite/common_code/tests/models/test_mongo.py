import pytest
from bson import ObjectId

from common.models.mongo import DbDocument


class MongoId(DbDocument):
    some_data: str


def test_dbdocument_deserialization_from_dict():
    id = ObjectId("67e46fec8b4dfb77b1584a22")
    test_data = "hello"
    expected_document = {
        "_id": ObjectId("67e46fec8b4dfb77b1584a22"),
        "some_data": "hello",
    }
    document = MongoId(**expected_document)
    assert document.id == id
    assert document.some_data == test_data


def test_dbdocument_serialization_with_id_alias():
    expected_id = ObjectId("67e46fec8b4dfb77b1584a22")
    expected_data = "hello"
    document = MongoId(id=expected_id, some_data=expected_data)
    assert document.id == expected_id
    assert document.to_mongo() == {"_id": expected_id, "some_data": expected_data}


@pytest.mark.parametrize(
    "input",
    [
        {"_id": ObjectId("67e46fec8b4dfb77b1584a22"), "some_data": "hello"},
        {"id": ObjectId("67e46fec8b4dfb77b1584a22"), "some_data": "hello"},
    ],
)
def test_dbdocument_to_mongo(input):
    document = MongoId(**input)
    assert document.to_mongo() == {
        "_id": ObjectId("67e46fec8b4dfb77b1584a22"),
        "some_data": "hello",
    }


def test_dbdocument_id_factory():
    document = MongoId(some_data="foo")
    assert document.id
    assert document.some_data == "foo"
    assert document.to_mongo() == {"_id": document.id, "some_data": "foo"}
