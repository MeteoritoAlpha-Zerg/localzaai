from pydantic import field_validator
from pydantic_settings import BaseSettings


class OpenTelemetryConfig(BaseSettings):
    otel_enabled: bool | None = None
    otel_export_console_enabled: bool = False
    otel_export_otlp_url: str | None = None

    stack_name: str = "local"
    environment: str = "prod"

    @field_validator("otel_export_otlp_url", mode="before")
    @classmethod
    def trim_trailing_slash(cls, value: str | None) -> str | None:
        if value and value.endswith("/"):
            return value[:-1]
        return value
