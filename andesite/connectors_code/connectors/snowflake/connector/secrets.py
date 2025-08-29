
from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class SnowflakeSecrets(ConnectorSecretsInterface):
    password: SecretStr
