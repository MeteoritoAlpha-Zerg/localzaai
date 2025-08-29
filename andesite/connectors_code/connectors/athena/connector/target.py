from typing import List

from connectors.connector import ConnectorTargetInterface


class AthenaTarget(ConnectorTargetInterface):
    catalog: str = ""
    workgroup: str = ""
    database: str = ""
    tables: List[str] = []

    def get_dataset_paths(self) -> List[List[str]]:
        paths = [[self.workgroup]]

        for table in self.tables:
            paths.append([self.catalog, self.database, table])

        return paths
