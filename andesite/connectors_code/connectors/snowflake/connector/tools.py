import asyncio
from typing import Any, cast

import snowflake.connector
from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.metadata import QueryResultMetadata
from common.models.tool import Tool, ToolResult
from opentelemetry import trace
from pydantic import BaseModel, Field
from snowflake.connector import ProgrammingError

from connectors.snowflake.connector.config import SnowflakeConnectorConfig
from connectors.snowflake.connector.target import SnowflakeTarget
from connectors.snowflake.connector.secrets import SnowflakeSecrets
from connectors.tools import ConnectorToolsInterface

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class ListSnowflakeDatabasesInput(BaseModel):
    """Input model for listing Snowflake databases. No fields required."""

    class Config:
        extra = "ignore"


class GetSnowflakeTablesInput(BaseModel):
    """Input model for listing tables in a selected Snowflake database."""

    database: str = Field(..., description="Name of the Snowflake database")


class SnowflakeExecuteQueryInput(BaseModel):
    """Input model for executing a SQL query in Snowflake."""

    query: str = Field(..., description="SQL query to execute")
    limit: int = Field(default=100, description="Maximum number of rows to return from the query")


class SnowflakeConnectorTools(ConnectorToolsInterface[SnowflakeSecrets]):
    """A collection of tools used by agents to interact with Snowflake."""

    def __init__(self, config: SnowflakeConnectorConfig, target: SnowflakeTarget, secrets: SnowflakeSecrets):
        super().__init__(ConnectorIdEnum.SNOWFLAKE, target, secrets)
        self.config = config

    def get_tools(self) -> list[Tool]:
        return [
            Tool(connector=ConnectorIdEnum.SNOWFLAKE, name="list_snowflake_databases", execute_fn=self.list_snowflake_databases_async),
            Tool(connector=ConnectorIdEnum.SNOWFLAKE, name="list_snowflake_tables", execute_fn=self.list_snowflake_tables_async),
            Tool(  # TODO: See how this works as normal tool first. QueryTool may not be necessary.
                connector=ConnectorIdEnum.SNOWFLAKE, name="execute_snowflake_query", execute_fn=self.execute_query_async
            ),
        ]

    @tracer.start_as_current_span("list_snowflake_databases_async")
    async def list_snowflake_databases_async(self, input: ListSnowflakeDatabasesInput) -> ToolResult:
        """Lists all databases available in Snowflake."""
        max_retries = self.config.api_max_retries
        attempt = 0
        while True:
            try:
                conn = snowflake.connector.connect(
                    account=self.config.account_id,
                    user=self.config.user,
                    password=self._secrets.password.get_secret_value(),
                    timeout=self.config.api_request_timeout,
                    client_session_keep_alive=True,
                )
                cs = conn.cursor()
                cs.execute("SHOW DATABASES")
                rows = cs.fetchall()
                cs.close()
                conn.close()
                databases: list[Any] = []
                for row in rows:
                    db = {
                        "name": row[1],
                        "created_on": str(row[0]),
                        "owner": row[4],
                        "comment": row[3],
                        "is_current": row[2],
                        "origin": row[5] if len(row) > 5 else "",
                    }
                    if db["name"] in self._target.databases:  # type: ignore[attr-defined]
                        databases.append(db)
                return ToolResult(result=databases)
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
                    attempt += 1
                else:
                    raise e

    @tracer.start_as_current_span("list_snowflake_tables_async")
    async def list_snowflake_tables_async(self, input: GetSnowflakeTablesInput) -> ToolResult:
        """Lists all tables in the specified Snowflake database."""
        max_retries = self.config.api_max_retries
        attempt = 0
        while True:
            try:
                conn = snowflake.connector.connect(
                    account=self.config.account_id,
                    user=self.config.user,
                    password=self._secrets.password.get_secret_value(),
                    timeout=self.config.api_request_timeout,
                    client_session_keep_alive=True,
                )
                cs = conn.cursor()
                cs.execute(f"USE DATABASE {input.database}")
                cs.execute("SHOW TABLES")
                rows = cs.fetchall()
                tables: list[Any] = []
                for row in rows:
                    table = {
                        "name": row[1],
                        "database": row[2],
                        "schema": row[3],
                        "created_on": str(row[0]),
                        "owner": row[9] if len(row) > 9 else "",
                        "comment": row[5],
                        "table_type": row[4],
                        "bytes": row[8] if len(row) > 8 else None,
                        "row_count": row[7] if len(row) > 7 else None,
                        "retention_time": None,
                    }
                    if table["database"] in self._target.databases:  # type: ignore[attr-defined]
                        tables.append(table)
                cs.close()
                conn.close()
                return ToolResult(result=tables)
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
                    attempt += 1
                else:
                    raise e

    @tracer.start_as_current_span("execute_query_async")
    async def execute_query_async(self, input: SnowflakeExecuteQueryInput) -> QueryResultMetadata:
        """Execute a snowflake query and return the results."""
        max_retries = self.config.api_max_retries
        attempt = 0
        while True:
            try:
                conn = snowflake.connector.connect(
                    account=self.config.account_id,
                    user=self.config.user,
                    password=self._secrets.password.get_secret_value(),
                    timeout=self.config.api_request_timeout,
                    client_session_keep_alive=True,
                )
                cs = conn.cursor()

                try:
                    cs.execute_async(input.query)
                    logger().debug(f"Executing Snowflake query: {input.query}")
                    query_id = cast(str, cs.sfqid)
                    if not query_id:
                        raise ValueError("Snowflake query ID is null. Query execution failed.")
                    while conn.is_still_running(conn.get_query_status_throw_if_error(query_id)):
                        await asyncio.sleep(0.2)
                except ProgrammingError:
                    logger().exception("Snowflake connector encountered an error while executing query.")

                try:
                    cs.get_results_from_sfqid(query_id)
                    results = cs.fetchmany(input.limit)
                    logger().debug(f"Fetched {len(results)} rows from Snowflake query")
                    column_headers = [col.name for col in cs.description]
                except ProgrammingError:
                    logger().exception("Snowflake connector encountered an error while fetching results.")
                    results = []
                    column_headers = []

                cs.close()
                conn.close()
                return QueryResultMetadata(
                    query_format="Snowflake",
                    query=str(input.query),
                    results=[[str(value) for value in row] for row in results],
                    column_headers=column_headers,
                )
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
                    attempt += 1
                else:
                    raise e
