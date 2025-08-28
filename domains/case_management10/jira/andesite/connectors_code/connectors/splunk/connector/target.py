from connectors.connector import ConnectorTargetInterface


class SplunkTarget(ConnectorTargetInterface):
    indexes: list[str] = []

    def get_dataset_paths(self) -> list[list[str]]:
        return [[index] for index in self.indexes]
