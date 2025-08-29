from connectors.connector import ConnectorTargetInterface


class GithubTarget(ConnectorTargetInterface):
    """
    Target for GitHub Issues connector.

    Holds the repository IDs for the repositories to be queried. Each repository ID is converted to a dataset path.
    """

    repository_ids: list[int] = []

    def get_dataset_paths(self) -> list[list[str]]:
        """
        Returns a list of dataset paths. Each repository ID is returned as a list with its string representation.
        """
        return [[str(repo_id)] for repo_id in self.repository_ids]
