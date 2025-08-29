from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class SalesforceSecrets(ConnectorSecretsInterface):
    username: SecretStr
    password: SecretStr
    security_token: SecretStr
