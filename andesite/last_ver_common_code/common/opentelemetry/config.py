from typing import Optional
from pydantic_settings import BaseSettings


class OpenTelemetryConfig(BaseSettings):
    is_otel_enabled: bool = False
    is_otel_console_export_enabled: bool = False
    grafana_alloy_url: Optional[str] = None
    stack_name: str = "local"
    environment: str = "prod"
