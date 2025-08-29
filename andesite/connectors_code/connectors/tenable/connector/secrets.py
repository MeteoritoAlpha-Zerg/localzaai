from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class TenableSecrets(ConnectorSecretsInterface):
    access_key: SecretStr
    secret_key: SecretStr
