from typing import List

from connectors.config import ConnectorConfig


class AthenaConnectorConfig(ConnectorConfig):
    region: str = "us-east-2"
    s3_staging_dir: str = "s3://andesite-athena/staging"
    query_timeout: int = 60
    displayable_field_names: List[str] = ["region"]
