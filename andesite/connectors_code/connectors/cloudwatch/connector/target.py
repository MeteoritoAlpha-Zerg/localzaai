from pydantic import Field

from connectors.connector import ConnectorTargetInterface


class CloudWatchTarget(ConnectorTargetInterface):
    """
    Target for AWS CloudWatch Connector specifying which log groups to query.
    """

    log_groups: list[str] = Field(default_factory=list)

    def get_dataset_paths(self) -> list[list[str]]:
        return [[lg] for lg in self.log_groups]
