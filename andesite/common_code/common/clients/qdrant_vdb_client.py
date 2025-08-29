"""qdrant_vdb_client module, contains all functions for interactions with Qdrant Vecdb.

This module contains an interface for interacting with Qdrant,
a vector database.

Classes:
    QdrantVector:
        Qdrant client.

Functions:
    create_collection(collection_name, vec_size, distance_method)
    add_vectors(collection_name, embeddings)
    query_vectors(collection_name, embedding, limit) -> list[ScoredPoint]
    is_collection_new(collection_name) -> bool
    is_collection_empty(collection_name, collection_count) -> bool
"""

import numpy as np
import qdrant_client  # type: ignore
from opentelemetry import trace
from pydantic import ValidationError
from qdrant_client import models  # type: ignore
from qdrant_client.models import (  # type: ignore
    OptimizersConfigDiff,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from common.clients.vdb_client import Distance, EmbedDict, VecDBClient
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class QdrantVector(VecDBClient):
    """Client for interacting with Qdrant Vector Database."""

    def __init__(self) -> None:
        self.client: qdrant_client.AsyncQdrantClient = qdrant_client.AsyncQdrantClient(url="http://localhost:6333")

    async def create_collection(
        self,
        collection_name: str,
        vec_size: int,
        distance_method: Distance = Distance.COSINE,
    ) -> bool:
        """Create a Qdrant collection, if not existant.

        Args:
            collection_name (str): Name of collection to create.
            vec_size (int): dimension of each vector
            distance_method (Distance): similarity metric

        Returns:
            bool: True if collection was created, False if collection exists.

        """
        if await self.client.collection_exists(collection_name=collection_name):
            logger().error(
                "Collection %s already exists in database. Delete collection if you would like to recreate.",
                collection_name,
            )
            return False

        match distance_method:
            case Distance.COSINE:
                distance = models.Distance.COSINE
            case Distance.DOT:
                distance = models.Distance.DOT
            case Distance.EUCLID:
                distance = models.Distance.EUCLID
            case Distance.MANHATTAN:
                distance = models.Distance.MANHATTAN
        _ = await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vec_size, distance=distance),
            optimizers_config=OptimizersConfigDiff(indexing_threshold=2000),
        )
        logger().info(
            "Qdrant Collection for %s was successfully created.",
            collection_name,
        )
        return True

    async def add_vectors(self, collection_name: str, embeddings: list[EmbedDict]) -> bool:
        """Add vectors to collection.

        Args:
            collection_name (str): Name of collection for vector upload.
            embeddings (list[EmbedDict]): dict with embedding and payload.

        Returns:
            bool: True if successfully added vectors, False if not

        """
        points = []
        for idx, embedding in enumerate(embeddings):
            try:
                point = PointStruct(
                    id=idx,
                    vector=embedding["embedding"],
                    payload=embedding["payload"],
                )
            except ValidationError:
                logger().exception("Point validation unsuccessful")
            else:
                points.append(point)

        try:
            operation_info = await self.client.upsert(
                collection_name=collection_name,
                wait=True,
                points=points,
            )
        except Exception:
            logger().exception("Error in adding vectors to %s collection", collection_name)
            return False
        else:
            ct_embeddings = len(points)
            logger().info(
                "Successfully uploaded %s vectors to collection %s",
                ct_embeddings,
                collection_name,
            )

            logger().info(operation_info)
            return True

    async def query_vectors(
        self,
        collection_name: str,
        embedding: list[list[float]],
        limit: int = 3,
    ) -> list[ScoredPoint]:
        """Query vectors in vec db using a query.

        Args:
            collection_name (str): Name of collection to query.
            embedding (list[float]): Embedding of query text.
            limit (int): Number of top chunks to retrieve.

        Returns:
            list[ScoredPoint]: list of vectors with payload.

        """
        logger().info("Querying collection %s", collection_name)
        embedding = np.array(embedding[0])  # type: ignore[assignment]
        query_returns = await self.client.query_points(
            collection_name=collection_name,
            query=embedding,
            with_payload=True,
            limit=limit,
        )
        return query_returns.points

    async def is_collection_new(self, collection_name: str) -> bool:
        """Check if collection is new.

        Gets list of all collections in qdrant database and checks if
        collection_name exists.

        Args:
            collection_name (str): Name of collection to check if exists.

        Returns:
            bool: True if collection doesn't exist.

        """
        response = await self.client.get_collections()
        collection_list = [x.name for x in response.collections]
        if collection_name in collection_list:
            logger().info("Collection %s exists in Vector Database.", collection_name)
            return False
        logger().info("Collection %s does not exist in Vector Database.", collection_name)
        return True

    async def is_collection_empty(self, collection_name: str, collection_count: int) -> bool:
        """Check if collection is empty, given name.

        This fx assumes the collection exists; to be used after
        is_collection_new(). Main objective of this function is to check
        if collection exists but is not populated or populated insufficiently.
        Important Note: Collection will be deleted entirely and recreated if
        not populated insufficiently (collection_count(arg) > points_count)

        Args:
            collection_name (str): Name of collection to check.
            collection_count (int): Count of collection to check for population.

        Returns:
            bool: True if collection is empty.

        """
        collection_info = await self.client.get_collection(collection_name=collection_name)
        point_count = collection_info.points_count
        logger().info("%s Points found in Collection %s", point_count, collection_name)
        if point_count and point_count < collection_count:
            logger().info(
                "Deleting collection %s to recreate due to being incomplete.",
                collection_name,
            )
            _ = await self.client.delete_collection(collection_name=collection_name)
            return True
        return False

    async def recover_from_snapshot(self, collection_name: str, filename: str, wait: bool = True) -> None:
        """Recover collection from snapshot stored in container.

        Args:
            collection_name (str): Desired name of collection
            filename (str): Path of snapshot file
            wait (bool): Return confirmation of recovery; true is succesful.

        Note:
            Filepath in container is:
                filename = "file:///qdrant/snapshots/<name_of_snapshot>.snapshot"

        """
        response = await self.client.recover_snapshot(
            collection_name=collection_name,
            location=filename,
            wait=wait,
        )
        if response:
            logger().info(
                "Collection %s recovered from snapshot.",
                collection_name,
            )
        else:
            logger().error(
                "Collection %s was not succesfully recovered from snapshot.",
                collection_name,
            )

    async def create_snapshot(self, collection_name: str) -> bool:
        """Generate snapshot for a collection."""
        try:
            _ = self.client.create_snapshot(collection_name=collection_name, wait=True)
        except Exception:
            logger().exception("Error when creating snapshot for %s", collection_name)
            return False
        else:
            logger().info(
                "Snapshot for Collection %s was created succesfully.",
                collection_name,
            )
            return True

    async def list_collections(self) -> list[str] | None:
        """List all collections available.

        Returns:
            list[str]: Collection names in simple string format.

        """
        try:
            response = await self.client.get_collections()
            collections = [x.name for x in response.collections]
        except Exception:
            logger().exception("Error when retrieving collection list")
            return None
        else:
            logger().info("Collections available: %s", collections)
            return collections

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Qdrant."""
        # TODO: Make this work

        try:
            return await self.client.collection_exists(collection_name=collection_name)
        except Exception:
            logger().exception("Error checking existence of collection %s", collection_name)
            return False

    async def num_entities(self, collection_name: str, timeout: float | None = None) -> int:
        """Returns the number of entities in the collection."""
        # TODO: Make this work

        try:
            collection_info = await self.client.get_collection(collection_name=collection_name)
            return collection_info.points_count or 0
        except Exception:
            logger().exception("Error getting entity count for %s", collection_name)
            return 0

    async def delete_by_filter(self, collection_name: str, filter: str) -> bool:
        """Delete vectors from collection based on a filter."""
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="filter",
                            match=models.MatchValue(value=filter),
                        )
                    ]
                ),
            )
            logger().info("Deleted vectors from %s using filter: %s", collection_name, filter)
            return True
        except Exception:
            logger().exception("Error deleting vectors from %s using filter: %s", collection_name, filter)
            return False
