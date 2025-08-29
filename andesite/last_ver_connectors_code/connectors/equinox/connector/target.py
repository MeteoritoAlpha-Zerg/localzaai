from connectors.connector import ConnectorTargetInterface


class EquinoxTarget(ConnectorTargetInterface):
    project: str = ""

    def get_dataset_paths(self) -> list[list[str]]:
        return [[self.project]]
