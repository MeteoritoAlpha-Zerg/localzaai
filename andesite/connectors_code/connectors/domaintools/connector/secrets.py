from pydantic import SecretStr

from connectors.connector import ConnectorSecretsInterface


class DomainToolsSecrets(ConnectorSecretsInterface):
    api_username: SecretStr
    api_key: SecretStr
