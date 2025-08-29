
from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class SharePointSecrets(ConnectorSecretsInterface):
    access_token: SecretStr
