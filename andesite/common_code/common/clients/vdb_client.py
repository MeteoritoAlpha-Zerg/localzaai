from enum import Enum
from typing import Any, Protocol, TypedDict, final, runtime_checkable


class EmbedDict(TypedDict):
    """Dictionary schema for embeddings in add_vectors fx."""

    embedding: list[float]
    payload: dict[str, str | float | int]


class Distance(str, Enum):
    """Type of internal tags, build from payload Distance function types used to compare vectors."""

    def __str__(self) -> str:
        return str(self.value)

    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"
    MANHATTAN = "Manhattan"


class IndexMethod(str, Enum):
    """Vector Index Methods for db."""

    def __str__(self) -> str:
        return str(self.value)

    HNSW = "HNSW"
    FLAT = "FLAT"
    IVF_FLAT = "IVF_FLAT"
    IVF_SQ8 = "IVF_SQ8"
    IVF_PQ = "IVF_PQ"
    GPU_IVF_FLAT = "GPU_IVF_FLAT"
    DISKANN = "DISKANN"
    AUTOINDEX = "AUTOINDEX"


@final
class VecDBClientError(Exception):
    """Exception raised for errors in VecDBClient functions.

    Attributes:
        message (str): explanation of the error.

    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


@runtime_checkable
class VecDBClient(Protocol):
    """Protocol for Vector DB Clients."""

    @classmethod
    async def initialize(cls, config):
        """Initialize vector db client with config."""
        ...

    async def create_collection(
        self,
        collection_name: str,
        vec_size: int,
        distance_method: Distance,
    ) -> bool: ...

    async def add_vectors(
        self,
        collection_name: str,
        embeddings: list[EmbedDict],
    ) -> bool: ...

    async def query_vectors(
        self,
        collection_name: str,
        embedding: list[list[float]],
        limit: int = 3,
    ) -> list[Any]: ...

    async def list_collections(self) -> list[str] | None: ...

    async def create_snapshot(self, collection_name: str) -> bool: ...

    async def recover_from_snapshot(
        self,
        collection_name: str,
        filename: str,
        wait: bool = True,
    ) -> None: ...

    async def delete_by_filter(self, collection_name: str, delete_filter: str) -> bool: ...

    async def collection_exists(self, collection_name: str) -> bool: ...

    async def num_entities(self, collection_name: str, timeout: float | None = None) -> int: ...
