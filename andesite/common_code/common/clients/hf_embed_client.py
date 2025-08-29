"""Use HF Embedding model.

This module contains an interface for using an embedding model using
 sentence-transformers.

Classes:
    HFEmbedClient

Functions:
    make_batches(data) -> Generator[list[str]]
    post(data) -> list[list[float]]
    embed_passages(texts) -> list[list[float]]
    embed_query(text) -> list[list[float]]

Usage Example:
    embed_model = HFEmbedClient()

    # Embed single query
    sample_text = "This is a test."
    vector = embed_model.embed_query(text=sample_text)

    # Embed corpus
    corpus = ["test 1", "test 2", "test 3"]
    vectors = embed_model.embed_passages(texts = corpus)
"""

from collections.abc import Generator
from typing import final

import httpx
from opentelemetry import trace

from common.clients.embed_client import EmbedClientConfig, EmbedModel, EmbedModelConfig
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class HFConfig(EmbedModelConfig):
    hf: EmbedClientConfig


@final
class HFEmbedClient(EmbedModel):
    """Embedding model with embedding functionality."""

    def __init__(self, config: HFConfig) -> None:
        self.config: HFConfig = config
        self.url: str = config.hf.url
        self.headers: dict[str, str] = {"Content-Type": "application/json"}

    @staticmethod
    def make_batches(data: list[str], batch_size: int) -> Generator[list[str]]:
        """Break up long inputs into batches.

        Args:
            data (list[str]): Texts to embed.
            batch_size (int): n for max batch size.

        Yields:
            Generator[list[str]]: Generates batches.

        """
        for i in range(0, len(data), batch_size):
            yield data[i : i + batch_size]

    async def post(self, data: list[str] | str) -> list[list[float]] | None:
        """HTTP Post request for embedding endpoint.

        Args:
            data (list[str] | str): Individual query or list of docs to embed.

        Returns:
            list[list[float]] : List of embeddings from text.

        """
        batch_threshold = 25
        if isinstance(data, list) and len(data) > batch_threshold:
            batches = list(self.make_batches(data=data, batch_size=batch_threshold))
            responses: list[list[float]] = []
            total_batches = len(batches)
            for idx, batch in enumerate(batches):
                logger().info("Processing Embedding Batch %s / %s", idx + 1, total_batches)
                embeds = await self.post(data=batch)
                if embeds:
                    responses.extend(embeds)
            return responses

        timeout = 300
        json_data = {"inputs": data}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url=self.url,
                    headers=self.headers,
                    json=json_data,
                    timeout=timeout,
                )
                _ = response.raise_for_status()
            except Exception:
                logger().exception("Unexpected Error Occured")

            else:
                return response.json()
        return None

    async def embed_passages(self, texts: list[str]) -> list[list[float]] | None:
        """Embed passages or corpus.

        Args:
            texts (list[str]): texts being used as corpus for vectors.

        Returns:
            list[list[float]] | None: list of embeddings.

        """
        logger().info("Encoding passages.")
        try:
            response = await self.post(data=texts)
        except Exception:
            logger().exception("Unexpected error occurred.")
            return None
        else:
            return response

    async def embed_query(self, text: str) -> list[list[float]] | None:
        """Embed query.

        Args:
            text (str): Text of query.

        Returns:
            list[list[float]]: embedding of text query.

        """
        logger().info("Encoding query.")
        query_prompt = "Represent this sentence for searching relevant passages:"
        query = query_prompt + text
        try:
            response = await self.post(data=query)
        except Exception:
            logger().exception("Unexpected error ocurred.")
            return None
        else:
            return response
