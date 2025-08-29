from abc import abstractmethod
import asyncio
from connectors.connector import ConnectorTargetInterface
from connectors.connector_id_enum import ConnectorIdEnum
from opentelemetry import trace
from typing import Optional

from common.models.tool import Tool


from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)

tracer = trace.get_tracer(__name__)


class ConnectorToolsInterface:
    """
    This is where you define all the tools an agent can use to interact with a connector.
    """

    @tracer.start_as_current_span("_load_dataset_descriptions_async")
    async def _load_dataset_descriptions_async(
        self,
        path_prefix: Optional[list[str]] = [],
    ) -> list[DatasetDescription]:
        return (
            await DatasetDescriptionManager.instance().get_dataset_descriptions_async(
                self._connector, path_prefix=path_prefix
            )
        )

    def __init__(
        self,
        connector: ConnectorIdEnum,
        target: ConnectorTargetInterface,
        connector_display_name: str,
    ):
        """
        Initializes the tool collection for a connector.

        :param connector: The connector the tools will target.
        """
        self._target = target
        self._connector = connector
        self._connector_display_name = connector_display_name

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """
        Retrieves a list of tools that interact with the connector.
        """
        pass

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
