import datetime
from functools import lru_cache
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING

from common.jsonlogging.jsonlogger import Logging
from common.models.connectors import ConnectorScope
from common.models.document import DocumentStorageModel, ProcessingStatusEnum, RiskScoreEnum

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class DocumentStorageException(Exception):
    """Base class for exceptions in this module."""

    pass


class DocumentStorageManager:
    def __init__(
        self,
    ):
        """
        Initializes the DocumentStorageManager.

        :return: None
        """
        self._storage_collection: AgnosticCollection | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "DocumentStorageManager":
        """
        Get a global singleton of the DocumentStorageManager in a threadsafe manner.
        :return: The app-wide DocumentStorageManager singleton.
        """
        return DocumentStorageManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_document_async")
    async def get_document_async(
        self,
        doc_id: str,
    ) -> DocumentStorageModel | None:
        """
        Asynchronously retrieves document from the database or cache.

        :param doc_id: the id of the document.
        :return: The retrieved document or None if not found
        """
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to get document because no storage collection was initialized.")

        document = await self._storage_collection.find_one(
            {
                "_id": ObjectId(doc_id),
                "archived_at": None,
            }
        )  # type: ignore[func-returns-value]

        if document is None:
            return None

        logger().info(
            "Retrieved document with doc_id '%s'",
            doc_id,
        )

        return DocumentStorageModel.from_mongo(document)

    @tracer.start_as_current_span("get_document_checksum_async")
    async def get_document_by_checksum_async(self, checksum: str) -> DocumentStorageModel | None:
        if self._storage_collection is None:
            raise DocumentStorageException(
                "Unable to get document by checksum because no storage collection was initialized."
            )
        document = await self._storage_collection.find_one({"checksum": checksum, "archived_at": None})  # type: ignore[func-returns-value]

        if document is None:
            return None

        return DocumentStorageModel.from_mongo(document)

    @tracer.start_as_current_span("get_all_documents_async")
    async def get_all_documents_async(
        self, skip: int | None = None, limit: int | None = None
    ) -> list[DocumentStorageModel]:
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to get documents because no storage collection was initialized.")
        pipeline: list[dict[str, Any]] = [
            {"$match": {"archived_at": None}},
        ]
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})

        # to_list with length of None means it will return ALL results
        documents_in_mongo = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None
        )
        logger().debug("Retrieved %s documents", len(documents_in_mongo))

        documents: list[DocumentStorageModel] = []
        for d in documents_in_mongo:
            document_response = DocumentStorageModel.from_mongo(d)
            if document_response:
                documents.append(document_response)
        return documents

    @tracer.start_as_current_span("archive_document_async")
    async def archive_all_documents_async(self) -> bool:
        """
        Asynchronously archives all documents.

        :raises DocumentStorageException: If there is an error deleting the document.
        :return: True if the documents were archived, False otherwise.
        """
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to archive documents because no storage collection was initialized.")

        try:
            result = await self._storage_collection.update_many(
                {"archived_at": None},
                {"$set": {"archived_at": datetime.datetime.now(datetime.UTC)}},
            )
        except Exception as err:
            raise DocumentStorageException("Unable to archive documents") from err

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already archived
            logger().info("No documents are available to archive")
            return False

        logger().info("Archived all documents")

        return True

    @tracer.start_as_current_span("archive_document_async")
    async def archive_document_async(self, doc_id: str) -> bool:
        """
        Asynchronously archives the content of a document.

        :param doc_id: the id of the document to archive.
        :raises DocumentStorageException: If there is an error deleting the document.
        :return: True if the document was archived, False otherwise.
        """
        if self._storage_collection is None:
            raise DocumentStorageException(
                f"Unable to archive document with doc_id '{doc_id}' because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.update_one(
                {"_id": ObjectId(doc_id), "archived_at": None},
                {"$set": {"archived_at": datetime.datetime.now(datetime.UTC)}},
            )
        except Exception as err:
            raise DocumentStorageException(f"Unable to archive document with doc_id '{doc_id}'") from err

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already archived
            logger().info(
                "Document with doc_id '%s' was already archived or never existed",
                doc_id,
            )
            return False

        logger().info("Archived document with doc_id '%s'", doc_id)

        return True

    async def reset_document_async(self, doc_id: str, scopes: list[ConnectorScope]) -> bool:
        """
        Asynchronously resets the content of a document in the database.

        :param doc_id: the id of the document to reset.
        :raises DocumentStorageException: If there is an error resetting the document.
        :return: True if the document was found and reset, False otherwise.
        """
        if self._storage_collection is None:
            raise DocumentStorageException(
                f"Unable to reset document with doc_id '{doc_id}' because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.update_one(
                {"_id": ObjectId(doc_id), "archived_at": None},
                {
                    "$set": {
                        "single_sentence_summary": None,
                        "comprehensive_summary": None,
                        "scopes": [scope.model_dump() for scope in scopes],
                        "generated_prompts": None,
                        "exploratory_searches": [],
                        "risk_score": RiskScoreEnum.UNKNOWN,
                        "risk_assessment": None,
                        "recommendations": None,
                        "processing_ended_at": None,
                        "processing_error": None,
                        "processing_status": ProcessingStatusEnum.PENDING,
                        "processing_progress_percent": 0,
                        "llm_config": None,
                        "archived_at": None,
                        "iocs": None,
                        "full_text": None,
                        "uploaded_at": datetime.datetime.now(datetime.UTC),
                    }
                },
            )
        except Exception as e:
            raise DocumentStorageException(f"Unable to reset document with doc_id '{doc_id}'") from e

        if result.matched_count == 0:
            logger().info("Document with doc_id '%s' never existed", doc_id)
            return False

        if result.modified_count == 0:
            logger().info(
                "Document with doc_id '%s' is already reset",
                doc_id,
            )
            return True

        return True

    @tracer.start_as_current_span("upsert_document_async")
    async def upsert_document_async(self, document_storage_model: DocumentStorageModel) -> DocumentStorageModel:
        """
        Asynchronously sets the content of a document in the database. You can
        update documents and introduce new documents using this method.
        This method will raise an Exception if trying to update an archived document.

        :param document_storage_model: The document storage model.
        :return: The updated document storage model.
        :raises DocumentStorageException: If there is an error setting the document.
        """
        if self._storage_collection is None:
            raise DocumentStorageException(
                f"Unable to set document with id '{document_storage_model.id}' because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {"_id": ObjectId(document_storage_model.id), "archived_at": None},
                {"$set": document_storage_model.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            if updated_mongo_document is None:
                raise DocumentStorageException(f"Unable to update document with id '{document_storage_model.id}'")
            updated_doc = DocumentStorageModel.from_mongo(updated_mongo_document)

            logger().info(
                "Document with id '%s' was updated",
                updated_doc.id,
            )
            return updated_doc
        except Exception as e:
            logger().error(f"An error occurred while setting document with id '{document_storage_model.id}': {e}")
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection | None = None):
        """
        Initializes the DocumentStorageManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "DocumentStorageManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "DocumentStorageManager initialized without a storage collection - documents will not be persisted"
            )
            return
        await self._storage_collection.create_index([("uploaded_at", ASCENDING)])

        await self._migrate_june_2_2025()
        await self._migrate_june_7_2025()
        await self._migrate_june_12_2025()

    async def _migrate_june_12_2025(self):
        """
        Adds lookback_days to exploratory searches model.
        """
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to get documents because no storage collection was initialized.")

        current_docs = self._storage_collection.find(
            {
                "$and": [
                    {"exploratory_searches": {"$exists": True}},
                    {"exploratory_searches": {"$ne": None}},
                    {"exploratory_searches": {"$type": "array"}},
                    {"archived_at": None},
                    {
                        "exploratory_searches": {
                            "$elemMatch": {
                                "$or": [
                                    {"lookback_days": {"$exists": False}},
                                    {"lookback_days": None},
                                ]
                            }
                        }
                    },
                ]
            }
        )
        async for d in current_docs:
            exploratory_searches = d.get("exploratory_searches", [])
            updated_searches = []
            for search in exploratory_searches:
                if not isinstance(search, dict):
                    updated_searches.append(search)
                    continue

                if search.get("lookback_days") is None:
                    search["lookback_days"] = 2

                updated_searches.append(search)

            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {"exploratory_searches": updated_searches},
                },
            )

    async def _migrate_june_7_2025(self):
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to get documents because no storage collection was initialized.")

        current_docs = self._storage_collection.find(
            {
                "archived_at": None,
                "recommended_actions": {"$exists": True},
            }
        )
        async for d in current_docs:
            recommended_actions = d.get("recommended_actions", [])
            if recommended_actions is None or not isinstance(recommended_actions, list):
                recommended_actions = []
            recommendations = [{"source": "exploratory_search", "content": action} for action in recommended_actions]
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {"recommendations": recommendations},
                    "$unset": {
                        "recommended_actions": None,
                    },
                },
            )

    async def _migrate_june_2_2025(self):
        if self._storage_collection is None:
            raise DocumentStorageException("Unable to get documents because no storage collection was initialized.")

        current_docs = self._storage_collection.find(
            {
                "archived_at": None,
                "comprehensive_summary": {"$exists": False},
            }
        )
        async for d in current_docs:
            summary = d.get("summary", None)
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {
                        "comprehensive_summary": summary,
                        "single_sentence_summary": "",
                    },
                    "$unset": {
                        "summary": None,
                    },
                },
            )
