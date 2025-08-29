from typing import Optional

from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class CrowdstrikeConnectorConfig(ConnectorConfigurationBase):
    """
    Configuration for CrowdStrike connector.
    """

    # CrowdStrike host (optional if using url)
    host: Optional[str] = Field(None, description="CrowdStrike host, e.g. api.crowdstrike.com")
    url: Optional[str] = Field(
        None,
        description="Base URL for the CrowdStrike API, e.g. https://api.crowdstrike.com",
    )
    client_id: str = Field(..., description="CrowdStrike API client ID")
    client_secret: StorableSecret = Field(..., description="CrowdStrike API client secret")

    api_request_timeout: int = Field(default=30, description="Request timeout in seconds")
    api_max_retries: int = Field(default=3, description="Number of times to retry API requests upon failure")
