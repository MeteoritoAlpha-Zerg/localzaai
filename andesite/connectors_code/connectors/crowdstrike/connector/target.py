from connectors.connector import ConnectorTargetInterface


class CrowdstrikeTarget(ConnectorTargetInterface):
    def get_dataset_paths(self) -> list[list[str]]:
        return []
