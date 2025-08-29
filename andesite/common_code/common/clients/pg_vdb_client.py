import json
import re
from collections.abc import Generator
from typing import Annotated, Any, final

import asyncpg  # type: ignore[import-untyped, import-not-found]
from opentelemetry import trace
from pgvector.asyncpg import register_vector  # type: ignore [import-untyped, import-not-found]
from pydantic import BaseModel, Field, field_validator
from pydantic_core import ValidationError

from common.clients.vdb_client import Distance, EmbedDict
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@final
class PgVector:
    """Client for interacting with PgVector Database."""

    def __init__(self) -> None:
        self.conn = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(
        self,
        user: str,
        password: str,
        database: str,
        host: str,
        port: str,
    ):
        """Establish connection to PostgreSQL database.

        Args:
            user (str): username of db
            password (str): pw associated with user for db
            database (str): db name
            host (str): url of host, 127.0.0.1, if local
            port (str): port for db connection

        """
        if not self.conn:
            self.conn = await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)
            if self.conn:
                try:
                    await self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    await register_vector(self.conn)
                except Exception:
                    logger().exception("Error occured while connecting to database.")
                    raise
                else:
                    logger().info("Connection to vector database successfully established.")

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if named collection exists in database."""
        if self.conn:
            response = await self.conn.fetch(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = $1);",
                collection_name,
            )
            exists: bool = response[0]["exists"]
            if exists:
                logger().info("Collection %s is found in database.", collection_name)
            return exists
        raise ValueError("Connection to database not established.")

    @staticmethod
    def _is_valid_identifier(identifier: str) -> bool:
        """Validate SQL identifier to prevent injection.

        Only allows alphanumeric characters and underscores.
        First character must be a letter or underscore.

        Args:
            identifier (str): input for sql command.

        Returns:
            bool: True if input is valid.

        """
        pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        return bool(pattern.match(identifier))

    async def create_collection(
        self,
        collection_name: str,
        vec_size: int,
        distance_method: Distance,
    ) -> bool:
        """Create a 'collection' in pgvector, if not existant.

        Args:
            collection_name (str): Name of collection to create.
            vec_size (int): dimension of each vector
            distance_method (Distance): similarity metric

        Returns:
            bool: True if collection was created, False if collection exists.

        Raises:
            ValueError: If db connection not created.
            ValidationError: If inputs fail validation.
            DuplicateTableError: If table already exists.

        """
        if await self.collection_exists(
            collection_name=collection_name,
        ):
            logger().warning(
                "Collection already exists. Set OVERWRITE argument if you would like to recreate collection."
            )
            return False

        # TODO: write OVERWRITE logic

        class CreateCollectionInputs(BaseModel):
            collection_name: str
            vec_size: Annotated[int, Field(gt=0, lt=20000)]

            @field_validator("collection_name", mode="before")
            @classmethod
            def _is_valid_identifier(cls, identifier: str):
                """Validate SQL identifier to prevent injection.

                Only allows alphanumeric characters and underscores.
                First character must be a letter or underscore.

                Args:
                    identifier (str): input for sql command.

                Returns:
                    str: identifier input, if valid.

                Raises:
                    ValidationError: If doesn't pass validation.

                """
                pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
                if not bool(pattern.match(identifier)):
                    raise ValidationError("Invalid collection name: %s", collection_name)
                return identifier

        try:
            _ = CreateCollectionInputs.model_validate({})
        except ValidationError:
            logger().exception("create_collection inputs failed validation.")
            raise

        if self.conn:
            try:
                response = await self.conn.execute(
                    f"CREATE TABLE {collection_name} (id bigserial PRIMARY KEY, embedding vector({vec_size}), payload json)",
                )
            except asyncpg.exceptions.DuplicateTableError:
                logger().exception("Table creation unsuccesful; table %s already exists", collection_name)
                raise
            else:
                if response == "CREATE TABLE":
                    logger().info("Table %s successfully created.", collection_name)
                    return True
                return False
        else:
            raise ValueError("Connection to Database not established.")

    @staticmethod
    def _generate_batches(lst: list[Any], batch_size: int):
        for i in range(0, len(lst), batch_size):
            yield lst[i : i + batch_size]

    async def add_vectors(
        self,
        collection_name: str,
        embeddings: list[EmbedDict],
    ) -> bool:
        """Add vectors to collection.

        Args:
            collection_name (str): Name of collection for vector upload.
            embeddings (list[EmbedDict]): dict with embedding and payload.

        Returns:
            bool: True if successfully added vectors, False if not

        Raises:
            ValueError: If db connection not established.

        """

        class AddVectorsInputs(BaseModel):
            collection_name: str
            embeddings: list[EmbedDict]

            @field_validator("collection_name", mode="before")
            @classmethod
            def _is_valid_identifier(cls, identifier: str):
                """Validate SQL identifier to prevent injection.

                Only allows alphanumeric characters and underscores.
                First character must be a letter or underscore.

                Args:
                    identifier (str): input for sql command.

                Returns:
                    str: identifier input, if valid.

                Raises:
                    ValidationError: If doesn't pass validation.

                """
                pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
                if not bool(pattern.match(identifier)):
                    raise ValidationError("Invalid collection name: %s", collection_name)
                return identifier

        try:
            _ = AddVectorsInputs.model_validate({"collection_name": collection_name, "embeddings": embeddings})
        except ValidationError:
            logger().exception("Inputs for add_vectors failed type validation.")

        if self.conn:
            batches: Generator[list[EmbedDict], None] = self._generate_batches(embeddings, 20)

            for batch in batches:
                embed_string = ""
                flat_params = []
                for i in range(len(batch)):
                    embed_string += f"(${i * 2 + 1}, ${i * 2 + 2}), "
                    flat_params.append(batch[i]["embedding"])
                    flat_params.append(json.dumps(batch[i]["payload"]))
                embed_string = embed_string[:-2]
                try:
                    response = await self.conn.execute(
                        f"INSERT INTO {collection_name} (embedding, payload) VALUES {embed_string}",
                        *flat_params,
                    )
                except Exception:
                    logger().exception("Error uploading vectors.")
                    return False
                else:
                    if "INSERT" in response:
                        logger().info("Vectors successfully added to collection %s", collection_name)
            return True
        raise ValueError("Connection to Database not established.")

    async def query_vectors(
        self,
        collection_name: str,
        embedding: list[list[float]],
        limit: Annotated[int, Field(gt=1, lt=20)] = 3,
        distance: Distance = Distance.COSINE,
    ) -> list[asyncpg.Record]:
        """Query vectors in vec db using a query.

        Args:
            collection_name (str): Name of collection to query.
            embedding (list[float]): Embedding of query text.
            limit (int): Number of top chunks to retrieve.

        Returns:
            list[asyncpg.Record]: list of vectors with payload.

        Raises:
            ValueError: If db connection not established.
            ValidationError: If inputs don't pass type validation.

        """

        class QueryVectorInputs(BaseModel):
            distance: Distance
            collection_name: str
            limit: Annotated[int, Field(gt=1, lt=20)]

            @field_validator("collection_name", mode="before")
            @classmethod
            def _is_valid_identifier(cls, identifier: str):
                """Validate SQL identifier to prevent injection.

                Only allows alphanumeric characters and underscores.
                First character must be a letter or underscore.

                Args:
                    identifier (str): input for sql command.

                Returns:
                    str: identifier input, if valid.

                Raises:
                    ValidationError: If doesn't pass validation.

                """
                pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
                if not bool(pattern.match(identifier)):
                    raise ValidationError("Invalid collection name: %s", collection_name)
                return identifier

        try:
            _ = QueryVectorInputs.model_validate(
                {"distance": distance, "collection_name": collection_name, "limit": limit}
            )
        except ValidationError:
            logger().exception("Inputs failed validation for querying vectors.")
            raise

        match distance:
            case Distance.COSINE:
                distance_sign = "<=>"
            case Distance.DOT:
                distance_sign = "<#>"
            case _:
                distance_sign = "<->"

        if self.conn:
            try:
                sql = f"SELECT * FROM {collection_name} ORDER BY embedding {distance_sign} $1 LIMIT {limit}"

                response = await self.conn.fetch(
                    sql,
                    embedding,
                )
            except:
                logger().exception("Error while querying vectors.")
                raise
            else:
                return response
        else:
            raise ValueError("Connection to Database not established.")

    async def recover_from_snapshot(
        self,
        collection_name: str,
        filename: str,
        wait: bool = True,
    ) -> None:
        # TODO: Contingent on deployment strategy
        pass

    async def create_snapshot(self, collection_name: str) -> bool:
        # TODO: Contingent on deploymnent strategy
        if self.conn:
            try:
                _ = await self.conn.execute("")
            except Exception:
                logger().exception("Error while creating snapshot of collection %s", collection_name)
                return False
            else:
                return True
        else:
            raise ValueError("Connection to Database not established.")

    async def list_collections(self) -> list[str] | None:
        """List all collections available.

        Returns:
            list[str]: Collection names in simple string format.

        Raises:
            ValueError: If db connection not established.

        """
        if self.conn:
            try:
                response = await self.conn.fetch("SELECT * FROM pg_tables WHERE schemaname = 'public';")
            except Exception:
                logger().exception("Error while retrieving list of tables.")
            else:
                collection_list: list[str] = [x["tablename"] for x in response]
                return collection_list
        else:
            raise ValueError("Connection to Database not established.")
        return None

    async def index_collection(self, collection_name: str, distance: Distance) -> bool:
        """Index specified collection.

        Args:
            collection_name (str): Name of collection to be indexed.
            distance (Distance): Distance metric to be used for indexing.

        Returns:
            bool: True if indexing was successful, False otherwise.

        Raises:
            ValueError: If db connection is not established.

        """

        class IndexCollectionInputs(BaseModel):
            collection_name: str
            distance: Distance

            @field_validator("collection_name", mode="before")
            @classmethod
            def _is_valid_identifier(cls, identifier: str):
                """Validate SQL identifier to prevent injection.

                Only allows alphanumeric characters and underscores.
                First character must be a letter or underscore.

                Args:
                    identifier (str): input for sql command.

                Returns:
                    str: identifier input, if valid.

                Raises:
                    ValidationError: If doesn't pass validation.

                """
                pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
                if not bool(pattern.match(identifier)):
                    raise ValidationError("Invalid collection name: %s", collection_name)
                return identifier

        try:
            _ = IndexCollectionInputs.model_validate({"collection_name": collection_name, "distance": distance})
        except ValidationError:
            logger().exception("Inputs failed validation for querying vectors.")
            raise

        match distance:
            case Distance.COSINE:
                distance_input = "vector_cosine_ops"
            case Distance.DOT:
                distance_input = "vector_ip_ops"
            case _:
                distance_input = "vector_l2_ops"

        if self.conn:
            try:
                response = await self.conn.execute(
                    f"CREATE INDEX ON {collection_name} USING hnsw (embedding {distance_input})"
                )
            except Exception:
                logger().exception("Error indexing collection %s", collection_name)
                return False
            else:
                if "CREATE INDEX" in response:
                    logger().info("Succesfully created index for %s with %s", collection_name, distance_input)
                return True
        else:
            raise ValueError("Connection to Database not established.")

    async def num_entities(self, collection_name: str, timeout: float | None = None) -> int:
        """Returns the number of entities in the collection."""
        # TODO: Make this work

        if not self.conn:
            raise ValueError("Connection to Database not established.")
        try:
            result = await self.conn.fetchval(f"SELECT COUNT(*) FROM {collection_name};")
            return int(result)
        except Exception:
            logger().exception("Error while counting entities in collection %s", collection_name)
            return 0

    async def delete_by_filter(self, collection_name: str, delete_filter: str) -> bool:
        """Delete vectors from collection based on a filter."""
        # TODO: Make this work

        if not self.conn:
            raise ValueError("Connection to Database not established.")
        try:
            query = f"DELETE FROM {collection_name} WHERE {filter};"
            await self.conn.execute(query)
            logger().info("Deleted vectors from %s using filter: %s", collection_name, filter)
            return True
        except Exception:
            logger().exception("Error deleting vectors from %s using filter: %s", collection_name, filter)
            return False
