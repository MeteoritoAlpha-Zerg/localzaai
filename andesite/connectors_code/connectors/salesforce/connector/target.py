from pydantic import Field

from connectors.connector import ConnectorTargetInterface

class SalesforceTarget(ConnectorTargetInterface):
    """
    Defines which Salesforce objects the connector tools will operate on.
    """
    objects: list[str] = Field(default_factory=list, description="List of Salesforce objects to target")

    def get_dataset_paths(self) -> list[list[str]]:
        """
        Returns each configured object as a separate dataset path.
        """
        return [[obj] for obj in self.objects]
