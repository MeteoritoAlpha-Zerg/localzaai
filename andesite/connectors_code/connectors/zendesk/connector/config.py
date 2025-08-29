from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class ZendeskConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    subdomain: str
    email: str
    api_token: StorableSecret
    api_request_timeout: int = Field(default=30, description="Request timeout in seconds")
    api_max_retries: int = Field(default=3, description="Maximum number of API request retries")
