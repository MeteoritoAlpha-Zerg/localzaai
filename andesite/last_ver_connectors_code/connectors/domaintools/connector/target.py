from connectors.connector import ConnectorTargetInterface


class DomainToolsTarget(ConnectorTargetInterface):
    def get_dataset_paths(self) -> list[list[str]]:
        return []
