
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase


class SentinelOneConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    api_endpoint: str
    token: StorableSecret
