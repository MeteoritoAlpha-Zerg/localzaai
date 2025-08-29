from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
import pytest_asyncio

from common.clients.milvus_vdb_client import MilvusConfig, MilvusVecDBClient
from common.clients.vdb_client import Distance, EmbedDict, VecDBClientError


@pytest_asyncio.fixture
async def milvus_client():
    config = MilvusConfig(
        vecdb_milvus_url="https://mock-url",
        vecdb_milvus_token="mock-token",
    )

    with (
        patch("common.clients.milvus_vdb_client.AsyncMilvusClient", return_value=AsyncMock()) as async_mock,
        patch("common.clients.milvus_vdb_client.MilvusClient", return_value=MagicMock()) as sync_mock,
        patch("common.clients.milvus_vdb_client.logger", return_value=MagicMock()) as mock_logger,
    ):
        client: MilvusVecDBClient = MilvusVecDBClient()
        await client.initialize(config)
        client.async_client = async_mock.return_value
        client.sync_client = sync_mock.return_value

        yield client, mock_logger


@pytest.mark.asyncio
class TestMilvusVecDBClient:
    async def test_create_collection_successful(self, milvus_client) -> None:
        """Test successful collection creation."""
        # Setup
        client, mock_logger = milvus_client
        col_name = "test_collection"
        vec_size = 512

        # Col doesn't exist
        client.sync_client.has_collection.return_value = False

        # Index Params
        mock_index_params = MagicMock()
        client.sync_client.prepare_index_params.return_value = mock_index_params

        # Execute
        result = await client.create_collection(
            collection_name=col_name,
            vec_size=vec_size,
        )

        assert result is True
        client.sync_client.has_collection.assert_called_once_with(collection_name=col_name)
        mock_index_params.add_index.assert_called_once_with(
            field_name="vector",
            metric_type="COSINE",
            index_type="HNSW",
        )
        client.async_client.create_collection.assert_called_once_with(
            collection_name=col_name,
            dimension=vec_size,
            metric_type="COSINE",
            index_params=mock_index_params,
        )
        mock_logger.info.assert_called_once()

    async def test_create_collection_with_different_distance(self, milvus_client) -> None:
        """Test collection creation with different distance settings."""
        client, mock_logger = milvus_client
        col_name = "test_collection"
        vec_size = 512

        # Collection doesn't exist
        client.sync_client.has_collection.return_value = False

        # Index params
        mock_index_params = MagicMock()
        client.sync_client.prepare_index_params.return_value = mock_index_params

        # Test different distance metrics
        test_cases = [
            (Distance.DOT, "IP"),
            (Distance.EUCLID, "L2"),
            (Distance.MANHATTAN, "JACCARD"),
        ]

        for distance_enum, expected_metric in test_cases:
            # Reset mocks
            mock_index_params.reset_mock()
            client.async_client.create_collection.reset_mock()

            # Execute
            result = await client.create_collection(
                collection_name=col_name,
                vec_size=vec_size,
                distance_method=distance_enum,
            )

            # Assert
            assert result is True
            mock_index_params.add_index.assert_called_once_with(
                field_name="vector",
                metric_type=expected_metric,
                index_type="HNSW",
            )
            client.async_client.create_collection.assert_called_once_with(
                collection_name=col_name,
                dimension=vec_size,
                metric_type=expected_metric,
                index_params=mock_index_params,
            )

    async def test_create_collection_already_exists(self, milvus_client):
        """Test when collection already exists."""
        # Setup
        client, mock_logger = milvus_client
        col_name = "existing_collection"
        vec_size = 128

        # Mock has_collection to return True (collection exists)
        client.sync_client.has_collection.return_value = True

        # Execute
        result = await client.create_collection(
            collection_name=col_name,
            vec_size=vec_size,
        )

        assert result is False
        client.sync_client.has_collection.assert_called_once_with(collection_name=col_name)
        client.async_client.create_collection.assert_not_called()
        # Verify error logged
        mock_logger.error.assert_called_once()

    async def test_create_collection_exception(self, milvus_client):
        """Test exception handling during collection creation."""

        client, mock_logger = milvus_client
        col_name = "test_col"
        vec_size = 512

        # Col doesn't exist
        client.sync_client.has_collection.return_value = False

        # Index Params
        mock_index_params = MagicMock()
        client.sync_client.prepare_index_params.return_value = mock_index_params

        # Force exception
        client.async_client.create_collection.side_effect = Exception("Test Exception")

        with pytest.raises(Exception, match="Test Exception"):
            await client.create_collection(
                collection_name=col_name,
                vec_size=vec_size,
            )

        client.sync_client.has_collection.assert_called_once_with(collection_name=col_name)
        client.async_client.create_collection.assert_called_once()
        mock_logger.exception.assert_called_once()

    async def test_add_vectors_success(self, milvus_client):
        """Test successful vector addition."""

        client, mock_logger = milvus_client
        col_name = "test_col"

        test_embeddings = [
            EmbedDict(embedding=[0.1, 0.2, 0.3], payload={"text": "test 1"}),
            EmbedDict(embedding=[0.4, 0.5, 0.6], payload={"text": "test 2"}),
            EmbedDict(embedding=[0.7, 0.8, 0.9], payload={"text": "test 3"}),
        ]

        expected_points = [
            {"id": 0, "vector": [0.1, 0.2, 0.3], "text": "test 1"},
            {"id": 1, "vector": [0.4, 0.5, 0.6], "text": "test 2"},
            {"id": 2, "vector": [0.7, 0.8, 0.9], "text": "test 3"},
        ]

        client.async_client.upsert.return_value = {"upsert_count": 3}

        result = await client.add_vectors(collection_name=col_name, embeddings=test_embeddings)

        assert result is True
        client.async_client.upsert.assert_called_once_with(collection_name=col_name, data=expected_points)
        mock_logger.info.assert_called_once()

    async def test_add_vectors_with_np_arrays(self, milvus_client):
        """Numpy arrays."""
        client, mock_logger = milvus_client
        col_name = "test_col"

        vectors = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])

        test_embeddings = [
            EmbedDict(embedding=vectors[0], payload={"text": "test 1"}),
            EmbedDict(embedding=vectors[1], payload={"text": "test 2"}),
            EmbedDict(embedding=vectors[2], payload={"text": "test 3"}),
        ]

        client.async_client.upsert.return_value = {"upsert_count": 3}

        result = await client.add_vectors(collection_name=col_name, embeddings=test_embeddings)

        assert result is True
        client.async_client.upsert.assert_called_once()
        mock_logger.info.assert_called_once()

    async def test_add_vectors_with_multi_payload(self, milvus_client):
        """Test payload with multiple k, v."""
        client, mock_logger = milvus_client
        col_name = "test_col"

        vectors = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])

        test_embeddings = [
            EmbedDict(embedding=vectors[0], payload={"text": "test 1", "category": "cat", "score": 0.85}),
            EmbedDict(embedding=vectors[1], payload={"text": "test 2", "category": "dog", "score": 0.90}),
            EmbedDict(embedding=vectors[2], payload={"text": "test 3", "category": "bear", "score": 0.88}),
        ]

        client.async_client.upsert.return_value = {"upsert_count": 3}

        result = await client.add_vectors(collection_name=col_name, embeddings=test_embeddings)

        assert result is True
        client.async_client.upsert.assert_called_once()
        mock_logger.info.assert_called_once()

    async def test_add_vectors_upsert_count_mismatch(self, milvus_client):
        """Test when upsert_count doesn't match expected count."""
        client, mock_logger = milvus_client
        collection_name = "test_collection"

        embeddings = [
            EmbedDict(embedding=[0.1, 0.2, 0.3], payload={"text": "test 1"}),
            EmbedDict(embedding=[0.4, 0.5, 0.6], payload={"text": "test 2"}),
            EmbedDict(embedding=[0.7, 0.8, 0.9], payload={"text": "test 3"}),
        ]

        # Mock upsert response with count mismatch
        client.async_client.upsert.return_value = {"upsert_count": 2}  # Only 2 of 3 inserted

        # Execute
        result = await client.add_vectors(collection_name=collection_name, embeddings=embeddings)

        # Assert
        assert result is False
        client.async_client.upsert.assert_called_once()
        # Should not log success message on count mismatch
        mock_logger.info.assert_not_called()

    async def test_add_vectors_upsert_exception(self, milvus_client):
        """Test exception during upsert operation."""
        # Setup
        client, mock_logger = milvus_client
        collection_name = "test_collection"

        # Create test embeddings
        embeddings = [
            EmbedDict(embedding=[0.1, 0.2, 0.3], payload={"text": "test 1"}),
            EmbedDict(embedding=[0.4, 0.5, 0.6], payload={"text": "test 2"}),
        ]

        # Mock exception during upsert
        client.async_client.upsert.side_effect = Exception("Upsert failed")

        # Execute
        with pytest.raises(VecDBClientError, match="Unable to upsert vectors: Upsert failed"):
            await client.add_vectors(collection_name=collection_name, embeddings=embeddings)

        # Assert
        client.async_client.upsert.assert_called_once()
        mock_logger.exception.assert_called_once_with("Error in adding vectors to %s collection", collection_name)

    async def test_query_vectors_basic(self, milvus_client):
        """Test basic successful vector query."""
        client, mock_logger = milvus_client
        col_name = "test_collection"
        embedding = [[0.1, 0.2, 0.3]]
        limit = 3

        # Mock list_indexes
        index_name = "test_index"
        client.sync_client.list_indexes.return_value = [index_name]

        # Mock describe_index
        index_details = {"metric_type": "COSINE"}
        client.sync_client.describe_index.return_value = index_details

        # Mock search results
        mock_result = [
            [
                {
                    "distance": 0.1,
                    "entity": {
                        "id": 1,
                        "text": "sample text 1",
                        "vector": [0.1, 0.2, 0.3],  # This should be excluded from final result
                    },
                },
                {
                    "distance": 0.2,
                    "entity": {
                        "id": 2,
                        "text": "sample text 2",
                        "vector": [0.2, 0.3, 0.4],  # This should be excluded from final result
                    },
                },
            ]
        ]
        client.async_client.search.return_value = mock_result

        result = await client.query_vectors(collection_name=col_name, embedding=embedding, limit=limit)

        # Assert
        client.sync_client.list_indexes.assert_called_once_with(collection_name=col_name)
        client.sync_client.describe_index.assert_called_once_with(collection_name=col_name, index_name=index_name)
        client.async_client.search.assert_called_once_with(
            collection_name=col_name,
            anns_field="vector",
            data=embedding,
            limit=limit,
            search_params={"metric_type": index_details["metric_type"]},
            output_fields=["*"],
            filter="",
        )

        # Check correct data processing
        expected_result = [
            {"distance": 0.1, "id": 1, "text": "sample text 1"},
            {"distance": 0.2, "id": 2, "text": "sample text 2"},
        ]
        assert result == expected_result
        mock_logger.info.assert_called_once_with("Querying collection %s", col_name)

    async def test_query_vectors_custom_limit(self, milvus_client):
        """Test vector query with custom limit."""
        client, mock_logger = milvus_client
        collection_name = "test_collection"
        embedding = [[0.1, 0.2, 0.3]]
        custom_limit = 5

        # Mock list_indexes
        client.sync_client.list_indexes.return_value = ["index1"]
        client.sync_client.describe_index.return_value = {"metric_type": "IP"}

        # Mock search with empty results
        client.async_client.search.return_value = [[]]

        result = await client.query_vectors(collection_name=collection_name, embedding=embedding, limit=custom_limit)

        # Assert
        client.async_client.search.assert_called_once_with(
            collection_name=collection_name,
            anns_field="vector",
            data=embedding,
            limit=custom_limit,
            search_params={"metric_type": "IP"},
            output_fields=["*"],
            filter="",
        )
        assert result == []

    async def test_query_vectors_with_complex_payload(self, milvus_client):
        """Test query with complex nested payload structures."""
        client, mock_logger = milvus_client
        collection_name = "complex_collection"
        embedding = [[0.1, 0.2, 0.3]]

        # Mock index information
        client.sync_client.list_indexes.return_value = ["complex_index"]
        client.sync_client.describe_index.return_value = {"metric_type": "L2"}

        # Mock search with complex results
        complex_result = [
            [
                {
                    "distance": 0.15,
                    "entity": {
                        "id": 1,
                        "metadata": {"source": "file1.pdf", "page": 5},
                        "nested": {"key1": "value1", "key2": [1, 2, 3]},
                        "timestamp": 1623456789,
                        "vector": [0.1, 0.2, 0.3],
                    },
                },
            ],
        ]
        client.async_client.search.return_value = complex_result

        # Execute
        result = await client.query_vectors(collection_name=collection_name, embedding=embedding)

        # Assert
        expected_result = [
            {
                "distance": 0.15,
                "id": 1,
                "metadata": {"source": "file1.pdf", "page": 5},
                "nested": {"key1": "value1", "key2": [1, 2, 3]},
                "timestamp": 1623456789,
            }
        ]
        assert result == expected_result

    async def test_query_vectors_with_np_array(self, milvus_client):
        """Test with numpy array embeddings (realistic scenario)."""
        client, mock_logger = milvus_client
        collection_name = "numpy_collection"

        rng = np.random.default_rng(42)  # Fixed seed for reproducibility
        query_vector = rng.random((1, 3)).tolist()  # 1 vector with 3 dimensions

        # Mock index information
        client.sync_client.list_indexes.return_value = ["numpy_index"]
        client.sync_client.describe_index.return_value = {"metric_type": "COSINE"}

        # Mock search results
        mock_result = [[{"distance": 0.25, "entity": {"id": 42, "text": "numpy text", "vector": [0.1, 0.2, 0.3]}}]]
        client.async_client.search.return_value = mock_result

        # Execute
        result = await client.query_vectors(collection_name=collection_name, embedding=query_vector)

        # Assert
        client.async_client.search.assert_called_once_with(
            collection_name=collection_name,
            anns_field="vector",
            data=query_vector,
            limit=3,  # Default limit
            search_params={"metric_type": "COSINE"},
            output_fields=["*"],
            filter="",
        )

        expected_result = [{"distance": 0.25, "id": 42, "text": "numpy text"}]
        assert result == expected_result

    async def test_query_vectors_empty_results(self, milvus_client):
        """Test behavior with empty search results."""
        client, mock_logger = milvus_client
        collection_name = "empty_collection"
        embedding = [[0.1, 0.2, 0.3]]

        client.sync_client.list_indexes.return_value = ["empty_index"]
        client.sync_client.describe_index.return_value = {"metric_type": "COSINE"}

        # Mock empty search results
        client.async_client.search.return_value = [[]]

        # Execute
        result = await client.query_vectors(collection_name=collection_name, embedding=embedding)

        # Assert
        assert result == []
        mock_logger.info.assert_called_once()
