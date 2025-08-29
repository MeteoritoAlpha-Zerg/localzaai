from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class SplunkSecrets(ConnectorSecretsInterface):
    token: SecretStr | None
    delete_token: SecretStr | None
    indexing_token: SecretStr | None
    mtls_client_cert_data: SecretStr | None
    mtls_client_key_data: SecretStr | None
    token_oauth_client_id: SecretStr | None
    token_oauth_client_secret: SecretStr | None
