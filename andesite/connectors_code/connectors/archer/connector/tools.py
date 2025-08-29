from typing import Any
from connectors.archer.connector.target import ArcherTarget

from common.models.connector_id_enum import ConnectorIdEnum
from connectors.archer.connector.secrets import ArcherSecrets
from connectors.tools import ConnectorToolsInterface
from common.models.tool import Tool



class ArcherConnectorTools(ConnectorToolsInterface[ArcherSecrets]):
    """A collection of tools for interacting with the Archer API."""

    def __init__(self, config: Any, target: ArcherTarget, secrets: ArcherSecrets):
        """Initializes the Archer connector tools with the given configuration and target.

        :param config: The Archer connector configuration containing url, api_key, and email.
        :param target: The target containing specific project keys (if any).
        """
        self.config = config
        self.target = target
        super().__init__(ConnectorIdEnum.ARCHER, target, secrets)

    # TODO: get_projects
    # TODO: get_issues

    def get_tools(self) -> list[Tool]:
        """Returns a list of Tool objects for Archer operations.

        The returned tools include the ability to list projects and retrieve issues for a project.
        :return: A list of Tool instances.
        """
        tools: list[Tool] = []

        return tools
