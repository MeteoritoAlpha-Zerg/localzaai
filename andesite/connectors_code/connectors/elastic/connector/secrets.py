from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class ElasticSecrets(ConnectorSecretsInterface):
    api_key: SecretStr
