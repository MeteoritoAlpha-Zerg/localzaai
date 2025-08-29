from typing import List

from connectors.config import ConnectorConfig


class SentinelOneConnectorConfig(ConnectorConfig):
    api_endpoint: str

    displayable_field_names: List[str] = [
        "api_endpoint",
    ]
