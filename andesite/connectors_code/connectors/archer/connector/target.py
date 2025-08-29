from connectors.connector import ConnectorTargetInterface


class ArcherTarget(ConnectorTargetInterface):

    def get_dataset_paths(self) -> list[list[str]]:
        return [[]]
