from connectors.connector import ConnectorTargetInterface


class JIRATarget(ConnectorTargetInterface):
    # List of project keys to target
    project_keys: list[str] = []

    def get_dataset_paths(self) -> list[list[str]]:
        # Each project key represents a dataset path
        return [[key] for key in self.project_keys]
