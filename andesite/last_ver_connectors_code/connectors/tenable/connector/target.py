from connectors.connector import ConnectorTargetInterface


class TenableTarget(ConnectorTargetInterface):
    def get_dataset_paths(self) -> list[list[str]]:
        return []
