from typing import Any, Literal

from common.jsonlogging.jsonlogger import Logging
from pydantic import SecretStr

from elasticsearch import Elasticsearch  # type: ignore

"""
This module is responsible for managing the Elastic clients used by the application.
It provides a way to initialize the clients with the appropriate configuration.
"""
logger = Logging.get_logger(__name__)


class ElasticException(Exception):
    pass


class ElasticClient:
    _elastic_app: Elasticsearch

    def __init__(self, url: str, api_key: str):
        self._elastic_app = Elasticsearch(url, api_key=api_key, verify_certs=False)

    @classmethod
    def get_client(cls, url: str, api_key: SecretStr) -> "ElasticClient":
        return ElasticClient(url=url, api_key=api_key.get_secret_value())

    def list_indices(self) -> list[str]:
        """
        Lists all (non-internal) elasticsearch indices
        """
        indices = self._elastic_app.cat.indices(h="index").splitlines()
        return [index for index in indices if not index.startswith(".internal.")]

    def list_index_fields(self, index: str) -> dict[str, Any]:
        return self._elastic_app.indices.get_mapping(index=index).body

    def count(
        self, index: str, query: dict[str, Any]
    ) -> int:
        response = self._elastic_app.count(body=query, index=index)

        return response.get("count", -1)

    def search(
        self, index: str, query: dict[str, Any]
    ) -> list[dict[Literal["_source"], Any]]:
        response = self._elastic_app.search(body=query, index=index)

        return response.get("hits", {}).get("hits", [])
