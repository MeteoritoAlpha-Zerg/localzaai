from typing import List

from connectors.config import ConnectorConfig


class EquinoxConnectorConfig(ConnectorConfig):
    protocol: str = "http"
    host: str
    port: int
    displayable_field_names: List[str] = ["protocol", "host", "port"]
