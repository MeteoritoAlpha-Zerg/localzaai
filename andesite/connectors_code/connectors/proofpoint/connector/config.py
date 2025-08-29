from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class ProofpointConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    api_host: str = Field(..., description="Base URL for Proofpoint API")
    principal: str = Field(..., description="Proofpoint service principal")
    token: StorableSecret = Field(..., description="Proofpoint service token")
    request_timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries for API requests")
    campaign_id_lookback: int = Field(30, description="Number of days of campaign id data to index", lt=50)
