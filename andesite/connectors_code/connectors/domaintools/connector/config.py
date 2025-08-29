from common.models.secret import StorableSecret
from connectors.connector import ConnectorConfigurationBase


class DomainToolsConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    api_username: StorableSecret
    api_key: StorableSecret
