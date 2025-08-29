from typing import Any, Literal
from common.jsonlogging.jsonlogger import Logging
from common.models.metadata import QueryResultMetadata
from common.models.tool import Tool
from connectors.elastic.connector.client import ElasticClient
from connectors.elastic.connector.config import ElasticConnectorConfig
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.elastic.connector.target import ElasticTarget
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.tools import ConnectorToolsInterface


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

class Query(BaseModel):
    """
    field_name must be a valid field that exists in this index
    """
    field_name: str
    string_to_match: str

class TimeFrame(BaseModel):
    field: str = Field(description="The field we are interested in searching over for this particular time range")
    count: int = Field(gt=0)
    unit: Literal['days'] | Literal['hours']

def _construct_query(queries: list[Query], timeframe: None | TimeFrame) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if len(queries) > 0:
        query = {"query": { "match": {}}}
        for pair in queries:
            query["query"]["match"][pair.field_name] = {"query": pair.string_to_match}

    if timeframe:
        query = {"query": { "range": { timeframe.field: {
            "gte" : f"now-{timeframe.count}{'d' if timeframe.unit == 'days' else 'h'}",
            "lt" :  "now"
        } }}}
    return query

class ElasticConnectorTools(ConnectorToolsInterface):
    """
    A collection of tools used by agents that query Elastic.
    """

    def __init__(
        self,
        elastic_config: ElasticConnectorConfig,
        target: ElasticTarget,
    ):
        """
        Initialize the Tools with a specified AWS configuration
        """
        self._index = target.index
        self._url = elastic_config.url
        self._api_key = elastic_config.api_key
        self._target = target
        super().__init__(ConnectorIdEnum.ELASTIC, target, connector_display_name="Elastic")

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="get_index_description",
                connector="elastic",
                execute_fn=self.get_index_description,
            )
        )
        tools.append(
            Tool(
                name="get_index_fields",
                connector="elastic",
                execute_fn=self.get_index_fields,
            )
        )
        tools.append(
            Tool(
                name="execute_count_query",
                connector="elastic",
                execute_fn=self.execute_count_query,
            )
        )
        tools.append(
            Tool(
                name="execute_match_query",
                connector="elastic",
                execute_fn=self.execute_match_query,
            )
        )
        return tools

    class GetIndexInput(BaseModel):
        """
        Retrieve the description of an ElasticSearch index

        Don't use this tool to directly answer a user's question unless they specifically requested an index description. This tool is solely for receiving additional schema information.
        To answer user questions you should use a query tool to adequately get a sense of the meaning of the data.
        """
        pass

    @tracer.start_as_current_span("get_index_description")
    async def get_index_description(self, input: GetIndexInput) -> str:
        index = self._index
        logger().debug("Fetching ElasticSearch index description for %s", index)
        existing_dataset_descriptions = await self._load_dataset_descriptions_async(
            path_prefix=[index]
        )

        if len(existing_dataset_descriptions) == 1:
            description = existing_dataset_descriptions[0].description
        elif len(existing_dataset_descriptions) == 0:
            description = f"No description found for index {index}"
        else:
            logger().error(f"Multiple descriptions exist for index {index}")
            raise Exception(
                f"Multiple descriptions exist for index {index}, so none can be retrieved."
            )
        logger().debug("Retrieved the following index description: %s", description)
        return description

    class GetIndexFieldsInput(BaseModel):
        """
        Retrieve the field mappings of an ElasticSearch index

        Don't use this tool to directly answer a user's question unless they specifically requested the fields of an index. This tool is solely for receiving additional schema information.
        To answer user questions you should use a query tool to adequately get a sense of the meaning of the data.
        """

        pass

    @tracer.start_as_current_span("get_index_fields")
    async def get_index_fields(self, input: GetIndexFieldsInput) -> dict[str, Any]:
        index = self._index

        return ElasticClient.get_client(
            url=self._url, api_key=self._api_key
        ).list_index_fields(index=index)

    class ExecuteCountQueryInput(BaseModel):
        """
        Query ElasticSearch to answer any user question about cybersecurity using the ElasticSearch count api.

        Use this tool if the user ever want to know how many documents are in the index.
        This tool can also be used to find the count of how many documents adhere to particular queries passed in.

        You should make sure to call `get_index_fields` before calling this tool, and be absolutely certain your fields exist.
        """
        queries: list[Query] = Field(default=[], description="A list of field name and string mappings to be matched in each document to count", examples=[[f"{Query(field_name='my_index_field', string_to_match='string of interest').model_dump()}"]])

        timeframe: TimeFrame | None = Field(description="An optional field to specify the timeframe to search over. This parameter is needed for answering questions that ask for an analysis over some period of time. You MUST be sure the field provided is a valid field to perform an ElasticSearch range query over", examples=[f"{TimeFrame(field='timestamp', count=1, unit='days').model_dump()}", f"{TimeFrame(field='timestamp', count=24, unit='hours').model_dump()}"])

    @tracer.start_as_current_span("execute_match_query")
    def execute_count_query(self, input: ExecuteCountQueryInput) -> QueryResultMetadata:
        index = self._index
        query = _construct_query(input.queries, input.timeframe)

        count = ElasticClient.get_client(
            url=self._url, api_key=self._api_key
        ).count(query=query, index=index)

        return QueryResultMetadata(
            query_format="ES",
            query=str(query),
            results=[[str(count)]],
            column_headers=["count"],
        )

    class ExecuteMatchQueryInput(BaseModel):
        """
        Execute a ElasticSearch query using the ElasticSearch search api to answer any user question about cybersecurity.

        If there are no results from the query, edit the query to try to get results (that are relevant to the user question).
        Sometimes there won't be results and that is an acceptable answer. If you think a different query could possibly give results, try with similar queries to make sure.
        Sometimes you may be using the incorrect field for a filter, you can change based on your exploration, but not as a first resort.

        You should make sure to call `get_index_fields` before calling this tool, and be absolutely certain your fields exist.
        """
        queries: list[Query] = Field(description="A list of field name and string mappings to be matched in this index", examples=[[f"{Query(field_name='my_index_field', string_to_match='string of interest').model_dump()}"]])

        timeframe: TimeFrame | None = Field(description="An optional field to specify the timeframe to search over. This parameter is needed for answering questions that ask for an analysis over some period of time. You MUST be sure the field provided is a valid field to perform an ElasticSearch range query over", examples=[f"{TimeFrame(field='timestamp', count=1, unit='days').model_dump()}", f"{TimeFrame(field='timestamp', count=24, unit='hours').model_dump()}"])

    @tracer.start_as_current_span("execute_match_query")
    def execute_match_query(self, input: ExecuteMatchQueryInput) -> QueryResultMetadata:
        index = self._index
        query = _construct_query(input.queries, input.timeframe)

        hits = ElasticClient.get_client(
            url=self._url, api_key=self._api_key
        ).search(query=query, index=index)
        rows: list[list[str]] = []
        columns: set[str] = set()
        for hit in hits:
            row: list[str] = []
            source = hit.get("_source", {})
            for column in source:
                columns.add(column)
                row.append(str(source[column]))
            rows.append(row)

        return QueryResultMetadata(
            query_format="ES",
            query=str(query),
            results=rows,
            column_headers=list(columns),
        )
