from pydantic import SecretStr

from connectors.connector import ConnectorSecretsInterface


class CrowdstrikeSecrets(ConnectorSecretsInterface):
    client_secret: SecretStr
