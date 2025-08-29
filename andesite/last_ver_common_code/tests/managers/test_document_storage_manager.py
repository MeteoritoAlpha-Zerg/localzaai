import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.document_storage.document_storage_manager import (
    DocumentStorageManager,
)

from common.models.document import DocumentStorageModel


@pytest.fixture(autouse=True)
async def doc_storage_manager():
    manager = DocumentStorageManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["documents"]
    # Uncomment for testing against local MongoDB
    # from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
    # await MongoDbClient.initialize(MongoDbConfig())
    # collection = MongoDbClient.get_collection("metamorph_test", "documents")
    await manager.initialize(collection)
    return manager


@pytest.mark.asyncio
async def test_get_all_docs_none(
    doc_storage_manager: DocumentStorageManager,
) -> None:
    all_docs = await doc_storage_manager.get_all_documents_async()
    assert len(all_docs) == 0


@pytest.mark.asyncio
async def test_get_all_docs(
    doc_storage_manager: DocumentStorageManager,
) -> None:
    doc = DocumentStorageModel(
        name="tester",
        file_name="tester.pdf",
        mime_type="1234",
        s3_bucket="1234",
        s3_key="1234",
    )
    await doc_storage_manager.upsert_document_async(doc)

    m = await doc_storage_manager.get_all_documents_async()
    assert len(m) == 1


@pytest.mark.asyncio
async def test_update_doc(doc_storage_manager) -> None:
    doc = DocumentStorageModel(
        name="tester",
        file_name="tester.pdf",
        mime_type="1234",
        s3_bucket="1234",
        s3_key="1234",
    )
    await doc_storage_manager.upsert_document_async(doc)
    retrieved_doc = await doc_storage_manager.get_document_async(doc.id)

    assert retrieved_doc.id == doc.id

    retrieved_doc.processing_progress_percent = 20
    saved_doc = await doc_storage_manager.upsert_document_async(retrieved_doc)
    assert saved_doc.processing_progress_percent == 20


@pytest.mark.asyncio
async def test_archive_doc(doc_storage_manager) -> None:
    doc = DocumentStorageModel(
        name="tester",
        file_name="tester.pdf",
        mime_type="1234",
        s3_bucket="1234",
        s3_key="1234",
    )
    doc = await doc_storage_manager.upsert_document_async(doc)

    await doc_storage_manager.archive_document_async(doc.id)

    all_docs = await doc_storage_manager.get_all_documents_async()
    assert len(all_docs) == 0


@pytest.mark.asyncio
async def test_archive_all_docs(doc_storage_manager) -> None:
    doc = DocumentStorageModel(
        name="tester",
        file_name="tester.pdf",
        mime_type="1234",
        s3_bucket="1234",
        s3_key="1234",
    )
    await doc_storage_manager.upsert_document_async(doc)

    await doc_storage_manager.archive_all_documents_async()

    all_docs = await doc_storage_manager.get_all_documents_async()
    assert len(all_docs) == 0
