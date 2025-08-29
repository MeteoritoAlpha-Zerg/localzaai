from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class ConfluenceConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    api_key: StorableSecret = Field(..., description="API Token for Confluence authentication")
    email: str = Field(..., description="Email for Confluence authentication")
    url: str = Field(..., description="URL for Confluence querying")

    api_request_timeout: int = Field(default=30, description="Request timeout in seconds")
    api_max_retries: int = Field(default=3, description="Maximum number of API request retries")
