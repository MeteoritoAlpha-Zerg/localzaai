from pydantic import SecretStr
from connectors.connector import ConnectorSecretsInterface


class GuarddutySecrets(ConnectorSecretsInterface):
    aws_access_key_id: SecretStr
    aws_secret_access_key: SecretStr
    aws_session_token: SecretStr | None = None
