from httpx import AsyncClient

from connectors.crowdstrike.connector.config import CrowdstrikeConnectorConfig
from connectors.crowdstrike.connector.secrets import CrowdstrikeSecrets


async def fetch_token(config: CrowdstrikeConnectorConfig, secrets: CrowdstrikeSecrets) -> str:
    """
    Obtain OAuth2 token using client credentials.
    """
    base_url = config.url or f"https://{config.host}"
    timeout = config.api_request_timeout
    async with AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(config.client_id, secrets.client_secret.get_secret_value()),
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise Exception("Failed to obtain access token from CrowdStrike")
        return token
