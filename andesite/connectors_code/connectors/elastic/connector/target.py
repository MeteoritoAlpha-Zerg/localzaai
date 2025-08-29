from connectors.connector import ConnectorTargetInterface


class ElasticTarget(ConnectorTargetInterface):
    index: str = ""

    def get_dataset_paths(self) -> list[list[str]]:
        return [[self.index]]
