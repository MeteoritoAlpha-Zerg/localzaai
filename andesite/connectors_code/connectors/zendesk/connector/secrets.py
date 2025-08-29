
from pydantic import SecretStr

from connectors.connector import ConnectorSecretsInterface

class ZendeskSecrets(ConnectorSecretsInterface):
    api_token: SecretStr
