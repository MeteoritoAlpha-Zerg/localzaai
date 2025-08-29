"""Use Cohere Embedding model hosted in Azure.

This module contains a client for using an embedding model hosted on Azure endpoint.

Classes:
    AzureEmbedClient

Functions:
    make_batches(data) -> Generator[list[str]]
    post(data) -> list[list[float]]
    embed_passages(texts) -> list[list[float]]
    embed_query(text) -> list[list[float]]

Usage Example:
    embed_model = AzureEmbedClient()

    # Embed single query
    sample_text = "This is a test."
    vector = embed_model.embed_query(text=sample_text)

    # Embed corpus
    corpus = ["test 1", "test 2", "test 3"]
    vectors = embed_model.embed_passages(texts = corpus)
"""

from collections.abc import Generator
from enum import Enum
from typing import Any, ClassVar, final

import httpx
from opentelemetry import trace
from pydantic import BaseModel, SecretStr
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)()
tracer = trace.get_tracer(__name__)


class InputType(str, Enum):
    """Enum for embedding type."""

    def __str__(self) -> str:
        return str(self.value)

    TEXT = "text"
    DOCUMENT = "document"
    QUERY = "query"


class AzureConfig(BaseModel):
    url: str
    token: SecretStr
    api_version: str


class AzureEmbedModelParams(Enum):
    """Enum to determine vector size for embedding model."""

    COHERE_EMBED3 = 1024
    COHERE_EMBED4 = 1536


class AzureHTTPResponse(BaseModel):
    """Model for Embeding post response from Azure."""

    id: str
    object: str
    data: list[dict[str, Any]]
    model: str
    usage: dict[str, Any]


@final
class AzureEmbedClient:
    """Client for Azure Embedding."""

    base_url: str | None = None
    api_key: str | None = None
    headers: dict[str, str] | None = None
    api_version: str | None = None
    _model: AzureEmbedModelParams | None = None
    _instance: ClassVar["AzureEmbedClient | None"] = None

    @classmethod
    async def initialize(
        cls, config: AzureConfig, model: AzureEmbedModelParams = AzureEmbedModelParams.COHERE_EMBED3
    ) -> None:
        if cls._instance:
            logger.warning("AzureEmbedClient is already initialized. Use get_client method")
            return

        cls.base_url = config.url
        cls.api_key = config.token.get_secret_value()
        cls.headers = {
            "Authorization": f"Bearer {cls.api_key}",
            "Content-Type": "application/json",
        }
        cls.api_version = config.api_version
        cls._model = model
        cls._instance = cls()

    @classmethod
    def get_client(cls) -> "AzureEmbedClient":
        if not cls._instance:
            raise ValueError("AzureEmbedClient not initialized")
        return cls._instance

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

    async def post(
        self,
        data: list[str] | str,
        input_type: InputType = InputType.TEXT,
    ) -> list[dict[str, Any]]:
        """HTTP Post request for embedding endpoint.

        Args:
            data (list[str] | str): Individual query or list of docs to embed.
            input_type (InputType): Enum to register input as query, text, or document.

        Returns:
            list[list[float]] : List of embeddings from text.

        """
        batch_threshold = 25
        if isinstance(data, list) and len(data) > batch_threshold:
            batches = list(self.make_batches(data=data, batch_size=batch_threshold))
            responses: list[dict[str, Any]] = []
            total_batches = len(batches)
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("[green]Processing Embedding Batches", total=total_batches)
                for idx, batch in enumerate(batches):
                    logger.info("Processing Embedding Batch %s / %s", idx + 1, total_batches)
                    embeds = await self.post(data=batch)
                    if embeds:
                        responses.extend(embeds)
                    progress.update(
                        task, advance=1, description=f"[green]Processing Embedding Batches ({idx + 1}/{total_batches})"
                    )

            return responses

        timeout = 300
        payload = {
            "input": data if isinstance(data, list) else [data],
            "input_type": str(input_type),
            "encoding_format": "float",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url=f"{self.base_url}/embeddings?api-version={self.api_version}",
                    headers=self.headers,
                    json=payload,
                    timeout=timeout,
                )
                _ = response.raise_for_status()
                validated_response: AzureHTTPResponse = AzureHTTPResponse.model_validate_json(response.content)
            except Exception:
                logger.exception("Unexpected Error Occured")
                raise

            else:
                return validated_response.data

    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed passages or corpus.

        Args:
            texts (list[str]): texts being used as corpus for vectors.

        Returns:
            list[list[float]]: list of embeddings.

        Raises:
            ValueError: If response is not returned or "data" isn't in response.

        """
        if not self.api_version:
            raise ValueError("API Version is not found in config.")

        logger.info("Encoding passages.")
        try:
            response: list[dict[str, Any]] = await self.post(data=texts, input_type=InputType.DOCUMENT)
        except Exception:
            logger.exception("Unexpected error occurred.")
            raise
        else:
            if not response:
                raise ValueError
            embeddings: list[list[float]] = [x["embedding"] for x in response]
            logger.info("Succesfully generated embedding for corpus")
            return embeddings

    async def embed_query(self, text: str) -> list[list[float]]:
        """Embed query.

        Args:
            text (str): Text of query.

        Returns:
            list[list[float]]: embedding of text query.

        Raises:
            ValueError: If response is not returned or "data" isn't in response.

        """
        if not self.api_version:
            raise ValueError("API Version is not found in config.")

        logger.info("Encoding query.")
        try:
            response = await self.post(data=text, input_type=InputType.QUERY)
        except Exception:
            logger.exception("Unexpected error ocurred.")
            raise
        else:
            if not response:
                raise ValueError
            embeddings: list[list[float]] = [x["embedding"] for x in response]
            logger.info("Succesfully generated embedding for text: %s", text)
            return embeddings

    async def get_dimensions(self) -> int:
        """Get dimensions for embedding, given a model."""
        if self._model:
            return self._model.value
        raise ValueError("Model params not specified")
