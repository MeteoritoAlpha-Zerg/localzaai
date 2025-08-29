from connectors.connector import ConnectorTargetInterface


class ServiceNowTarget(ConnectorTargetInterface):
    # List of table names to target
    table_names: list[str] = []

    def get_dataset_paths(self) -> list[list[str]]:
        # Each table is treated as an individual dataset
        return [[table] for table in self.table_names]
