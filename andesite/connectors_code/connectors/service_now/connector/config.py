from pydantic import Field
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase

class ServiceNowConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    instance_url: str = Field("", description="The URL of the ServiceNow instance")
    username: str = Field("", description="ServiceNow username")
    password: StorableSecret = Field(..., description="ServiceNow password")
