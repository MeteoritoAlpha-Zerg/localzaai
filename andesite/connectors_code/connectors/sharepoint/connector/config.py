from pydantic import Field
from common.models.secret import StorableSecret
from connectors.config import ConnectorConfigurationBase

class SharePointConnectorConfig(ConnectorConfigurationBase):  # pragma: no cover
    url: str = Field(..., description="SharePoint site URL, e.g. https://yourcompany.sharepoint.com")
    client_id: str = Field(..., description="Azure AD Application (client) ID")
    client_secret: StorableSecret = Field(..., description="Azure AD Application client secret")
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    api_version: str = Field("v1.0", description="Microsoft Graph API version to be used")
    request_timeout: int = Field(30, description="API request timeout in seconds")
    api_max_retries: int = Field(3, description="Max retries for API calls")
