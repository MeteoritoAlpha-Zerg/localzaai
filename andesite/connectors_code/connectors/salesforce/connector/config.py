from pydantic import Field
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class SalesforceConnectorConfig(ConnectorConfigurationBase):
    """
    Configuration for Salesforce connector authentication and API interaction.
    """
    username: StorableSecret = Field(..., description="Salesforce username")
    password: StorableSecret = Field(..., description="Salesforce password")
    security_token: StorableSecret = Field(..., description="Salesforce security token")
    domain: str = Field(
        default="login",
        description="Salesforce login domain (e.g., login or test)"
    )
    api_version: str = Field(
        default="58.0",
        description="Salesforce API version to use"
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Number of retries for API calls upon failure"
    )
