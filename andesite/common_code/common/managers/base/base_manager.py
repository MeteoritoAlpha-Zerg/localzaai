from typing import Annotated, Any, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError, PyMongoError
from pymongo.results import (
    DeleteResult,
    InsertOneResult,
    UpdateResult,
)

from common.jsonlogging.jsonlogger import Logging
from common.models.mongo import DbDocument, DbError, DbException

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

T = TypeVar("T", bound=DbDocument)
U = TypeVar("U", bound=BaseModel)

type FilterQuery = dict[str, Any]  # Filter query for DB queries
type Projection = dict[str, bool] | None  # Projection for DB queries

IdList = Annotated[
    list[str],
    Field(description="List of IDs relevant to batch operations", default_factory=list),
]


class BatchUpdateResult(BaseModel):
    requested_ids: IdList
    inserted_ids: IdList
    updated_ids: IdList
    deleted_ids: IdList
    failed_ids: IdList
    errors: str | None = Field(
        description="Optional error message to include for failed operations",
        default=None,
    )


def id_filter(document: DbDocument) -> dict[str, ObjectId]:
    return {"_id": document.id}


def id_filter_str(id: str) -> dict[str, ObjectId]:
    return {"_id": ObjectId(id)}


class Manager[T: DbDocument]:
    def __init__(self, collection: AgnosticCollection, cls: type[T]) -> None:
        """
        Initializes the Manager with a collection and document class.
        :param collection: The AgnosticCollection to interact with the database.
        :param cls: The class of the DBDocument type to deserialize documents to.
        """
        self.collection = collection
        self.db_document_cls = cls

    def catch_pymongo_error(function: Any):
        """
        Decorator to handle unexpected PyMongo errors and raise a DbException instead.
        """

        async def execute_db_task(self, *args, **kwargs):
            collection_name = self.collection.name
            try:
                return await function(self, *args, **kwargs)
            except PyMongoError as e:
                logger().error(
                    "Unexpected DB error running Operation=%s, Args=%s, Kwargs=%s, Error=%s",
                    function.__name__,
                    args,
                    kwargs,
                    e,
                )
                raise DbException("Unexpected DB error", collection_name) from e

        return execute_db_task

    @catch_pymongo_error
    async def find_one_projection(self, object_id: str, projection: Projection, document_cls: type[U]) -> U | None:
        # https://mypy.readthedocs.io/en/latest/error_code_list.html#code-func-returns-value
        # find_one returns the document or None if it's not found, but mypy cannot infer this type
        # It errors that we are not ignoring the None return value
        document = await self.collection.find_one(filter=id_filter_str(object_id), projection=projection)  # type: ignore[func-returns-value]
        if document is None:
            return None
        return document_cls(**document)

    async def find_one(self, object_id: str) -> T | None:
        return await self.find_one_projection(object_id=object_id, projection=None, document_cls=self.db_document_cls)

    @catch_pymongo_error
    async def find_many_projection(self, query: FilterQuery, projection: Projection, document_cls: type[U]) -> list[U]:
        result = []
        cursor = self.collection.find(query, projection)
        async for document in cursor:  # type: ignore[var-annotated]
            result.append(document_cls(**document))
        return result

    async def find_many(self, query: FilterQuery) -> list[T]:
        return await self.find_many_projection(query, None, self.db_document_cls)

    @catch_pymongo_error
    async def insert_one(self, document: T) -> str:
        try:
            result: InsertOneResult = await self.collection.insert_one(document.to_mongo())
            return str(result.inserted_id)
        except DuplicateKeyError as err:
            raise DbException(
                "Document already exists",
                self.collection.name,
                error_type=DbError.resource_found,
            ) from err

    @catch_pymongo_error
    async def delete_one(self, object_id: str) -> str:
        result: DeleteResult = await self.collection.delete_one({"_id": ObjectId(object_id)})
        if result.deleted_count == 0:
            raise DbException(
                f"Failed to delete document Id={object_id}",
                self.collection.name,
                DbError.resource_not_found,
            )
        return object_id

    @catch_pymongo_error
    async def update_one(self, document: T, upsert: bool = False) -> str:
        try:
            result: UpdateResult = await self.collection.update_one(
                {"_id": document.id}, {"$set": document.to_mongo()}, upsert=upsert
            )
        except DuplicateKeyError as err:
            raise DbException(
                "Document already exists",
                self.collection.name,
                error_type=DbError.resource_found,
            ) from err
        if result.matched_count == 0:
            raise DbException(
                f"Failed to update document Id={document.id}. Document not found.",
                self.collection.name,
                DbError.resource_not_found,
            )
        return str(document.id)
