from typing import Any, Literal
from common.jsonlogging.jsonlogger import Logging
from elasticsearch import AsyncElasticsearch  # type: ignore
from pydantic import SecretStr

"""
This module is responsible for managing the Elastic clients used by the application.
It provides a way to initialize the clients with the appropriate configuration.
"""
logger = Logging.get_logger(__name__)


class ElasticException(Exception):
    pass


class ElasticClient:
    _elastic_app: AsyncElasticsearch

    def __init__(self, url: str, api_key: str):
        self._elastic_app = AsyncElasticsearch(url, api_key=api_key, verify_certs=False)

    @classmethod
    def get_client(cls, url: str, api_key: SecretStr) -> "ElasticClient":
        return ElasticClient(url=url, api_key=api_key.get_secret_value())

    async def close(self):
        """
        Closes the elasticsearch client connection
        """
        await self._elastic_app.close()

    async def list_indices(self) -> list[str]:
        """
        Lists all (non-internal) elasticsearch indices
        """
        indices = (await self._elastic_app.cat.indices(h="index")).splitlines()
        return [index for index in indices if not index.startswith(".internal.")]

    async def list_index_fields(self, index: str) -> dict[str, Any]:
        return (await self._elastic_app.indices.get_mapping(index=index)).body

    async def count(self, index: str, query: dict[str, Any]) -> int:
        response = await self._elastic_app.count(body=query, index=index)
        return response.get("count", -1)

    async def search(self, index: str, query: dict[str, Any], size: int | None = None) -> list[dict[Literal["_source", "_id"], Any]]:
        # Default size is 10 anyways, but passing size=None, causes an error in the elasticsearch sdk client
        response = await self._elastic_app.search(index=index, body=query, size=size or 10)
        return response.get("hits", {}).get("hits", [])

    async def paginated_search(self, index: str, query: dict[str, Any], size: int = 1000, max_pages: int = 1000) -> list[dict[Literal["_source", "_id"], Any]]:
        hits = []
        search_after = None

        for page_num in range(max_pages):
            query["size"] = size
            if search_after:
                query["search_after"] = search_after

            response = await self._elastic_app.search(index=index, body=query)
            page_hits = response.get("hits", {}).get("hits", [])

            if not page_hits:
                break

            hits.extend(page_hits)
            search_after = page_hits[-1].get("sort")

            if not search_after:
                break

            if page_num == max_pages - 1:
                logger().warning("Max pages reached, stopping pagination")

        return hits

    async def agg_search(self, index: str, query: dict[str, Any]) -> dict[str, Any]:
        response = await self._elastic_app.search(body=query, index=index)

        return response.get("aggregations", {})

    async def search_full_response(self, index: str, query: dict[str, Any]) -> dict[str, Any]:
        """
        Unlike `search`, which returns only the list of matched documents (`hits`), this method returns the entire
        response body, including metadata, aggregations, and other fields
        """
        response = await self._elastic_app.search(index=index, body=query)
        return response.body
