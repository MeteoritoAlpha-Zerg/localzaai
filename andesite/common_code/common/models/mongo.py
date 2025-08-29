from enum import StrEnum, auto

from bson import ObjectId
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DbDocument(BaseModel):
    """
    DbDocument is a base model for MongoDB documents.
    It includes an ObjectId and provides a method to serialize the document for MongoDB storage.
    """

    id: ObjectId = Field(
        serialization_alias="_id",
        validation_alias=AliasChoices("id", "_id"),
        default_factory=ObjectId,
    )

    model_config = ConfigDict(
        # Serializes enums as their values
        use_enum_values=True,
        # Pydantic does not support bson.ObjectId, setting this to allow it
        arbitrary_types_allowed=True,
    )

    def to_mongo(self):
        return self.model_dump(by_alias=True)


class DbError(StrEnum):
    unknown = auto()
    resource_found = auto()
    resource_not_found = auto()
    partial_update_failure = auto()


class DbException(Exception):
    """
    DbException is a custom exception class for MongoDB-related errors.
    """

    def __init__(
        self,
        message: str,
        collection_name: str,
        error_type: DbError = DbError.unknown,
    ) -> None:
        super().__init__(message)
        self.collection_name = collection_name
        self.message = message
        self.error_type = error_type

    def __str__(self):
        return f"{self.collection_name} Code={self.error_type} Msg={self.message}"
