from abc import abstractmethod
from typing import TypeVar
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace

from connectors.connector import ConnectorTargetInterface, ConnectorSecretsInterface

tracer = trace.get_tracer(__name__)

TSecrets = TypeVar("TSecrets", bound=ConnectorSecretsInterface)

class ConnectorToolsInterface[TSecrets]:
    """
    This is where you define all the tools an agent can use to interact with a connector.
    """
    def __init__(
        self,
        connector: ConnectorIdEnum,
        target: ConnectorTargetInterface,
        secrets: TSecrets
    ):
        """
        Initializes the tool collection for a connector.

        :param connector: The connector the tools will target.
        """
        self._target = target
        self._connector = connector
        self._secrets = secrets

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """
        Retrieves a list of tools that interact with the connector.
        """
        pass
