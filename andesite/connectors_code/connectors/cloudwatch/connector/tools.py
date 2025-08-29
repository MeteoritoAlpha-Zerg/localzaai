import asyncio
from datetime import datetime, timezone
from itertools import chain
import json
from typing import Any, Dict, List, Literal

from botocore.config import Config as BotoConfig
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.metadata import QueryResultMetadata
from common.models.tool import Tool
from pydantic import BaseModel, Field, field_validator

from connectors.cloudwatch.connector.config import CloudWatchConnectorConfig
from connectors.cloudwatch.connector.target import CloudWatchTarget
from connectors.cloudwatch.connector.secrets import CloudWatchSecrets
from connectors.tools import ConnectorToolsInterface
from connectors.cloudwatch.connector.aws import get_client_context
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)



class QueryCloudWatchMetricsInput(BaseModel):
    """Input model for querying CloudWatch metric statistics."""

    namespace: str = Field(..., description="The metric namespace to query")
    metric_name: str = Field(..., description="The name of the metric to query")
    dimensions: Dict[str, str] = Field(
        default_factory=dict, description="Key-value map of dimensions to filter the metric"
    )
    start_time: float = Field(..., description="Start time in seconds since epoch")
    end_time: float = Field(..., description="End time in seconds since epoch")
    period: int = Field(..., description="Granularity, in seconds, of the returned data points")
    statistics: List[str] = Field(..., description="List of statistics to retrieve (e.g., Average, Sum)")


class GetCloudWatchLogsInputBase(BaseModel):
    """Gets log events over a specified duration."""
    start_time: str = Field(
        ...,
        description="Start time in ISO-8601 format (e.g., '2023-04-15T10:30:00Z' or '2023-04-15T10:30:00+00:00')"
    )
    end_time: str = Field(
        ...,
        description="End time in ISO-8601 format (e.g., '2023-04-15T11:30:00Z' or '2023-04-15T11:30:00+00:00')"
    )
    limit: int = Field(default=100, description="Maximum number of log events to return")

    @field_validator("start_time", "end_time")
    def validate_iso_format(cls, v):
        try:
            # Try to parse using built-in fromisoformat
            # First handle 'Z' notation by replacing with +00:00
            if v.endswith('Z'):
                v = v[:-1] + '+00:00'
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO-8601 datetime format: {v}. Use format like '2023-04-15T10:30:00Z' or '2023-04-15T10:30:00+00:00'")

    @property
    def start_timestamp(self) -> int:
        """Convert end_time to a timestamp past epoch in milliseconds."""
        # Handle 'Z' notation by replacing with +00:00
        iso_time = self.start_time
        if iso_time.endswith('Z'):
            iso_time = iso_time[:-1] + '+00:00'

        dt = datetime.fromisoformat(iso_time)

        # Ensure the datetime is timezone-aware (UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    @property
    def end_timestamp(self) -> int:
        """Convert end_time to a timestamp past epoch in milliseconds."""
        # Handle 'Z' notation by replacing with +00:00
        iso_time = self.end_time
        if iso_time.endswith('Z'):
            iso_time = iso_time[:-1] + '+00:00'

        dt = datetime.fromisoformat(iso_time)

        # Ensure the datetime is timezone-aware (UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # converts to milliseconds
        return int(dt.timestamp() * 1000)

    @property
    def pagination_config(self) -> dict[str, int]:
        return { 'MaxItems': self.limit, 'PageSize': min(self.limit, 1000) }


class GetCloudWatchFieldsInput(GetCloudWatchLogsInputBase):
    """
    Use this tool before writing an insights query to understand the fields available to you.
    """
    pass

class GetCloudWatchLogsFilterPatternInput(GetCloudWatchLogsInputBase):
    """
    Use this tool when you need simple text matching or basic pattern filtering in CloudWatch logs.
    If the user asks for you to match a specific string or something, and simply analyze the logs, this is the right choice

    WHEN TO CHOOSE THIS TOOL:
    - You need to find specific text patterns or strings in logs
    - You need simple matching without complex analysis
    - You want to search for exact phrases or terms
    - You need to quickly filter logs based on presence/absence of text
    - You have a straightforward filtering need without requiring aggregation or statistics
    - You need to search for specific error messages or log patterns
    - You need logs exactly as they appear in CloudWatch without transformation

    DO NOT use this tool if you need to:
    - Perform calculations or aggregations on log data
    - Extract specific fields for analysis
    - Group by fields or create statistics
    - Parse structured logs into analyzable components
    - Perform time-based analysis

    For those advanced analytical needs, use the GetCloudWatchLogsInsightsQuery tool instead.
    """

    filter_pattern: str | None = Field(
        default=None,
        description="""
        CloudWatch filter pattern for text-based filtering. Leave empty to retrieve all logs without filtering.

        HOW TO WRITE EFFECTIVE FILTER PATTERNS:
        - Simple text matching: 'ERROR' (finds logs containing 'ERROR')
        - Multiple terms (OR logic): 'ERROR CRITICAL FATAL' (any of these terms)
        - Excluding terms: 'ERROR -INFO' (contains 'ERROR' but not 'INFO')
        - Exact phrases: '"connection timeout"' (exact phrase matching)
        - JSON field matching: '{ $.eventType = "ERROR" }' (for JSON structured logs)
        - Combining terms: '"user login" ERROR' (both terms must appear)
        - Wildcards aren't supported directly - use simpler terms instead

        The filter pattern is case-sensitive and supports basic text patterns only.
        """
    )

class GetCloudWatchLogsInsightsQueryInput(GetCloudWatchLogsInputBase):
    """
    BEFORE USING THIS TOOL, MAKE SURE YOU USE THE FIELDS TOOL TO UNDERSTAND THE LOGS.
    The fields tool shows the fields that are most likely present in the logs, but it doesn’t include everything.
    You may have to do a a keyword search using the `like` command instead of directly accessing data in fields. Use your best judgement here.
    Use this tool when you need advanced analytical capabilities for CloudWatch logs beyond simple text filtering.

    WHEN TO CHOOSE THIS TOOL:
    - You need to perform calculations or statistics on log data (counts, sums, averages)
    - You need to extract and analyze specific fields from structured logs
    - You want to group results by certain fields or properties
    - You need to detect trends or patterns over time periods
    - You want to transform log data into a more analyzable format
    - You need to sort, limit, or perform advanced filtering on results
    - You need to compare or analyze numeric values in logs

    DO NOT use this tool if:
    - You only need simple text matching (use the FilterPattern tool instead)
    - You just need to search for the presence of specific strings

    Insights queries are more powerful but can be more complex than filter patterns.
    """

    insights_query: str = Field(
        default=...,
        description="""
        CloudWatch Logs Insights query string for advanced log analysis.

        HOW TO WRITE EFFECTIVE INSIGHTS QUERIES:
        - Start with a command: Every query must begin with commands like 'fields', 'filter', or 'stats'
        - Basic field selection: 'fields @timestamp, @message'
        - Filtering: 'filter @message like /ERROR/'
        - Text pattern matching: 'filter @message like /fail/ or @message like /error/'
        - Extracting fields: 'parse @message "user=* status=*" as user, status'
        - Aggregations: 'stats count(*) as count by statusCode'
        - Time analysis: 'stats avg(duration) by bin(5m)'
        - Sorting: 'sort @timestamp desc'
        - Limiting results: 'limit 20'
        - Chaining commands with pipe (|): 'filter level="ERROR" | stats count(*) by service'. When building a chained query, try writing small queries step by step and piping them together iteratively.

        Available built-in fields include:
        - @timestamp: Event timestamp
        - @message: Raw log message
        - @logStream: Log stream name
        - @log: Additional log metadata

        For JSON logs, you can reference fields directly: 'stats avg(duration) by service'
        You can also reference nested fields using `.`, for example: 'stats count(*) by trace.filename'
        """
    )

    @field_validator("insights_query")
    def validate_insights_query(cls, v):
        if v is None:
            return v

        # Basic validation for CloudWatch Insights syntax
        valid_starting_commands = ['fields', 'filter', 'stats', 'sort', 'limit', 'parse']

        # Check if query starts with a valid command
        query_starts_with_valid_command = any(v.strip().lower().startswith(cmd) for cmd in valid_starting_commands)

        if not query_starts_with_valid_command:
            raise ValueError(
                f"Invalid CloudWatch Insights query. Query must start with one of: {', '.join(valid_starting_commands)}. "
                f"For example: 'fields @timestamp, @message | filter @message like /ERROR/'"
            )

        # Check for balanced quotes and pipes
        if v.count('"') % 2 != 0:
            raise ValueError("Invalid CloudWatch Insights query: Unbalanced double quotes")

        if v.count("'") % 2 != 0:
            raise ValueError("Invalid CloudWatch Insights query: Unbalanced single quotes")

        # Check for balanced regex delimiters
        if v.count("/") % 2 != 0:
            raise ValueError("Invalid CloudWatch Insights query: Unbalanced regex pattern delimiters (/)")

        return v


class CloudWatchConnectorTools(ConnectorToolsInterface[CloudWatchSecrets]):
    """
    A collection of tools used by agents that query AWS CloudWatch.
    """

    def __init__(
        self,
        config: CloudWatchConnectorConfig,
        target: CloudWatchTarget,
        secrets: CloudWatchSecrets
    ):
        super().__init__(ConnectorIdEnum.CLOUDWATCH, target, secrets)
        self.config = config
        self._log_stream_schemas: dict[str, list[str]] = {}

    def _get_scoped_log_streams(self) -> list[str]:
        return list(chain(*self._target.get_dataset_paths()))


    def get_tools(self) -> List[Tool]:
        tools: List[Tool] = []
        tools.append(
            Tool(
                connector=ConnectorIdEnum.CLOUDWATCH,
                name="query_cloudwatch_filter_pattern",
                execute_fn=self.get_cloudwatch_logs_filter_pattern_async,
                timeout_seconds=120,
            )
        )

        tools.append(
            Tool(
                connector=ConnectorIdEnum.CLOUDWATCH,
                name="query_cloudwatch_insights_query",
                execute_fn=self.get_cloudwatch_logs_insights_query_async,
                timeout_seconds=120,
            )
        )

        tools.append(
            Tool(
                connector=ConnectorIdEnum.CLOUDWATCH,
                name="query_cloudwatch_fields",
                execute_fn=self.get_fields_async,
            )
        )
        return tools


    async def _get_client_context(self, service: Literal["cloudwatch", "logs"]):
        """
        Internal helper to construct a CloudWatch client with configured retries and timeouts.

        :return: Configured CloudWatch client.
        """
        boto_config = BotoConfig(
            retries={
                'max_attempts': self.config.api_max_retries,
                'mode': 'standard'
            },
            connect_timeout=self.config.api_request_timeout,
            read_timeout=self.config.api_request_timeout
        )
        return await get_client_context(service, boto_config)

    async def query_cloudwatch_metrics_async(self, input: QueryCloudWatchMetricsInput) -> QueryResultMetadata:
        """
        Queries CloudWatch for metric statistics over a specified time range.

        Use this tool to retrieve time series data points for a specific metric.
        This can be used to monitor resource performance or investigate trends in AWS services.
        """

        async with await self._get_client_context("cloudwatch") as client:
            start_dt = datetime.fromtimestamp(input.start_time, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(input.end_time, tz=timezone.utc)
            # TODO: Add try/except around boto3 get_metric_statistics call to catch and raise clean AWS errors.
            response = await client.get_metric_statistics(
                Namespace=input.namespace,
                MetricName=input.metric_name,
                Dimensions=[{"Name": k, "Value": v} for k, v in input.dimensions.items()],
                StartTime=start_dt,
                EndTime=end_dt,
                Period=input.period,
                Statistics=input.statistics,
            )
        datapoints = response.get("Datapoints", [])
        sorted_dps = sorted(datapoints, key=lambda x: x["Timestamp"])
        timestamps = [dp["Timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ") for dp in sorted_dps]
        result: Dict[str, Any] = {"Label": response.get("Label", ""), "Timestamps": timestamps}
        for stat in input.statistics:
            result[stat] = [dp.get(stat) for dp in sorted_dps]
        return QueryResultMetadata(
            query_format="cloudwatch",
            query="get_metric_statistics",
            results=[[str(result)]],
            column_headers=["MetricData"],
        )

    async def _fetch_standard_query(self, input: GetCloudWatchLogsFilterPatternInput, client, log_group) -> list[dict[str, Any]]:
        """Handle standard log filtering with optional filter_pattern."""
        events = []
        paginator = client.get_paginator("filter_log_events")
        logger().debug(f"{input}")

        # Build the query parameters
        query_params = {
            "logGroupName": log_group,
            "startTime": input.start_timestamp,
            "endTime": input.end_timestamp,
            "PaginationConfig": input.pagination_config
        }

        # Add filter pattern if provided
        if input.filter_pattern:
            query_params["filterPattern"] = input.filter_pattern

        try:
            async for page in paginator.paginate(**query_params):
                events.extend(page.get("events", []))
                # Check if we've hit the limit
                if len(events) >= input.limit:
                    events = events[:input.limit]
                    break
        except Exception as e:
            logger().error(f"Error fetching events from {log_group}: {str(e)}")
            # Depending on your error handling strategy, you might want to raise or return empty

        return events

    async def _fetch_insights_query(self, input: GetCloudWatchLogsInsightsQueryInput, client, log_group) -> list[dict[str, Any]]:
        """Handle CloudWatch Logs Insights queries."""
        try:
            # Start the query
            start_query_response = await client.start_query(
                logGroupName=log_group,
                startTime=input.start_timestamp,
                endTime=input.end_timestamp,
                queryString=input.insights_query,
                limit=input.limit
            )

            query_id = start_query_response['queryId']

            # Poll until query completes
            while True:
                query_results = await client.get_query_results(queryId=query_id)
                status = query_results.get('status')

                if status in ['Complete', 'Failed', 'Cancelled']:
                    break

                # Wait a bit before polling again
                await asyncio.sleep(1)

            # For consistency with standard query format, transform insights results into events
            if status == 'Complete':
                # Convert Insights results to a format similar to log events
                events = []
                for result in query_results.get('results', []):
                    # Each result is a list of field/value pairs
                    event_data = {}
                    for field in result:
                        field_name = field.get('field')
                        field_value = field.get('value')
                        event_data[field_name] = field_value

                    # Create an event-like structure
                    event = {
                        "message": str(event_data),  # Convert the data to string for consistency
                        "timestamp": input.start_timestamp,  # Use query start time as fallback
                        "insights_result": event_data  # Keep the original data
                    }

                    # Extract timestamp if available
                    if '@timestamp' in event_data:
                        try:
                            ts = event_data['@timestamp']
                            # Try to parse timestamp if it's in a known format
                            if isinstance(ts, str):
                                if ts.endswith('Z'):
                                    ts = ts[:-1] + '+00:00'
                                dt = datetime.fromisoformat(ts)
                                event["timestamp"] = int(dt.timestamp() * 1000)
                        except (ValueError, TypeError):
                            pass  # Keep the default timestamp if parsing fails

                    events.append(event)

                    # Check if we've hit the limit
                    if len(events) >= input.limit:
                        break

                return events
            else:
                # Return an error event if the query failed
                error_event = {
                    "message": f"Query failed with status: {status}",
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "error": True
                }
                return [error_event]

        except Exception as e:
            logger().error(f"Error executing Insights query on {log_group}: {str(e)}")
            # Return an error event
            error_event = {
                "message": f"Error executing query: {str(e)}",
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "error": True
            }
            return [error_event]

    async def get_cloudwatch_logs_filter_pattern_async(self, input: GetCloudWatchLogsFilterPatternInput) -> QueryResultMetadata:
        async with await self._get_client_context("logs") as client:
            tasks = [self._fetch_standard_query(input, client, lg) for lg in self._get_scoped_log_streams()] # type: ignore[attr-defined]
            all_results = await asyncio.gather(*tasks)

            events = list(chain(*all_results))

            if len(events) > input.limit:
                events = events[:input.limit]

        query_format = "cloudwatch"
        filter_pattern_string = f" filterPattern={input.filter_pattern}" if input.filter_pattern else ""
        log_streams_string = ",".join(self._get_scoped_log_streams())
        query = f"filter_log_events logGroupNames={log_streams_string}{filter_pattern_string}"
        column_headers = ["Event"]
        results = [[str(event)] for event in events]

        return QueryResultMetadata(
            query_format=query_format,
            query=query,
            results=results,
            column_headers=column_headers,
        )

    async def get_cloudwatch_logs_insights_query_async(self, input: GetCloudWatchLogsInsightsQueryInput) -> QueryResultMetadata:
        async with await self._get_client_context("logs") as client:
            tasks = [self._fetch_insights_query(input, client, lg) for lg in self._get_scoped_log_streams()]
            all_results = await asyncio.gather(*tasks)

            events = list(chain(*all_results))

            if len(events) > input.limit:
                events = events[:input.limit]

        query_format = "cloudwatch_insights"
        log_streams_string = ",".join(self._get_scoped_log_streams())
        query_string = input.insights_query
        query = f"insights_query logGroupNames={log_streams_string} query={query_string}"

        # For insights queries, use custom column headers if we can extract them
        if events and events[0].get("insights_result"):
            column_headers = list(events[0]["insights_result"].keys())
            results = [[event["insights_result"].get(header, "") for header in column_headers] for event in events]
        else:
            column_headers = ["Event"]
            results = [[str(event)] for event in events]

        return QueryResultMetadata(
            query_format=query_format,
            query=query,
            results=results,
            column_headers=column_headers,
        )

    async def get_fields_async(self, input: GetCloudWatchFieldsInput) ->  dict[str, list[str]]:
        # TODO: user can add known fields per log stream
        system_fields = [
            '@timestamp',
            '@message',
            '@logStream',
            '@log',
            '@ingestionTime',
            '@eventId',
            '@ptr'
        ]
        basic_fields_query = "fields @timestamp, @log, @logStream, @message"
        # map: log_group: list of fields at log group
        fields_map: dict[str, list[str]] = {}

        async with await self._get_client_context("logs") as client:
            query_input = GetCloudWatchLogsInsightsQueryInput(**input.model_dump(), insights_query=basic_fields_query)

            # run the fields query for every log group we havent discovered the schema for
            tasks = []
            for log_group in self._get_scoped_log_streams():
                if log_group in self._log_stream_schemas:
                    continue
                tasks.append(self._fetch_insights_query(query_input, client, log_group))
            all_results = await asyncio.gather(*tasks)

            # update fields_map with the results of the fields query
            for log_group, queryresult in zip(self._get_scoped_log_streams(), all_results):
                log_group_fields = []
                for result_item in queryresult:
                    query_response = result_item.get("insights_result")
                    # in the case of an invalid log group, or a failure, this will return None, so we only append when
                    # there is an actual result
                    if isinstance(query_response, dict):
                        log_group_fields.extend(self._parse_fields(query_response))
                # update the fields map
                fields_map[log_group] = list(set(log_group_fields))

        # now we update the fields map with the already known log group schemas, and update the known schemas
        for log_group in self._get_scoped_log_streams():
            # if a log group in scope is already found, update fields map
            if log_group in self._log_stream_schemas:
                fields_map[log_group] = self._log_stream_schemas[log_group]
            else:
                # if the log group is somehow scoped but not in the fields map or existing schemas,
                # skip it (somehow we didnt get results)
                if log_group not in fields_map:
                    logger().warning("log group not in cache or in dynamic data dict. something went wrong")
                    continue
                # otherwise update known schemas with the log group
                self._log_stream_schemas[log_group] = fields_map[log_group]
        return fields_map

    def _parse_fields(self, query_result: dict[str, Any], prefix: str = "") -> list[str]:
        """
        Recursively extracts field names from nested data structures, using dot notation for hierarchy.

        Args:
            query_result: Dictionary containing potentially nested data
            prefix: Prefix to prepend to field names (for recursive calls)

        Returns:
            A flat list of field names, with nested fields represented using dot notation
        """
        fields = []


        for k, v in query_result.items():
            field_name = f"{prefix}.{k}" if prefix else k
            fields.append(field_name)

            # Handle nested dictionary
            if isinstance(v, dict):
                nested_fields = self._parse_fields(v, field_name)
                fields.extend(nested_fields)

            # Handle list of items
            elif isinstance(v, list) and v:
                for item in v:
                    if isinstance(item, dict):
                        nested_fields = self._parse_fields(item, field_name)
                        fields.extend(nested_fields)

            elif isinstance(v, str):
                try:
                    loaded_v = json.loads(v)
                    if isinstance(loaded_v, dict):
                        nested_fields = self._parse_fields(loaded_v, field_name)
                        fields.extend(nested_fields)
                    elif isinstance(loaded_v, list) and loaded_v:
                        for item in loaded_v:
                            if isinstance(item, dict):
                                nested_fields = self._parse_fields(item, field_name)
                                fields.extend(nested_fields)
                except (json.JSONDecodeError, TypeError):
                    # Not valid JSON, skip
                    continue

        processed_fields = []
        seen = set()

        for field in fields:
            # If field starts with @, strip away everything from @ to the first period
            if field.startswith('@') and '.' in field:
                # Find position of first period
                period_pos = field.find('.')
                # Keep only what comes after the first period
                field = field[period_pos+1:]

            # Add to result if not already seen
            if field not in seen:
                seen.add(field)
                processed_fields.append(field)

        return processed_fields
