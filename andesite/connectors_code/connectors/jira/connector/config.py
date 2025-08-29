from pydantic import Field
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase

class JIRAConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    url: str = Field(..., description="Base URL for the JIRA instance")
    api_key: StorableSecret = Field(..., description="API token for JIRA authentication")
    email: str = Field(..., description="Email address for JIRA authentication")
