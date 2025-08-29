from pydantic import SecretStr

from connectors.connector import ConnectorConfig


class TenableConnectorConfig(ConnectorConfig):
    access_key: SecretStr
    secret_key: SecretStr
