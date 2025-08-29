from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class JIRASecrets(ConnectorSecretsInterface):
    api_key: SecretStr
