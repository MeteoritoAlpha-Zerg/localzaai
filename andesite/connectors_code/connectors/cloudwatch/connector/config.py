from pydantic import Field
from pydantic import Field

from connectors.config import ConnectorConfigurationBase

class CloudWatchConnectorConfig(ConnectorConfigurationBase):
    api_request_timeout: int = Field(default=60, description="Request timeout in seconds")

    api_max_retries: int = Field(default=3, description="Number of times to retry API requests upon failure")

    log_retention_days: int = Field(default=7, description="Default number of days to look back when querying logs")
