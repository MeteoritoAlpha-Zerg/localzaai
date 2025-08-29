from pydantic import BaseModel
from connectors.connector_id_enum import ConnectorIdEnum
from opentelemetry import trace
from connectors.equinox.connector.target import EquinoxTarget
from connectors.tools import ConnectorToolsInterface

from common.models.tool import Tool

tracer = trace.get_tracer(__name__)


class EquinoxConnectorTools(ConnectorToolsInterface):
    """
    A collection of tools used by agents that query Equinox search API.
    """

    def __init__(self, target: EquinoxTarget, connector_display_name: str):
        """
        Initializes the tool collection for a specific equinox target.

        :param target: The Equinox target the tools will target.
        """
        super().__init__(ConnectorIdEnum.EQUINOX, target=target, connector_display_name=connector_display_name)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="get_most_recent_index",
                connector=self._connector_display_name,
                execute_fn=self.get_most_recent_index,
            )
        )
        return tools

    class GetMostRecentIndexInput(BaseModel):
        """
        Retrieves the date string corresponding to the most recent search index.. This function is used to determine which index date should be used
        when querying the Equinox Search API when the user does not specify a specific index date.
        """

        pass

    @tracer.start_as_current_span("get_most_recent_index")
    def get_most_recent_index(self, input: GetMostRecentIndexInput) -> str:
        # Hard coded to the only available host similarity search index
        return "2024-07-10"
