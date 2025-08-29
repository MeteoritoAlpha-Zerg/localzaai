from connectors.connector import ConnectorTargetInterface


class SentinelOneTarget(ConnectorTargetInterface):
    def get_dataset_paths(self) -> list[list[str]]:
        return []
