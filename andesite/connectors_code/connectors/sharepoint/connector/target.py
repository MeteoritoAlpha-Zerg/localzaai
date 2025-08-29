from connectors.connector import ConnectorTargetInterface
from pydantic import Field
from typing import List

class SharePointTarget(ConnectorTargetInterface):
    site_names: List[str] = Field(default_factory=list, description="List of SharePoint site names")

    def get_dataset_paths(self) -> List[List[str]]:
        # For simplicity, each site name represents a unique dataset
        return [[site] for site in self.site_names]
