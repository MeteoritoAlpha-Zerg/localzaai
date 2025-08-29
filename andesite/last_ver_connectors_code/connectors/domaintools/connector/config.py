from pydantic import SecretStr

from connectors.connector import ConnectorConfig


class DomainToolsConnectorConfig(ConnectorConfig):
    api_username: SecretStr
    api_key: SecretStr
