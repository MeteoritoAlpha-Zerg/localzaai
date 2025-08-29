import datetime
from functools import lru_cache
import uuid
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from typing import Any, Optional

from pymongo import ASCENDING
from opentelemetry import trace

from common.models.connectors import ConnectorScope
from common.jsonlogging.jsonlogger import Logging
from common.models.document import (
    DocumentStorageModel,
    RiskScoreEnum,
    ProcessingStatusEnum,
)

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
        self._storage_collection: Optional[AgnosticCollection] = None

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
    ) -> Optional[DocumentStorageModel]:
        """
        Asynchronously retrieves document from the database or cache.

        :param doc_id: the id of the document.
        :return: The retrieved document or None if not found
        """
        if self._storage_collection is None:
            raise DocumentStorageException(
                "Unable to get document because no storage collection was initialized."
            )

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
    async def get_document_by_checksum_async(
        self, checksum: str
    ) -> Optional[DocumentStorageModel]:
        if self._storage_collection is None:
            raise DocumentStorageException(
                "Unable to get document by checksum because no storage collection was initialized."
            )
        document = await self._storage_collection.find_one(
            {"checksum": checksum, "archived_at": None}
        )  # type: ignore[func-returns-value]

        if document is None:
            return None

        return DocumentStorageModel.from_mongo(document)

    @tracer.start_as_current_span("get_all_documents_async")
    async def get_all_documents_async(
        self, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> list[DocumentStorageModel]:
        if self._storage_collection is None:
            raise DocumentStorageException(
                "Unable to get documents because no storage collection was initialized."
            )
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
            raise DocumentStorageException(
                "Unable to archive documents because no storage collection was initialized."
            )

        try:
            result = await self._storage_collection.update_many(
                {"archived_at": None},
                {"$set": {"archived_at": datetime.datetime.now(datetime.timezone.utc)}},
            )
        except Exception:
            raise DocumentStorageException("Unable to archive documents")

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
                {"$set": {"archived_at": datetime.datetime.now(datetime.timezone.utc)}},
            )
        except Exception:
            raise DocumentStorageException(
                f"Unable to archive document with doc_id '{doc_id}'"
            )

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already archived
            logger().info(
                "Document with doc_id '%s' was already archived or never existed",
                doc_id,
            )
            return False

        logger().info("Archived document with doc_id '%s'", doc_id)

        return True

    async def reset_document_async(
        self, doc_id: str, scopes: list[ConnectorScope]
    ) -> bool:
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
                        "summary": None,
                        "scopes": [scope.model_dump() for scope in scopes],
                        "generated_prompts": None,
                        "exploratory_searches": [],
                        "risk_score": RiskScoreEnum.UNKNOWN,
                        "risk_assessment": None,
                        "recommended_actions": None,
                        "processing_ended_at": None,
                        "processing_errors": None,
                        "processing_status": ProcessingStatusEnum.PENDING,
                        "processing_progress_percent": 0,
                        "llm_config": None,
                        "archived_at": None,
                        "processing_conversation": None,
                    }
                },
            )
        except Exception:
            raise DocumentStorageException(
                f"Unable to reset document with doc_id '{doc_id}'"
            )

        if result.matched_count == 0 or result.modified_count == 0:
            # occurs when the document doesn't exist or is already reset
            logger().info(
                "Document with doc_id '%s' was already reset or never existed", doc_id
            )
            return False

        return True

    @tracer.start_as_current_span("upsert_document_async")
    async def upsert_document_async(
        self, document_storage_model: DocumentStorageModel
    ) -> DocumentStorageModel:
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
                raise DocumentStorageException(
                    f"Unable to update document with id '{document_storage_model.id}'"
                )
            updated_doc = DocumentStorageModel.from_mongo(updated_mongo_document)

            logger().info(
                "Document with id '%s' was updated",
                updated_doc.id,
            )
            return updated_doc
        except Exception as e:
            logger().error(
                f"An error occurred while setting document with id '{document_storage_model.id}': {e}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
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

    # Supports document schema of Feb 2025
    async def migrate_exploratory_searches(self):
        """
        Migrates exploratory searches from the old structure to the new structure:

        Old structure example:
        {
            "response": "...",
            "metadata": { ... },
            "raises_concern": false
        }

        New structure example:
        {
            "conversation": {
                "user_id": "...",
                "conversation_id": "<uuid>",
                "messages": [
                    {
                    "id": "<uuid>",
                    "role": "user",
                    "content": "...",
                    "type": "answer",
                    "timestamp": "<timestamp>",
                    "metadata": { ... },
                    "resources": [],
                    "scopes": [],
                    "proposed_followups": None
                    }
                ]
            },
            "raises_concern": false,
            "raised_exception": false
        }
        """
        if self._storage_collection is None:
            raise DocumentStorageException(
                "Unable to get documents because no storage collection was initialized."
            )

        unarchived_docs_without_exploratory_searches = self._storage_collection.find(
            {
                "exploratory_searches": None,
                "archived_at": None,
            }
        )
        async for d in unarchived_docs_without_exploratory_searches:
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {"exploratory_searches": []},
                },
            )

        docs_from_storage = self._storage_collection.find(
            {
                "exploratory_searches": {"$exists": True, "$ne": None},
                "archived_at": None,
            }
        )

        async for d in docs_from_storage:
            new_exploratory_searches = []

            for search in d.get("exploratory_searches", []):
                if "conversation" in search:
                    new_exploratory_searches.append(search)
                else:
                    conversation = {
                        "user_id": str(d.get("_id", "unknown")),
                        "conversation_id": str(uuid.uuid4()),
                        "messages": [
                            {
                                "id": str(uuid.uuid4()),
                                "role": "user",
                                "content": search.get("response", ""),
                                "type": "answer",
                                "timestamp": datetime.datetime.now(
                                    datetime.timezone.utc
                                ).isoformat(),
                                "metadata": search.get("metadata", None),
                                "resources": [],
                                "scopes": [],
                                "proposed_followups": None,
                            }
                        ],
                    }

                    new_entry = {
                        "conversation": conversation,
                        "raises_concern": search.get("raises_concern", False),
                        "raised_exception": False,
                    }

                    new_exploratory_searches.append(new_entry)
            # update generated prompts
            if d.get("generated_prompts") is None:
                new_generated_prompts = None
            elif isinstance(d.get("generated_prompts"), list) and all(
                isinstance(prompt, str) for prompt in d.get("generated_prompts")
            ):
                new_generated_prompts = [
                    {"id": str(uuid.uuid4()), "question": prompt}
                    for prompt in d.get("generated_prompts")
                ]
            else:
                new_generated_prompts = d.get("generated_prompts")
            await self._storage_collection.update_one(
                {"_id": d["_id"]},
                {
                    "$set": {
                        "exploratory_searches": new_exploratory_searches,
                        "summary": d.get("description", d.get("summary", None)),
                        "iocs": d.get("extracted_iocs", d.get("iocs", None)),
                        "generated_prompts": new_generated_prompts,
                    },
                    "$unset": {
                        "extracted_iocs": "",
                        "description": "",
                    },
                },
            )
        logger().info("Documents Migration Complete")
