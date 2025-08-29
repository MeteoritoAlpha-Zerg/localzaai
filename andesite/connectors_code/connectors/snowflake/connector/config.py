from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class SnowflakeConnectorConfig(ConnectorConfigurationBase):
    """Configuration for the Snowflake Connector. Inherits from ConnectorConfigurationBase. Uses account_id, user, and password as credentials, and defines API timeout and retry parameters."""
    account_id: str = Field(..., description="Snowflake account ID")
    user: str = Field(..., description="Snowflake username")
    password: StorableSecret = Field(..., description="Snowflake password")

    api_request_timeout: int = Field(default=30, description="Snowflake API request timeout in seconds")
    api_max_retries: int = Field(default=3, description="Maximum number of API call retries")
