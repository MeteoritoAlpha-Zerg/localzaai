from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class ConfluenceSecrets(ConnectorSecretsInterface):
    api_key: SecretStr
