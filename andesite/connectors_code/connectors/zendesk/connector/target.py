from connectors.connector import ConnectorTargetInterface


class ZendeskTarget(ConnectorTargetInterface):
    view_ids: list[str] = []

    def get_dataset_paths(self) -> list[list[str]]:
        return [[view_id] for view_id in self.view_ids]
