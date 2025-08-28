from common.models.secret import StorableSecret
from connectors.connector import ConnectorConfigurationBase


class TenableConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    access_key: StorableSecret
    secret_key: StorableSecret
