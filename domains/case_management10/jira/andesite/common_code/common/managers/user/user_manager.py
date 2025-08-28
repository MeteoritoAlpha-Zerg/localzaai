import uuid
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_settings import BaseSettings

from common.clients.mongodb_client import MongoDbClient
from common.jsonlogging.jsonlogger import Logging
from common.managers.user.user_model import User

logger = Logging.get_logger(__name__)


class MissingUserEmailError(Exception):
    pass


class UsersManagerConfig(BaseSettings):
    mongodb_database: str = "metamorph"


def check_client_initialization(cls_method):
    def check_client(*args, **kwargs):
        if not hasattr(args[0], "_col"):
            raise ValueError("MongoDb client is not initialized.")
        return cls_method(*args, **kwargs)

    return check_client


class UsersManager:
    _col: AsyncIOMotorCollection | None

    @classmethod
    def initialize(cls, cfg: UsersManagerConfig):
        cls._col = MongoDbClient.get_collection(cfg.mongodb_database, "users")

    @classmethod
    @check_client_initialization
    async def get_user(cls, id: str) -> User | None:
        return User.from_mongo(await cls._col.find_one({"_id": id}))  # type: ignore

    @classmethod
    @check_client_initialization
    async def get_or_create_user_from_email(cls, user_email: str | None) -> str:
        """
        Find or insert a user for a given email. Emails are assumed to be unique and
        required to map an external user's information to our internal data

        Raises MissingUserEmailError is no email is provided
        """
        if user_email is None:
            raise MissingUserEmailError()

        user = await cls._col.find_one_and_update(  # type: ignore
            {"email": user_email},
            {
                "$setOnInsert": User(
                    id=str(uuid.uuid4()),
                    email=user_email,
                ).to_mongo(),
            },
            upsert=True,
            return_document=True,
        )
        return user["_id"]

    @classmethod
    @check_client_initialization
    async def update_user(cls, user_id: str, values: dict[str, Any]) -> User | None:
        """
        Updates a user's settings
        """
        user = User.from_mongo(
            await cls._col.find_one_and_update(  # type: ignore
                {"_id": user_id},
                {"$set": values},
                return_document=True,
            )
        )

        return user
