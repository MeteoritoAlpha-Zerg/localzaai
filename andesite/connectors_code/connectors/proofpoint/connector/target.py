from pydantic import BaseModel

from connectors.connector import ConnectorTargetInterface


class ProofpointTarget(ConnectorTargetInterface, BaseModel):
    """
    ProofpointTarget defines the target for the proofpoint connector
    """

    def get_dataset_paths(self) -> list[list[str]]:
        """
        Returns a list with a single dataset path for Proofpoint threat intelligence data.
        """
        return []
