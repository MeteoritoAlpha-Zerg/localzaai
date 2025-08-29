from typing import Optional
from pydantic import Field
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase

class GuarddutyConnectorConfig(ConnectorConfigurationBase):
    """
    Configuration for AWS GuardDuty Connector
    """
    # Primary configuration fields
    aws_region: str = Field(
        default="us-west-2",
        description="AWS region to connect to"
    )
    aws_access_key_id: StorableSecret = Field(
        ...,
        description="AWS Access Key ID for authenticating with AWS services"
    )
    aws_secret_access_key: StorableSecret = Field(
        ...,
        description="AWS Secret Access Key for authenticating with AWS services"
    )
    aws_session_token: Optional[StorableSecret] = Field(
        default=None,
        description="AWS Session Token for authenticating with AWS services"
    )

    # Additional operational settings
    api_request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    api_max_retries: int = Field(
        default=3,
        description="Number of times to retry API requests upon failure"
    )

    findings_max_results: int = Field(
        default=50,
        description="Maximum number of findings to return per page"
    )
    findings_days_back: int = Field(
        default=30,
        description="Default number of days to look back when querying findings"
    )
