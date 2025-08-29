import json
from typing import Any

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import DatasetDescriptionManager
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.metadata import QueryResultMetadata
from common.models.tool import ExecuteQuerySpecialization, Tool
from opentelemetry import trace
from pydantic import BaseModel, Field, model_validator

from connectors.elastic.connector.client import ElasticClient
from connectors.elastic.connector.config import ElasticConnectorConfig
from connectors.elastic.connector.target import ElasticTarget
from connectors.elastic.connector.secrets import ElasticSecrets
from connectors.tools import ConnectorToolsInterface

ELASTIC_QUERY_PROMPT = """
Craft a performant and precise Elasticsearch query by using a bool query to combine must, filter, and optional must_not or should clauses.
Prioritize filter for structured data and exact matches, such as terms or ranges, since it's cached and faster.
Use match for full-text search on analyzed fields, and prefer term or keyword fields for exact values.
Avoid leading wildcards and unnecessary complexity.
Always define a clear sort order and limit results with size for efficiency.
Ensure field types align with query expectations by validating the index mapping beforehand.
"""

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class ElasticCountQuery(BaseModel):
    """
    Runs an Elasticsearch query that you specify and counts the matching records.
    The `query` field should contain only the body of the Elasticsearch query — the content
    that goes under the 'query' key in the Elasticsearch API. Do not wrap it inside another 'query' object.
    """

    query: dict[str, Any] = Field(
        description=(
            "The body of the Elasticsearch query — this is what goes under the 'query' key. "
            "For example: {'bool': {'must': [...], 'filter': [...]}}. "
            "Do not wrap it with another 'query' key."
        )
    )

    @model_validator(mode="before")
    def normalize_query(cls, values):
        logger().debug("Validating Elasticsearch count query: values=%s", values)
        if not isinstance(values, dict):
            raise ValueError("Input must be a dictionary.")
        if "query" in values and isinstance(values["query"], dict) and "query" in values["query"]:
            values["query"] = values["query"]["query"]
        if "query" not in values:
            raise ValueError("Missing required 'query' field.")
        return values


class ElasticSearchQuery(BaseModel):
    """
    Runs an Elasticsearch query that you specify and retrieves the matching records.
    The `query` field should contain only the body of the Elasticsearch query — i.e.,
    the content that goes under the 'query' key in the Elasticsearch API. You do not need
    to wrap it in another 'query' object.
    """

    query: dict[str, Any] = Field(
        description=(
            "The body of the Elasticsearch query — this is what goes under the 'query' key. "
            "For example: {'bool': {'must': [...], 'should': [...], 'filter': [...]}}. "
            "Do not wrap it with another 'query' key."
        )
    )

    @model_validator(mode="before")
    def normalize_query(cls, values):
        logger().debug("Validating Elasticsearch search query: values=%s", values)
        if not isinstance(values, dict):
            raise ValueError("Input must be a dictionary.")
        if "query" in values and isinstance(values["query"], dict) and "query" in values["query"]:
            values["query"] = values["query"]["query"]
        if "query" not in values:
            raise ValueError("Missing required 'query' field.")
        return values


class ElasticAggregationQuery(BaseModel):
    """
    Runs an Elasticsearch aggregation query.
    The `query` field (optional) contains the filter conditions. The `aggs` field contains
    the aggregation definitions. Do not wrap either field in another 'query' or 'aggs' key.
    """

    query: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "The body of the Elasticsearch query used to filter documents before aggregation. "
            "This is what goes under the 'query' key in the ES request. "
            "Example: {'range': {'timestamp': {'gte': 'now-7d/d', 'lte': 'now'}}}. "
            "Leave empty for aggregations over all documents."
        )
    )
    aggs: dict[str, Any] = Field(
        description=(
            "The aggregations to perform. This is what goes under the 'aggs' key in Elasticsearch. "
            "Set `size=0` in the actual ES query to suppress hits and return only aggregation results."
        )
    )

    @model_validator(mode="before")
    def normalize_query(cls, values):
        logger().debug("Validating Elasticsearch aggregation query: values=%s", values)
        if not isinstance(values, dict):
            raise ValueError("Input must be a dictionary.")
        if "query" in values and isinstance(values["query"], dict) and "query" in values["query"]:
            values["query"] = values["query"]["query"]
        if "aggs" not in values:
            raise ValueError("Missing required 'aggs' field.")
        return values


class ElasticConnectorTools(ConnectorToolsInterface[ElasticSecrets]):
    """
    A collection of tools used by agents that query Elastic.
    """

    def __init__(
        self,
        elastic_config: ElasticConnectorConfig,
        target: ElasticTarget,
        secrets: ElasticSecrets,
    ):
        """
        Initialize the Tools with a specified AWS configuration
        """
        self._index = target.index
        self._url = elastic_config.url
        self._target = target
        super().__init__(ConnectorIdEnum.ELASTIC, target, secrets)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="get_index_description",
                connector=ConnectorIdEnum.ELASTIC,
                execute_fn=self.get_index_description,
            )
        )
        tools.append(
            Tool(
                name="get_index_fields",
                connector=ConnectorIdEnum.ELASTIC,
                execute_fn=self.get_index_fields,
            )
        )
        tools.append(
            Tool(
                name="execute_count_query",
                connector=ConnectorIdEnum.ELASTIC,
                execute_fn=self.execute_count_query,
                specialization=ExecuteQuerySpecialization(
                    query_prompt=ELASTIC_QUERY_PROMPT,
                    dataset_paths=self._target.get_dataset_paths(),
                    get_schema=self._get_schema,
                ),
            )
        )
        tools.append(
            Tool(
                name="execute_aggregation_query",
                connector="elastic",
                execute_fn=self.execute_aggregation_query,
                specialization=ExecuteQuerySpecialization(
                    query_prompt=ELASTIC_QUERY_PROMPT,
                    dataset_paths=self._target.get_dataset_paths(),
                    get_schema=self._get_schema,
                ),
            )
        )
        tools.append(
            Tool(
                name="execute_search_query",
                connector="elastic",
                execute_fn=self.execute_search_query,
                specialization=ExecuteQuerySpecialization(
                    query_prompt=ELASTIC_QUERY_PROMPT,
                    dataset_paths=self._target.get_dataset_paths(),
                    get_schema=self._get_schema,
                ),
            )
        )
        return tools

    class GetIndexInput(BaseModel):
        """
        Retrieve the description of an ElasticSearch index

        Don't use this tool to directly answer a user's question unless they specifically requested the fields of an index.
        This tool is solely for receiving additional schema information such as identify the exact field name and data types prior to constructing a query.
        To answer user questions you should use a query tool to adequately get a sense of the meaning of the data.
        """

        pass

    @tracer.start_as_current_span("get_index_description")
    async def get_index_description(self, input: GetIndexInput) -> str:
        index = self._index
        logger().debug("Fetching ElasticSearch index description for %s", index)
        existing_dataset_descriptions = await DatasetDescriptionManager.instance().get_dataset_descriptions_async(
            self._connector, path_prefix=[index]
        )
        if len(existing_dataset_descriptions) == 1:
            description = existing_dataset_descriptions[0].description
        elif len(existing_dataset_descriptions) == 0:
            description = f"No description found for index {index}"
        else:
            logger().error(f"Multiple descriptions exist for index {index}")
            raise Exception(f"Multiple descriptions exist for index {index}, so none can be retrieved.")
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

        return await ElasticClient.get_client(url=self._url, api_key=self._secrets.api_key).list_index_fields(index=index)

    @tracer.start_as_current_span("execute_count_query")
    async def execute_count_query(self, input: ElasticCountQuery) -> QueryResultMetadata:
        index = self._index
        logger().debug(f"Executing count query with arguments: {input.model_dump()}")

        query = {"query": input.query}
        count = await ElasticClient.get_client(url=self._url, api_key=self._secrets.api_key).count(
            query=query, index=index
        )

        return QueryResultMetadata(
            query_format="ES",
            query=json.dumps(query),
            results=[[str(count)]],
            column_headers=["count"],
        )

    @tracer.start_as_current_span("execute_search_query")
    async def execute_search_query(self, input: ElasticSearchQuery) -> QueryResultMetadata:
        index = self._index
        logger().debug(f"Executing search query with arguments: {input.model_dump()}")

        query = {"query": input.query}
        hits = await ElasticClient.get_client(url=self._url, api_key=self._secrets.api_key).search(
            query=query, index=index
        )
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
            query=json.dumps(query),
            results=rows,
            column_headers=list(columns),
        )

    @tracer.start_as_current_span("execute_aggregation_query")
    async def execute_aggregation_query(self, input: ElasticAggregationQuery) -> QueryResultMetadata:
        index = self._index
        logger().debug(f"Executing aggregation query with arguments: {input.model_dump()}")

        query = {"query": input.query, "aggs": input.aggs}
        agg_results = await ElasticClient.get_client(url=self._url, api_key=self._secrets.api_key).agg_search(
            query=query, index=index
        )

        rows: list[list[str]] = []
        for agg_name, agg_result in agg_results.items():
            rows.append([agg_name, json.dumps(agg_result)])

        return QueryResultMetadata(
            query_format="ES",
            query=json.dumps(query),
            results=rows,
            column_headers=["aggregation_name", "aggregation_result"],
        )

    async def _get_schema(self) -> str:
        index_description = await self.get_index_description(self.GetIndexInput())
        mappings = await self.get_index_fields(self.GetIndexFieldsInput())
        return json.dumps({"description": index_description, "fields": mappings})
