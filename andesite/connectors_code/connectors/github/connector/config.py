from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class GithubConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    # Provide a default URL so that when the registry creates a default config via create(), it has a value
    url: str = Field(default="https://api.github.com", description="GitHub API base URL")
    access_token: StorableSecret = Field(..., description="GitHub API access token")
