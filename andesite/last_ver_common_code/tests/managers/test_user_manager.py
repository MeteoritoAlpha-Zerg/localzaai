import pytest
from unittest.mock import ANY, patch, AsyncMock
from common.clients.mongodb_client import MongoDbClient
from common.managers.user.user_manager import (
    MissingUserEmailError,
    UsersManager,
    UsersManagerConfig,
)
from common.managers.user.user_model import Tokens, User

config = UsersManagerConfig(mongodb_database="mongo_db")


async def test_no_initialization_error():
    with pytest.raises(ValueError, match="MongoDb client is not initialized."):
        await UsersManager.get_user("user_id")


@pytest.fixture
def mongo_client():
    with patch.object(
        MongoDbClient, "get_collection", return_value=AsyncMock()
    ) as mock:
        UsersManager.initialize(config)
        yield mock


@pytest.mark.parametrize(
    "user_payload,expected",
    [
        (
            {
                "_id": "user_id",
                "email": "user@andesite.ai",
                "theme_preference": "light",
                "timezone_preference": "EST",
                "tokens": {"test": "foo"},
            },
            User(
                id="user_id",
                email="user@andesite.ai",
                theme_preference="light",
                timezone_preference="EST",
                tokens=Tokens(test="foo"),  # type: ignore
            ),
        ),
        (None, None),
    ],
)
async def test_get_user(mongo_client, user_payload, expected):
    user_mock = AsyncMock(return_value=user_payload)
    mongo_client.return_value.find_one = user_mock
    user = await UsersManager.get_user("user_id")
    user_mock.assert_awaited_once_with({"_id": "user_id"})
    assert user == expected


async def test_get_or_create_user_from_email_none(mongo_client):
    with pytest.raises(MissingUserEmailError):
        await UsersManager.get_or_create_user_from_email(None)


async def test_get_or_create_user_from_email(mongo_client):
    user_mock = AsyncMock(return_value={"_id": "foo"})
    mongo_client.return_value.find_one_and_update = user_mock
    user_id = await UsersManager.get_or_create_user_from_email("user@andesite.ai")
    user_mock.assert_awaited_once_with(
        {"email": "user@andesite.ai"},
        {
            "$setOnInsert": {
                "email": "user@andesite.ai",
                "theme_preference": "default",
                "timezone_preference": "UTC",
                "tokens": {},
                "_id": ANY,
            }
        },
        upsert=True,
        return_document=True,
    )
    assert user_id == "foo"


@pytest.mark.parametrize(
    "user_payload,expected",
    [
        (
            {
                "_id": "user_id",
                "email": "user@andesite.ai",
                "theme_preference": "light",
                "timezone_preference": "EST",
                "tokens": {"test": "foo"},
            },
            User(
                id="user_id",
                email="user@andesite.ai",
                theme_preference="light",
                timezone_preference="EST",
                tokens=Tokens(test="foo"),  # type: ignore
            ),
        ),
        (None, None),
    ],
)
async def test_update_user(mongo_client, user_payload, expected):
    user_mock = AsyncMock(return_value=user_payload)
    mongo_client.return_value.find_one_and_update = user_mock
    user = await UsersManager.update_user("user_id", {"a": "b"})
    user_mock.assert_awaited_once_with(
        {"_id": "user_id"},
        {"$set": {"a": "b"}},
        return_document=True,
    )
    assert user == expected
