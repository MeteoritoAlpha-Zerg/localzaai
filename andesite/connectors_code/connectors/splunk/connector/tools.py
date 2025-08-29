import json
import re
from typing import Any, Callable, Coroutine

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import DatasetDescriptionManager
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.metadata import QueryResultMetadata
from common.models.tool import ExecuteQuerySpecialization, Tool
from dateutil import parser as date_parser
from opentelemetry import trace
from pydantic import BaseModel, Field, field_validator

from connectors.connector import ConnectorTargetInterface
from connectors.splunk.connector.config import SplunkConnectorConfig
from connectors.splunk.connector.target import SplunkTarget
from connectors.splunk.connector.secrets import SplunkSecrets
from connectors.splunk.database.splunk_instance import SplunkField, SplunkInstance
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)


SPL_QUERY_PROMPT = """
You are a cybersecurity expert with a deep understanding of context and data relevance.

You will be provided indexes and fields with descriptions available to you. Generate an SPL query to answer the user question.

Do not use any fields that are not listed.
Important: if a field is used in an aggregation, e.g. stats count, and it has no values for the filter, the results will be empty.
So remove fields from aggregates if not essential to answering the question.
Sometimes you may be using the incorrect field for a filter, you can change based on your exploration, but not as a first resort.
Sometimes there will be multiple fields that could contain the same data, in which case you can filter on them all with an OR statement.
Note: remember that if you're limiting the rows, especially without a filter or aggregate, you're seeing only a small portion of the data.
In general, try your best not to write a query that just returns N rows with all fields. Favor aggregations so that most of the relevant data is captured.

Guidelines for Generating SPL Queries:
1. Exclude any time-related fields, commands, or filters from the SPL, focusing solely on non-temporal data aspects. This includes avoiding fields like 'date_month', 'date_year', and commands like 'earliest' or 'latest'.
2. Explicitly specify one or more indexes in the SPL query. DO NOT DO THIS: index=*
3. Enclose all string values within double quotation marks.
4. Pay close attention to the time range the user asks for.
"""


class SplunkConnectorTools(ConnectorToolsInterface[SplunkSecrets]):
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
        query_instance: SplunkInstance,
        secrets: SplunkSecrets,
        config: SplunkConnectorConfig
    ):
        """
        Initializes the tool collection for a specific splunk target.

        :param target: The Splunk indexes the tools will target.
        """
        self.get_dataset_structures = get_dataset_structures
        self.query_instance = query_instance
        self.query_timeout_seconds = config.query_timeout_seconds
        super().__init__(ConnectorIdEnum.SPLUNK, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                connector=ConnectorIdEnum.SPLUNK,
                name="get_splunk_indexes",
                execute_fn=self.get_splunk_indexes_async,
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.SPLUNK,
                name="get_splunk_index_fields",
                execute_fn=self.get_splunk_index_fields_async,
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.SPLUNK,
                name="execute_splunk_query",
                execute_fn=self._execute_splunk_query,
                specialization=ExecuteQuerySpecialization(
                    query_prompt=SPL_QUERY_PROMPT,
                    dataset_paths=self._target.get_dataset_paths(),
                    get_schema=self._get_splunk_schema,
                ),
                timeout_seconds=self.query_timeout_seconds,
            )
        )
        return tools

    class GetSplunkIndexesInput(BaseModel):
        """Gets available Splunk indexes. ABSOLUTELY DO NOT PROVIDE ANY INPUTS."""

        pass

    @tracer.start_as_current_span("get_splunk_indexes_async")
    async def get_splunk_indexes_async(self, input: GetSplunkIndexesInput) -> list[tuple[str, str]]:
        """
        Asynchronously retrieves a list of Splunk indexes and their fields that the AI model can query. This function is used
        to determine which indexes are available based on the current user context, enabling focused data extraction.
        Use this before querying splunk.
        """

        # For every index in Splunk, we must find the description of the index if it exists and if not define it as "No description available"
        index_descriptions = await DatasetDescriptionManager.instance().get_dataset_descriptions_async(
            self._connector, path_prefix=[]
        )
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
            llmPrompts.append((index_description.path[0], index_description.description))

        return llmPrompts

    class GetSplunkIndexFieldsInput(BaseModel):
        """
        Retrieves field names and example values for a specified Splunk index.
        This information can be helpful to understand the data structure within the index, which assists in crafting accurate and contextually appropriate queries.
        """

        index: str = Field(description="The name of the Splunk index for which field information is required.")

    @tracer.start_as_current_span("get_splunk_index_fields_async")
    async def get_splunk_index_fields_async(self, input: GetSplunkIndexFieldsInput) -> list[str]:
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
        dataset_structure = await DatasetStructureManager.instance().get_dataset_structure_async(self._connector, index)
        dataset_descriptions = await DatasetDescriptionManager.instance().get_dataset_descriptions_async(
            self._connector, path_prefix=[index]
        )

        field_descriptions: dict[str, dict[str, str]] = {}
        field_descriptions[index] = {}
        for dataset_description in dataset_descriptions:
            field_descriptions[index][dataset_description.path[-1]] = dataset_description.description

        if dataset_structure is None:
            # indexing isn't complete but we can still grab it directly from splunk
            logger().debug(
                "Index not found in dataset structure manager, so querying splunk directly for index: %s",
                index,
            )
            dataset_structures = await self.get_dataset_structures(SplunkTarget(indexes=[index]))
            if len(dataset_structures) != 1:
                raise Exception(f"Index '{index}' not found in dataset structure manager or in the splunk index")
            dataset_structure = dataset_structures[0]
            await DatasetStructureManager.instance().set_dataset_structure_async(dataset_structure)
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

    class ExecuteSplunkQueryInput(BaseModel):
        """
        Executes Splunk queries with configurable parameters, such as earliest, latest, and limit.

        The query must be a valid query with proper Search Processing Language (SPL)\
        syntax. The 'earliest' and 'latest' params could be used to customize the time ranges,\
        while the 'limit' param limits the amount of results. The time ranges could be in \
        relative or absolute time formats like '-5d' or '2025-04-14T00:00:00', respectively. The tool \
        will return the results from the query executed in the splunk database. It should \
        be used when the user asks about something that can benefit from extra information found \
        in the splunk database, such as "how many failed login attempts in the past 24 hours?" \
        It will not provide any information outside of what is found inside the splunk database.\
        """

        query: str = Field(
            description="The Splunk query to execute (SPL syntax) and nothing else. Not even punctuation."
        )
        earliest: str | None = Field(
            description="The beginning of the time window to query (relative or absolute), defaults to '-24h'. If absolute time is required, use the ISO time format YYYY-MM-DD for year-month-day, (e.g. 2022-11-15) and YYY-MM-DDTHH:MM:SS for year-month-dayThour:minutes:seconds (e.g. 2022-11-15T20:00:00).",
            default="-24h",
            examples=["-24h", "-5d@w1", "2025-03-01", "2024-01-01T20:00:00"],
        )
        latest: str | None = Field(
            description="The end of the time window to query (relative or absolute), defaults to 'now'.If absolute time is required, use the ISO time format YYYY-MM-DD for year-month-day (e.g. 2022-11-15) and YYYY-MM-DDTHH:MM:SS for year-month-dayThour:minutes:seconds (e.g. 2022-11-15T20:00:00),",
            default="now",
            examples=["-1h", "@w6", "2025-03-01", "2025-01-01T:00:00:00"],
        )
        limit: int | None = Field(description="Max records to return, defaults to 100.", default=100)

        @field_validator("limit", mode="before")
        def limit_validator(cls, value: Any) -> int:
            if not isinstance(value, int):
                try:
                    return int(value)
                except Exception:
                    return 100
            return value

        @field_validator("earliest", mode="before")
        def earliest_none_validator(cls, value: Any):
            if value is None:
                return "-24h"
            return value

        @field_validator("latest", mode="before")
        def latest_none_validator(cls, value: Any):
            if value is None:
                return "now"
            return value

        @field_validator("earliest", "latest", mode="after")
        def time_format_validator(cls, value: Any) -> str:
            value_str = str(value)

            relative_time_markers = ["-", "+", "@", "now", "1"]
            if any(marker in value_str for marker in relative_time_markers) and len(value_str) < 6:
                return value_str

            if (value_str.startswith("-") or value_str.startswith("+")) and len(value_str) >= 6:
                raise ValueError(
                    f"Invalid relative time format: '{value_str}'. Use the shortest timeframe possible, such as '-1y' instead of '-365d'."
                )

            iso_date_pattern = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$"
            if re.match(iso_date_pattern, value_str):
                if len(value_str) == 10:
                    return f"{value_str}T00:00:00"
                return value_str

            try:
                # handle various date formats
                parsed_date = date_parser.parse(value_str)

                # Convert to Splunk's required format (ISO)
                transformed_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")

            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Could not parse date '{value_str}'. Use relative time (e.g., '-24h', '+1d') or absolute time in format YYYY-MM-DDT:HH:MM:SS (e.g., '2022-11-15T20:00:00')"
                ) from exc

            else:
                return transformed_date

    async def _execute_splunk_query(
        self,
        input: ExecuteSplunkQueryInput,
    ) -> QueryResultMetadata:
        """Retrieve the results of a Splunk query"""
        query = input.query
        earliest = input.earliest
        latest = input.latest
        limit = input.limit

        results = await self.query_instance.execute_query(query, earliest, latest, limit=limit)
        columns, rows = self.query_instance.result_to_sparse_table(results)

        # defaults come from splunk_instance.query implementation
        query = input.query
        if not re.search(r"\|\s*(head|limit)\s+\d+\s*$", query):
            query = f"{query} | head {limit or 100}"
        if latest:
            query = f"latest={latest} {query}"
        if earliest:
            query = f"earliest={earliest} {query}"

        metadata = QueryResultMetadata(
            query_format="SPL",
            query=query,
            results=rows,
            column_headers=columns,
        )

        return metadata

    async def _get_splunk_schema(self) -> str:
        indexes_and_descriptions_tool_response = await self.get_splunk_indexes_async(self.GetSplunkIndexesInput())
        indexes_and_descriptions: list[tuple[str, str]] = indexes_and_descriptions_tool_response

        splunk_schema_dict: dict[str, Any] = {}
        for index, description in indexes_and_descriptions:
            fields_with_descriptions_tool_response = await self.get_splunk_index_fields_async(
                self.GetSplunkIndexFieldsInput(index=index)
            )
            splunk_schema_dict[index] = {"description": description, "fields": fields_with_descriptions_tool_response}
        return json.dumps(splunk_schema_dict)
