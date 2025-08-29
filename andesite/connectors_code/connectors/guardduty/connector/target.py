from connectors.connector import ConnectorTargetInterface
from pydantic import BaseModel

class GuarddutyTarget(ConnectorTargetInterface, BaseModel):
    """
    Query target for GuardDuty specifying detectors
    """

    def get_dataset_paths(self) -> list[list[str]]:
        """
        Returns a list of paths for each detector ID.
        """
        return []
