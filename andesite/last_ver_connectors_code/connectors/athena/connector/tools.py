import time

import boto3
from botocore.exceptions import ClientError
from common.jsonlogging.jsonlogger import Logging
from common.models.metadata import QueryResultMetadata
from common.utils.context import context_llm_model_id
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.athena.connector.config import AthenaConnectorConfig
from connectors.athena.connector.target import AthenaTarget
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.metrics import ConnectorMetrics
from connectors.tools import ConnectorToolsInterface

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AthenaConnectorTools(ConnectorToolsInterface):
    """
    A collection of tools used by agents that query Athena.
    """

    def __init__(
        self,
        athena_config: AthenaConnectorConfig,
        target: AthenaTarget,
        connector_display_name: str,
    ):
        """
        Initialize the Tools with a specified AWS region.

        :param aws_region: The AWS region to use for the Glue client.
        """
        self._aws_region = athena_config.region
        self._catalog = target.catalog
        self._database = target.database
        self._tables = target.tables
        self._s3_out_dir = athena_config.s3_staging_dir
        self._query_timeout = athena_config.query_timeout
        self._target = target
        super().__init__(ConnectorIdEnum.ATHENA, target, connector_display_name)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                name="list_tables",
                connector=self._connector_display_name,
                execute_fn=self.list_tables,
            )
        )
        tools.append(
            Tool(
                name="get_athena_table_description_async",
                connector=self._connector_display_name,
                execute_fn=self.get_athena_table_description_async,
            )
        )
        tools.append(
            Tool(
                name="get_athena_column_descriptions_async",
                connector=self._connector_display_name,
                execute_fn=self.get_athena_column_descriptions_async,
            )
        )
        tools.append(
            Tool(
                name="list_columns",
                connector=self._connector_display_name,
                execute_fn=self.list_columns,
            )
        )
        tools.append(
            Tool(
                name="get_partitions",
                connector=self._connector_display_name,
                execute_fn=self.get_partitions,
            )
        )
        tools.append(
            Tool(
                name="execute_query",
                connector=self._connector_display_name,
                execute_fn=self.execute_query,
            )
        )
        return tools

    class ListTablesInput(BaseModel):
        """
        List all available tables.
        """

        pass

    @tracer.start_as_current_span("list_databases")
    def list_tables(self, input: ListTablesInput) -> list[str]:
        """
        List all available tables.

        :return: A list of table names.
        """
        logger().debug(
            "Listing tables for catalog %s and database %s",
            self._catalog,
            self._database,
        )
        client = boto3.client("athena", region_name=self._aws_region)
        response = client.list_table_metadata(
            CatalogName=self._catalog, DatabaseName=self._database
        )
        tables = [table["Name"] for table in response["TableMetadataList"]]
        logger().debug("Retrieved tables: %s", tables)
        return [
            t for t in self._tables if t in tables
        ] # Intersection with selected tables

    class ListTableDescriptionInput(BaseModel):
        """
        Get a curated description of a table.
        """

        table: str = Field(description="The name of the table.")

    @tracer.start_as_current_span("get_athena_table_description_async")
    async def get_athena_table_description_async(
        self, input: ListTableDescriptionInput
    ) -> str:
        table = input.table
        logger().debug(
            "Fetching Athena table description for %s.%s", self._database, table
        )

        path_to_table = [self._catalog, self._database, table]
        existing_dataset_descriptions = await self._load_dataset_descriptions_async(
            path_prefix=path_to_table
        )

        if len(existing_dataset_descriptions) == 1:
            description = existing_dataset_descriptions[0].description
        elif len(existing_dataset_descriptions) == 0:
            description = f"No description found for table {table}"
        else:
            logger().error(
                f"Multiple descriptions exist for table {table} and path {path_to_table}"
            )
            raise Exception(
                f"Multiple descriptions exist for table {table} and path {path_to_table}, so none can be retrieved."
            )
        logger().debug("Retrieved the following table description: %s", description)
        return description

    class ListColumnDescriptionInput(BaseModel):
        """
        Get a curated descriptions of all columns for a table.
        """

        table: str = Field(description="The name of the table.")

    @tracer.start_as_current_span("get_athena_column_descriptions_async")
    async def get_athena_column_descriptions_async(
        self, input: ListColumnDescriptionInput
    ) -> list[str]:
        """
        Asynchronously get a curated descriptions of all columns for a table.

        :param table: The name of the table.
        :return: The high level descriptions of the columns for a table.
        """

        existing_dataset_descriptions = await self._load_dataset_descriptions_async(
            path_prefix=[self._catalog, self._database, input.table]
        )
        column_descriptions_structured: list[str] = []

        for col in existing_dataset_descriptions:
            column_descriptions_structured.append(
                # A column's name is the last element in the path
                f"Column '{col.path[-1]}' (description '{col.description}')"
            )

        logger().debug(
            "Retrieved the following column descriptions: %s",
            column_descriptions_structured,
        )
        return column_descriptions_structured

    class ListColumnsInput(BaseModel):
        """
        List all columns in a specified table.
        """

        table: str = Field(description="The name of the table.")

    @tracer.start_as_current_span("list_columns")
    def list_columns(self, input: ListColumnsInput) -> str:
        table = input.table
        logger().debug(
            "Listing columns for table %s in database %s", table, self._database
        )
        client = boto3.client("glue", region_name=self._aws_region)
        response = client.get_table(DatabaseName=self._database, Name=table)
        columns = [
            col["Name"] for col in response["Table"]["StorageDescriptor"]["Columns"]
        ]
        logger().debug("Retrieved columns: %s", columns)
        return str(columns)

    class ListPartitionsInput(BaseModel):
        """
        Get partition keys for a specified table.
        """

        table: str = Field(description="The name of the table.")

    @tracer.start_as_current_span("get_partitions")
    def get_partitions(self, input: ListPartitionsInput) -> str:
        """
        Get partition keys for a specified table.

        :param table: The name of the table.
        :return: A list of partition keys.
        """
        table = input.table
        logger().debug(
            "Getting partitions for table %s in database %s", table, self._database
        )
        client = boto3.client("glue", region_name=self._aws_region)
        response = client.get_table(DatabaseName=self._database, Name=table)
        partitions = response["Table"]["PartitionKeys"]
        partition_keys = [partition["Name"] for partition in partitions]
        logger().debug("Retrieved partition keys: %s", partition_keys)
        return str(partition_keys)

    class ExecuteQueryInput(BaseModel):
        """
        Execute a SQL query on Athena and return the results.
        """

        query: str = Field(description="The SQL query to execute.")

    @tracer.start_as_current_span("execute_query")
    def execute_query(self, input: ExecuteQueryInput) -> str | QueryResultMetadata:
        """
        Execute a SQL query on Athena and return the results.

        :param query: The SQL query to execute.
        :return: A dictionary containing the query metadata and results.
        """
        query = input.query
        try:
            logger().debug("Executing query: %s", query)
            client = boto3.client("athena", region_name=self._aws_region)

            try:
                response = client.start_query_execution(
                    QueryString=query,
                    QueryExecutionContext={"Database": self._database},
                    ResultConfiguration={"OutputLocation": self._s3_out_dir},
                )
            except ClientError as e:
                logger().exception("Invalid Request Exception: %s", str(e))
                return f"Query failed: {str(e)}"

            query_execution_id = response["QueryExecutionId"]

            state = "RUNNING"
            timeout = self._query_timeout
            while state in ["RUNNING", "QUEUED"]:
                response = client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                if (
                    "QueryExecution" in response
                    and "Status" in response["QueryExecution"]
                    and "State" in response["QueryExecution"]["Status"]
                ):
                    state = response["QueryExecution"]["Status"]["State"]
                else:
                    state = "RUNNING"

                if state in ["SUCCEEDED", "FAILED"]:
                    break
                elif state in ["RUNNING", "QUEUED"]:
                    timeout -= 1
                    if timeout == 0:
                        raise TimeoutError("Timed out waiting for query to complete")
                    time.sleep(1)

            if state != "SUCCEEDED":
                raise Exception(f"Query failed: {response}")

            result_response = client.get_query_results(
                QueryExecutionId=query_execution_id
            )
            rows = result_response["ResultSet"]["Rows"]
            headers = [col["VarCharValue"] for col in rows[0]["Data"]]

            query_results = [
                [str(col.get("VarCharValue", "")) for col in row["Data"]]
                for row in rows[1:]
            ]

            result = QueryResultMetadata(
                query_format="SQL",
                query=query,
                results=query_results,
                column_headers=headers,
            )

            logger().debug("Retrieved query results: %s", result)
            ConnectorMetrics.connector_queries_counter.add(
                1,
                {
                    "connector": "athena",
                    "success": True,
                    "llm_model_id": context_llm_model_id.get() or "unknown",
                },
            )
            return result
        except Exception as e:
            logger().exception("Exception occurred while querying Athena: %s", str(e))
            ConnectorMetrics.connector_queries_counter.add(
                1,
                {
                    "connector": "athena",
                    "success": False,
                    "exception": str(e),
                    "llm_model_id": context_llm_model_id.get() or "unknown",
                },
            )
            raise e
