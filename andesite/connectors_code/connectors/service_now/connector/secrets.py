from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class ServiceNowSecrets(ConnectorSecretsInterface):
    password: SecretStr
