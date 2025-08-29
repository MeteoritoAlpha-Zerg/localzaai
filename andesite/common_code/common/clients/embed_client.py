from abc import ABCMeta, abstractmethod

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbedModelConfig(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(  # type: ignore [misc]
        env_prefix="EMBED_MODEL_",
        env_nested_delimiter="__",
        env_nested_max_split=1,
        extra="ignore",
        env_ignore_empty=True,
    )


class EmbedClientConfig(BaseModel):
    url: str
    token: str
    api_version: str | None = None
    enabled: bool = False


class EmbedModel(metaclass=ABCMeta):
    """Abstract Base Class for Emedding Model Clients."""

    @abstractmethod
    def __init__(self, config: EmbedClientConfig):
        pass

    @abstractmethod
    async def embed_passages(self, texts: list[str]) -> list[list[float]] | None:
        """Embed passages or corpus.

        Args:
            texts (list[str]): texts being used as corpus for vectors.

        Returns:
            list[list[float]] | None: list of embeddings.

        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> list[list[float]] | None:
        """Embed query.

        Args:
            text (str): Text of query.

        Returns:
            list[list[float]]: embedding of text query.

        """
        pass
