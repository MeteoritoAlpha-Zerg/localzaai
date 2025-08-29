from bson import ObjectId
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DbDocument(BaseModel):
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
