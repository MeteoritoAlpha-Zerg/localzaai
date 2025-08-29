
from pydantic import SecretStr

from connectors.connector import ConnectorSecretsInterface


class SentinelOneSecrets(ConnectorSecretsInterface):
    token: SecretStr
