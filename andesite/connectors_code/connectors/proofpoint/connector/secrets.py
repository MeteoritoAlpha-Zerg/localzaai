from pydantic import SecretStr

from connectors.connector import ConnectorSecretsInterface


class ProofpointSecrets(ConnectorSecretsInterface):
    token: SecretStr
