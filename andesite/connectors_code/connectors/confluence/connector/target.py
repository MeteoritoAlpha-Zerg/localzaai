from pydantic import Field

from connectors.connector import ConnectorTargetInterface


class ConfluenceTarget(ConnectorTargetInterface):
    """
    Defines the target for the Confluence connector, allowing the selection of one or more space keys.
    """

    space_keys: list[str] = Field(default_factory=list, description="List of Confluence space keys to target")

    def get_dataset_paths(self) -> list[list[str]]:
        """
        Returns the dataset paths corresponding to each space key.
        """
        return [[key] for key in self.space_keys]
