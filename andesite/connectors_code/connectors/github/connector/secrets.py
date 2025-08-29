from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class GithubSecrets(ConnectorSecretsInterface):
    access_token: SecretStr
