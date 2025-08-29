from pydantic import BaseModel, Field


class BaseModelConfig(BaseModel):
    """
    The BaseModelConfig contains properties that are shared across all model configurations.
    """

    enabled: bool = False
    provider: str = Field(min_length=3)
    model: str = Field(min_length=3)
    default_request_timeout_seconds: int = 120

    custom_header_name: str | None = None
    custom_header_value: str | None = None
