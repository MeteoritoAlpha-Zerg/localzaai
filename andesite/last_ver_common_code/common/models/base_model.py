from pydantic import BaseModel, Field


class BaseModelConfig(BaseModel):
    """
    The BaseModelConfig contains properties that are shared across all model configurations.
    """

    enabled: bool = False
    provider: str = Field(min_length=3)
    model: str = Field(min_length=3)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    max_tokens: int = 4000
    request_timeout_seconds: int = 120

    custom_header_name: str | None = None
    custom_header_value: str | None = None
