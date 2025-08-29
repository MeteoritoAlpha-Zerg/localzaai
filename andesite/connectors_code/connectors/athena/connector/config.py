
from connectors.config import ConnectorConfigurationBase


class AthenaConnectorConfig(ConnectorConfigurationBase):
    region: str = "us-east-2"
    s3_staging_dir: str = "s3://andesite-athena/staging"
    query_timeout: int = 60
