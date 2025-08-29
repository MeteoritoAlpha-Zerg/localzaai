# ruff: noqa: E402
"""milvus_vdb_client module, contains all functions for interactions with Milvus Vecdb.

This module contains an interface for interacting with Milvus,
a vector database.

Classes:
    MilvusVector:
        Milvus client.

Functions:
    create_collection(collection_name, vec_size, distance_method)
    add_vectors(collection_name, embeddings)
    query_vectors(collection_name, embedding, limit) -> list[ScoredPoint]
    is_collection_new(collection_name) -> bool
    is_collection_empty(collection_name, collection_count) -> bool
    list_collections() -> list[str]
    collection_exists(collection_name) -> bool
    num_entities(collection_name, timeout) -> int

"""

import dotenv
from pydantic import BaseModel, SecretStr


# This is put here bc pymilvus runs load_dotenv at init and breaks processor and backend with Assert Error
# (See: https://github.com/milvus-io/pymilvus/issues/2827)
def noop(*args, **kwargs):
    return False


dotenv.load_dotenv = noop

from typing import TYPE_CHECKING, Any, final

from opentelemetry import trace
from pymilvus import AsyncMilvusClient, MilvusClient  # type: ignore[import-untyped]
from pymilvus.orm.connections import connections  # type: ignore[import-untyped]

from common.jsonlogging.jsonlogger import Logging
from common.utils.async_wrap import async_wrap

if TYPE_CHECKING:
    from pymilvus.milvus_client import IndexParams  # type: ignore[import-untyped]

from common.clients.vdb_client import (
    Distance,
    EmbedDict,
    IndexMethod,
    VecDBClientError,
)

logger = Logging.get_logger(__name__)()
tracer: trace.Tracer = trace.get_tracer(__name__)


class MilvusConfig(BaseModel):
    vecdb_milvus_url: str
    vecdb_milvus_token: SecretStr


@final
class MilvusVecDBClient:
    """Client for interacting with Milvus Vector Database."""

    async_client: AsyncMilvusClient | None = None
    sync_client: MilvusClient | None = None
    _client: "MilvusVecDBClient | None" = None

    @classmethod
    async def initialize(cls, config: MilvusConfig) -> None:
        """Initialize sync and async pymilvus clients.

        Note: Pymilvus doesn't have equal functionality between sync and async
        clients, requiring the use of both. Default and preferrable
        implementation is with AsyncMilvusClient, but some handler functions
        have been implemented with MilvusClient. Please check if functionality
        for an implemented sync function is available in async client when
        updating. For those functions implemented with sync client and have I/O
        or network requests, async_wrapper was used to convert to async.

        Args:
            config (MilvusConfig): specifies vec db name in env var.

        """
        cls.async_client = AsyncMilvusClient(
            uri=config.vecdb_milvus_url,
            token=config.vecdb_milvus_token.get_secret_value(),
        )
        cls.sync_client = MilvusClient(
            uri=config.vecdb_milvus_url,
            token=config.vecdb_milvus_token.get_secret_value(),
        )
        cls._client = cls()

    @classmethod
    async def close(cls) -> None:
        """Close all open connections to milvus db."""
        if cls.async_client:
            await cls.async_client.close()
            cls.async_client = None
        if cls.sync_client:
            async_close = async_wrap(cls.sync_client.close)
            await async_close()
            cls.sync_client = None
        cls._client = None
        logger.info("Verified all milvus connections are closed")

    @classmethod
    def get_client(cls) -> "MilvusVecDBClient":
        """Use as singleton client."""
        if not cls._client:
            raise VecDBClientError("MilvusVecDB Client not initialized")
        return cls._client

    async def create_collection(
        self,
        collection_name: str,
        vec_size: int,
        distance_method: Distance = Distance.COSINE,
        index_method: IndexMethod = IndexMethod.HNSW,
    ) -> bool:
        """Create a Milvus collection, if not existant.

        Args:
            collection_name (str): Name of collection.
            vec_size (int): Dimension of vector; e.g., 1024.
            distance_method (Distance, enum): Method to be used for retrieval.
            index_method: (IndexMethod, enum): Method used for indexing collection.

        Returns:
            bool: True if collection was successfully created, false if collection already exists.

        Raises:
            VecDBClientError: If any error is raised when creating collection.

        """
        if await self.collection_exists(collection_name=collection_name):
            logger.error(
                "Collection %s already exists in database. Delete collection if you would like to recreate.",
                collection_name,
            )
            return False

        match distance_method:
            case Distance.COSINE:
                distance = "COSINE"
            case Distance.DOT:
                distance = "IP"
            case Distance.EUCLID:
                distance = "L2"
            case Distance.MANHATTAN:
                distance = "JACCARD"  # Milvus doesn't support Manhattan

        # Set index method
        if self.sync_client and self.async_client:
            index_params: IndexParams = self.sync_client.prepare_index_params()

            index_params.add_index(field_name="vector", metric_type=distance, index_type=str(index_method))

            try:
                _ = await self.async_client.create_collection(
                    collection_name=collection_name,
                    dimension=vec_size,
                    metric_type=distance,
                    index_params=index_params,
                )

            except Exception as e:
                logger.exception("Error when creating collection %s", collection_name)
                raise VecDBClientError(f"Error encountered when creating new collection: {e!s}") from e

            else:
                logger.info(
                    "Milvus Collection for %s was successfully created.",
                    collection_name,
                )
                return True
        else:
            logger.error("Milvus client is not initialized.")
            raise VecDBClientError("Milvus client is not initialized")

    async def add_vectors(self, collection_name: str, embeddings: list[EmbedDict]) -> bool:
        """Add vectors to collection.

        Args:
            collection_name (str): Name of collection for vector upload.
            embeddings (list[EmbedDict]): dict with embedding and payload.

        Returns:
            bool: True if successfully added vectors, False if not

        Raises:
            VecDBClientError: If error encountered during validation.

        """
        points = []
        for idx, embedding in enumerate(embeddings):
            try:
                point: dict[str, int | list[float] | str | float] = {"id": idx, "vector": embedding["embedding"]}
                for k, v in embedding["payload"].items():
                    point[k] = v

            except Exception as e:
                logger.exception("Point validation unsuccessful")
                raise VecDBClientError("Error encountered validating points for vectors") from e
            else:
                points.append(point)

        if self.sync_client and self.async_client:
            try:
                operation_info: dict[str, Any] = await self.async_client.upsert(
                    collection_name=collection_name,
                    data=points,
                )

            except Exception as e:
                logger.exception("Error in adding vectors to %s collection", collection_name)
                raise VecDBClientError(f"Unable to upsert vectors: {e!s}") from e

            else:
                ct_embeddings: int = len(points)

                if operation_info["upsert_count"] != ct_embeddings:
                    return False

                logger.info(
                    "Successfully uploaded %s vectors to collection %s",
                    ct_embeddings,
                    collection_name,
                )

                return True
        else:
            raise VecDBClientError("Milvus client is not initialized")

    async def query_vectors(
        self,
        collection_name: str,
        embedding: list[list[float]],
        limit: int = 3,
        query_filter: str = "",
    ) -> list[dict[str, Any]]:
        """Query vectors in vec db using a query.

        Args:
            collection_name (str): Name of collection to query.
            embedding (list[float]): Embedding of query text.
            limit (int): Number of top chunks to retrieve.
            filter (str): A scalar filtering condition to filter matching entities.

        Returns:
            list[Any]: list of vectors with payload.

        Raises:
            VecDBClientError: If index details are not available.

        """
        if self.sync_client and self.async_client:
            try:
                list_indexes_async = async_wrap(self.sync_client.list_indexes)
                collection_index: list[str] = await list_indexes_async(collection_name=collection_name)

                # Assumes there is only one index per collection, please be careful
                describe_index_async = async_wrap(self.sync_client.describe_index)
                index_details: dict[str, Any] = await describe_index_async(
                    collection_name=collection_name,
                    index_name=collection_index[0],
                )

            except Exception as e:
                logger.exception("Error encountered while getting index details in query_vectors.")
                raise VecDBClientError("Could not get index details from collection") from e
            else:
                logger.info("Querying collection %s", collection_name)

                query_returns: list[list[dict[str, Any]]] = await self.async_client.search(
                    collection_name=collection_name,
                    anns_field="vector",
                    data=embedding,
                    limit=limit,
                    search_params={"metric_type": index_details["metric_type"]},
                    output_fields=["*"],
                    filter=query_filter,
                )

                # Only return relevant data
                doc_retrieval_list: list[dict[str, Any]] = []
                for entry in query_returns[0]:
                    doc_dict = {"distance": entry["distance"]}
                    for k, v in entry["entity"].items():
                        if k == "vector":
                            continue
                        doc_dict[k] = v

                    doc_retrieval_list.append(doc_dict)

                return doc_retrieval_list
        else:
            raise VecDBClientError("Milvus client is not initialized")

    async def list_collections(self) -> list[str] | None:
        if self.sync_client:
            list_collections_async = async_wrap(self.sync_client.list_collections)
            return await list_collections_async()
        raise VecDBClientError("Milvus client is not initialized")

    async def has_connection(self) -> bool:
        if self.sync_client and self.async_client:
            has_connection_async = async_wrap(connections.has_connection)
            async_conn: bool = await has_connection_async(self.async_client._using)
            sync_conn: bool = await has_connection_async(self.sync_client._using)
            return all([async_conn, sync_conn])
        raise VecDBClientError("Milvus client is not initialized")

    async def create_snapshot(self, collection_name: str) -> bool:
        # TODO(@joaquindas)
        return False

    async def recover_from_snapshot(self, collection_name: str, filename: str, wait: bool = True) -> None:
        # TODO(@joaquindas)
        pass

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Milvus."""
        if self.sync_client and self.async_client:
            has_collection_async = async_wrap(self.sync_client.has_collection)
            return await has_collection_async(collection_name=collection_name)
        raise VecDBClientError("Milvus client is not initialized")

    async def num_entities(self, collection_name: str, timeout: float | None = None) -> int:
        """Check number of entities in the collection.

        Args:
            collection_name (str): Name of collection
            timeout (float, optional): Timeout for request

        Returns:
            int: number of entities in collection.

        Raises:
            VecDBClientError: if client is not initialized.

        """
        if self.sync_client and self.async_client:
            stats_async = async_wrap(self.sync_client.get_collection_stats)
            stats = await stats_async(collection_name, timeout=timeout)
            return stats.get("row_count", 0)
        raise VecDBClientError("Milvus client is not initialized")

    async def delete_by_filter(self, collection_name: str, delete_filter: str) -> bool:
        """Delete vectors from collection based on a filter.

        Args:
            collection_name (str): Name of target collection.
            filter (str): Filter to use for deleting vectors.

        Returns:
            bool: True if successful.

        Raises:
            VecDBClientError: If any errors encountered during deletion.

        """
        if self.sync_client and self.async_client:
            try:
                _ = await self.async_client.delete(
                    collection_name=collection_name,
                    filter=delete_filter,
                )
                logger.info("Deleted vectors from %s using filter: %s", collection_name, filter)
            except Exception as e:
                logger.exception("Error deleting vectors from %s using filter: %s", collection_name, filter)
                raise VecDBClientError("Encountered error deleting vectors") from e
            else:
                return True
        raise VecDBClientError("Milvus client is not initialized")
