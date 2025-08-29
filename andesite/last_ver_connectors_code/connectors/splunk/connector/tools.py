from typing import Any, Callable, Coroutine

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.connector import ConnectorTargetInterface
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.splunk.connector.target import SplunkTarget
from connectors.splunk.database.splunk_instance import SplunkField
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)


class SplunkConnectorTools(ConnectorToolsInterface):
    """
    A collection of tools used by agents that query Splunk.
    """

    def __init__(
        self,
        target: SplunkTarget,
        get_dataset_structures: Callable[
            [ConnectorTargetInterface | None],
            Coroutine[Any, Any, list[DatasetStructure]],
        ],
        connector_display_name: str,
    ):
        """
        Initializes the tool collection for a specific splunk target.

        :param target: The Splunk indexes the tools will target.
        """
        self.get_dataset_structures = get_dataset_structures
        super().__init__(ConnectorIdEnum.SPLUNK, target=target, connector_display_name=connector_display_name)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="get_splunk_indexes",
                connector=self._connector_display_name,
                execute_fn=self.get_splunk_indexes_async,
            )
        )
        tools.append(
            Tool(
                name="get_splunk_index_fields",
                connector=self._connector_display_name,
                execute_fn=self.get_splunk_index_fields_async,
            )
        )
        return tools

    class GetSplunkIndexesInput(BaseModel):
        """Gets available Splunk indexes. ABSOLUTELY DO NOT PROVIDE ANY INPUTS."""

        pass

    @tracer.start_as_current_span("get_splunk_indexes_async")
    async def get_splunk_indexes_async(
        self, input: GetSplunkIndexesInput
    ) -> list[tuple[str, str]]:
        """
        Asynchronously retrieves a list of Splunk indexes and their fields that the AI model can query. This function is used
        to determine which indexes are available based on the current user context, enabling focused data extraction.
        Use this before querying splunk.
        """

        # For every index in Splunk, we must find the description of the index if it exists and if not define it as "No description available"
        index_descriptions = await self._load_dataset_descriptions_async()
        defaulted_index_descriptions: list[DatasetDescription] = []
        target_indexes = SplunkTarget(**self._target.model_dump()).indexes
        for index in target_indexes:
            found_description = next(
                (x for x in index_descriptions if x.path == [index]),
                None,
            )
            description = "No description available"
            path = [index]
            if found_description:
                description = found_description.description
                path = found_description.path
            defaulted_index_descriptions.append(
                DatasetDescription(
                    connector=self._connector,
                    path=path,
                    description=description,
                )
            )

        llmPrompts: list[tuple[str, str]] = []
        for index_description in defaulted_index_descriptions:
            llmPrompts.append(
                (index_description.path[0], index_description.description)
            )

        return llmPrompts

    class GetSplunkIndexFieldsInput(BaseModel):
        """
        Retrieves field names and example values for a specified Splunk index.
        This information can be helpful to understand the data structure within the index, which assists in crafting accurate and contextually appropriate queries.
        """

        index: str = Field(
            description="The name of the Splunk index for which field information is required."
        )

    @tracer.start_as_current_span("get_splunk_index_fields_async")
    async def get_splunk_index_fields_async(
        self, input: GetSplunkIndexFieldsInput
    ) -> list[str]:
        """
        Asynchronously retrieves field names and example values for a specified Splunk index.
        This information can be helpful to understand the data structure within the index, which assists in crafting
        accurate and contextually appropriate queries.
        Use this before querying splunk.

        :param index: The name of the Splunk index for which field information is required.
        """
        index = input.index
        fields_without_description: list[str] = []
        # NOTE: we maintain two separate lists of fields so we can A) handle the descriptions however we like
        # and B: so both the model and the user see the fields with description first
        fields_with_description: list[str] = []
        dataset_structure = (
            await DatasetStructureManager.instance().get_dataset_structure_async(
                self._connector, index
            )
        )
        dataset_descriptions = await self._load_dataset_descriptions_async(
            path_prefix=[index]
        )

        field_descriptions: dict[str, dict[str, str]] = {}
        field_descriptions[index] = {}
        for dataset_description in dataset_descriptions:
            field_descriptions[index][dataset_description.path[-1]] = (
                dataset_description.description
            )

        if dataset_structure is None:
            # indexing isn't complete but we can still grab it directly from splunk
            logger().debug(
                "Index not found in dataset structure manager, so querying splunk directly for index: %s",
                index,
            )
            dataset_structures = await self.get_dataset_structures(
                SplunkTarget(indexes=[index])
            )
            if len(dataset_structures) != 1:
                raise Exception(
                    f"Index '{index}' not found in dataset structure manager or in the splunk index"
                )
            dataset_structure = dataset_structures[0]
            await DatasetStructureManager.instance().set_dataset_structure_async(
                dataset_structure
            )
        for field in dataset_structure.attributes:
            splunk_field = SplunkField.model_validate(field)
            index_desc = field_descriptions.get(index)
            if index_desc:
                description: str | None = index_desc.get(splunk_field.field_name)
                if description:
                    fields_with_description.append(
                        f"Field '{splunk_field.field_name}' (description '{description}') (example value '{splunk_field.example_value}')"
                    )
                else:
                    fields_without_description.append(
                        f"Field '{splunk_field.field_name}' (example value '{splunk_field.example_value}')"
                    )
            else:
                fields_without_description.append(
                    f"Field '{splunk_field.field_name}' (example value '{splunk_field.example_value}')"
                )
        # NOTE: we maintain two separate lists of fields so we can A) handle the descriptions however we like
        # and B: so both the model and the user see the fields with description first
        return fields_with_description + fields_without_description
