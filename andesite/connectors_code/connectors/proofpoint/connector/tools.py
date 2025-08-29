import asyncio
import json
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
import re
from re import Pattern
from typing import Any, Literal
from common.models.connector_id_enum import ConnectorIdEnum
from common.jsonlogging.jsonlogger import Logging
from connectors.proofpoint.client.proofpoint_instance import Interval, ProofPointCampaignIdsResponse, ProofpointInstance
from connectors.proofpoint.connector.config import ProofpointConnectorConfig
from connectors.proofpoint.connector.secrets import ProofpointSecrets
from connectors.proofpoint.connector.parsing import (
    parse_proofpooint_forensics,
    parse_proofpoint_messages,
    parse_proofpoint_clicks,
)
from connectors.proofpoint.utils import validate_ISO8601_interval
from connectors.tools import ConnectorToolsInterface
from connectors.proofpoint.connector.target import ProofpointTarget
from connectors.cache import Cache
from common.models.tool import Tool
from datetime import timedelta
from pydantic import BaseModel, Field, field_validator, model_validator
from opentelemetry import trace

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def snake_to_camel(snake_str: str) -> str:
    """Turns a snake string to camel string, e.g. my_snake_string -> mySnakeString"""
    return "".join(
        x if i == 0 else x.capitalize()
        for i, x in enumerate(snake_str.lower().split("_"))
    )


def find_matches(pattern: Pattern[str], text: str) -> list[str]:
    """
    Return the list of terms that appear in `text`, case-insensitive.
    """
    seen = set()
    for m in pattern.finditer(text):
        seen.add(m.group(1).lower())
    return list(seen)


def search_for_iocs_in_records(records: list[dict], iocs: list[str]) -> list[dict]:
    """Search for strings in a list of json records"""
    joined = "|".join([re.escape(term) for term in iocs])
    pattern = re.compile(f"(?=({joined}))", re.IGNORECASE)
    results = []
    for record in records:
        try:
            serialized = json.dumps(record)
        except (TypeError, ValueError, UnicodeEncodeError) as e:
            continue
        iocs_found = find_matches(pattern, serialized)
        if iocs_found:
            record["iocs_found"] = iocs_found
            results.append(record)
    return results


class GetCampaignIdsInput(BaseModel):
    """List all campaign IDs and their status from the Proofpoint Campaign threat intelligence API. This is global intelligence and not specific to any customer."""

    lookback_days: int = Field(
        default=0,
        gt=0,
        le=30,
        description="Number of days to look back. Always round up to the nearest day, never round down."
    )


class GetSiemEventsInput(BaseModel):
    """Retrieve SIEM events from the Proofpoint API over a specified time range. These events indicate which clicks and messages were permitted and which were blocked within your environment. It contains extensive email and click metadata for each event."""

    interval: str = Field(
        description=(
            "A string containing an ISO8601-formatted interval.\n"
            "Note: Intervals that contain the future will result in an API error.\n"
            "Examples:\n"
            "- '2016-05-01T12:00:00Z/2016-05-01T13:00:00Z' - an hour interval, beginning at noon UTC on 05-01-2016\n"
            "- '2016-05-01T12:00:00Z/2016-05-01T22:00:00Z' - a 10 hour interval, beginning at noon UTC on 05-01-2016\n"
        )
    )
    threat_status: list[str] = Field(
        default=["active"],
        description="The threat status to filter the SIEM events. Any combination of: ['falsePositive', 'active', 'cleared'].",
    )
    limit: int = Field(
        default=100,
        description="The number of records that will be shown to the LLM. The full results will still be cached and value counts of event types will be shown."
    )

    @field_validator("interval")
    def validate_interval(cls, value: str) -> str:
        """Validate the interval format."""
        return validate_ISO8601_interval(value)

    @field_validator("threat_status")
    def validate_threat_status(cls, value: list[str]) -> list[str]:
        """Validate and sort the threat_status array to minimize chance of cache misses."""
        valid_statuses = ["falsePositive", "active", "cleared"]
        if not all(status in valid_statuses for status in value):
            raise ValueError(
                f"Invalid threat status. Must be one or more of: {valid_statuses}"
            )
        return sorted(value)


class FindSiemEventsByIOCsInput(BaseModel):
    """Retrieve SIEM events in customer environment that contain specific strings (IOCs). Returns the hits up to limit."""

    interval: str = Field(
        description=(
            "A string containing an ISO8601-formatted interval.\n"
            "Note: Intervals that contain the future will result in an API error.\n"
            "Examples:\n"
            "- '2016-05-01T12:00:00Z/2016-05-01T13:00:00Z' - an hour interval, beginning at noon UTC on 05-01-2016\n"
            "- '2016-05-01T12:00:00Z/2016-05-01T22:00:00Z' - a 10 hour interval, beginning at noon UTC on 05-01-2016\n"
        )
    )
    threat_status: list[str] = Field(
        default=["active"],
        description="The threat status to filter the SIEM events. Any combination of: ['falsePositive', 'active', 'cleared'].",
    )
    iocs: list[str] = Field(
        default=[],
        description="A list of strings to search for in the SIEM events. These can be any indicators of compromise (IOCs) such as IP addresses, domain names, or file hashes.",
    )
    event_type: Literal[
        "messages_delivered",
        "messages_blocked",
        "clicks_permitted",
        "clicks_blocked",
        "all",
    ] = Field(
        default="all",
        description=(
            "The type of message to search for in the SIEM events. "
            "Can be one of: ['messages_delivered', 'messages_blocked', 'clicks_permitted', 'clicks_blocked', 'all']."
        ),
    )
    limit: int = Field(
        default=100,
        description="The number of records that will be shown to the LLM. The full results will still be cached and value counts of event types will be shown."
    )

    @field_validator("interval")
    def validate_interval(cls, value: str) -> str:
        """Validate the interval format."""
        return validate_ISO8601_interval(value)

    @field_validator("threat_status")
    def validate_threat_status(cls, value: list[str]) -> list[str]:
        """Validate and sort the threat_status array to minimize chance of cache misses."""
        valid_statuses = ["falsePositive", "active", "cleared"]
        if not all(status in valid_statuses for status in value):
            raise ValueError(
                f"Invalid threat status. Must be one or more of: {valid_statuses}"
            )
        return sorted(value)


class GetCampaignDetailsInput(BaseModel):
    """Retrieve detailed information from Proofpoint threat intelligence about a specific campaign."""

    campaign_id: str = Field(
        description="The unique identifier of the campaign to retrieve details for."
    )
    include_campaign_members: bool = Field(
        default=False,
        description="Whether or not to show the campaign members in the response. Defaults to False. If True, the response will include details about each threat variant which has been correlated to this campaign",
    )


class FindCampaignsWithIOCsInput(GetCampaignIdsInput):
    """Retrieve Campaign details from the Proofpoint API over a specified time range. Then search them for specific strings (IOCs). Returns the hits."""

    include_campaign_members: bool = Field(
        default=False,
        description="Whether or not to show the campaign members in the response. Defaults to False. If True, the response will include details about each threat variant which has been correlated to this campaign",
    )
    iocs: list[str] = Field(
        default=[],
        description="A list of strings to search for in the SIEM events. These can be any indicators of compromise (IOCs) such as IP addresses, domain names, or file hashes.",
    )


class GetForensicsByThreatInput(BaseModel):
    """Retrieve all evidence of a ProofPoint identified threat in our environment. May not be immediately consistent with the SIEM events."""

    threat_id: str = Field(
        description="The unique identifier of the threat to retrieve environment forensics for."
    )
    include_campaign_forensics: bool = Field(
        default=True,
        description="Whether or not to include forensics data for the associated campaign.",
    )
    include_nonmalicious: bool = Field(
        default=False,
        description="Whether or not to include non malicious forensics data. Defaults to False. CAUTION: Setting this to True will return substantial amounts of data that could cause LLM context issues.",
    )


class GetForensicsByCampaignInput(BaseModel):
    """Retrieve all evidence of a ProofPoint identified campaign in our environment. May not be immediately consistent with the SIEM events."""

    campaign_id: str = Field(
        description="The unique identifier of the campaign to retrieve environment forensics for."
    )
    include_nonmalicious: bool = Field(
        default=False,
        description="Whether or not to include non malicious forensics data. Defaults to False. CAUTION: Setting this to True will return substantial amounts of data that could cause LLM context issues.",
    )


class ProofpointConnectorTools(ConnectorToolsInterface[ProofpointSecrets]):
    """
    A collection of tools used by agents to interact with Proofpoint Threat Intelligence APIs.
    """

    def __init__(
        self,
        target: ProofpointTarget,
        config: ProofpointConnectorConfig,
        secrets: ProofpointSecrets,
        cache: Cache | None = None,
    ):
        """
        Initialize the ProofPoint connector tools.
        :param target: The ProofPoint query target (ProofPointTarget) instance specifying space keys.
        :param config: The ProofPointConnectorConfig with configuration details.
        """
        self.target = target
        self.config = config
        self.cache = cache
        self.client = ProofpointInstance(
            api_host=config.api_host,
            principal=config.principal,
            token=secrets.token,
            request_timeout=config.request_timeout,
            max_retries=config.max_retries,
            cache=cache,
        )
        super().__init__(ConnectorIdEnum.PROOFPOINT, target, secrets)

    async def get_campaign_ids_async(
            self, input: GetCampaignIdsInput
    ) -> list[dict[str, Any]]:
        """
        Get all campaign data from the last specified time period using the DatasetStructureManager.
        Starts from the latest indexed data, not current time.

        Args:
            lookback_days: Number of days to look back

        Returns:
            List of campaign data dictionaries
        """
        existing_datasets = await DatasetStructureManager.instance().get_all_dataset_structures_async(
            ConnectorIdEnum.PROOFPOINT
        )

        if not existing_datasets:
            logger().warning("no existing datasets found for ProofPoint connector.")
            return []

        end_time = max(
            Interval(interval=dataset.dataset).parse_as_datetimes()[1]
            for dataset in existing_datasets
        )
        start_time = end_time - timedelta(days=input.lookback_days)
        # Create the target interval
        target_interval = Interval(
            interval=f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        # Find datasets that overlap with our target time range
        overlapping_datasets = []
        for dataset in existing_datasets:
            dataset_interval = Interval(interval=dataset.dataset)
            if target_interval.overlaps_with(dataset_interval):
                overlapping_datasets.append(dataset)

        # Extract campaign data from overlapping datasets
        all_campaigns = []
        for dataset in overlapping_datasets:
            campaigns = ProofPointCampaignIdsResponse.model_validate(dataset.attributes).campaigns
            all_campaigns.extend(campaigns)

        return [c.model_dump() for c in all_campaigns]

    @tracer.start_as_current_span("get_campaign_details_async")
    async def get_campaign_details_async(
        self, input: GetCampaignDetailsInput
    ) -> dict[str, Any]:
        """
        Fetch detailed information for a specific campaign.
        """
        details = await self.client.get_campaign(campaign_id=input.campaign_id)
        if not input.include_campaign_members:
            _ = details.pop("campaignMembers", [])
            return details
        return details

    @tracer.start_as_current_span("find_campaigns_by_iocs_async")
    async def find_campaigns_by_iocs_async(
        self, input: FindCampaignsWithIOCsInput
    ) -> list[dict[str, Any]]:
        """
        Find campaigns that contain specific IOCs over a specified time interval.
        """
        campaign_ids_result = await self.get_campaign_ids_async(input)

        campaign_ids = [
            campaign["id"] for campaign in campaign_ids_result
        ]
        if not campaign_ids:
            return []

        campaign_details = await asyncio.gather(
            *(
                self.client.get_campaign(campaign_id=campaign_id)
                for campaign_id in campaign_ids
            )
        )

        hits = search_for_iocs_in_records(campaign_details, input.iocs)
        # Filter out campaign members to keep response manageable
        if not input.include_campaign_members:
            for hit in hits:
                _ = hit.pop("campaignMembers", [])
            return hits
        return hits

    @tracer.start_as_current_span("get_siem_events_for_time_range_async")
    async def get_siem_events_for_time_range_async(
        self, input: GetSiemEventsInput
    ) -> dict[str, str | dict[str, list[dict[str, Any]]]]:
        """
        Fetch all ProofPoint SIEM events over a time period.
        """
        siem_events = await self.client.get_siem_events(
            interval=input.interval, threat_status=input.threat_status
        )

        messages_delivered = siem_events.get("messagesDelivered", [])
        messages_blocked = siem_events.get("messagesBlocked", [])
        clicks_permitted = siem_events.get("clicksPermitted", [])
        clicks_blocked = siem_events.get("clicksBlocked", [])

        result = {
            "messagesDelivered": parse_proofpoint_messages(messages_delivered)
            if messages_delivered
            else [],
            "messagesBlocked": parse_proofpoint_messages(messages_blocked)
            if messages_blocked
            else [],
            "clicksPermitted": parse_proofpoint_clicks(clicks_permitted)
            if clicks_permitted
            else [],
            "clicksBlocked": parse_proofpoint_clicks(clicks_blocked)
            if clicks_blocked
            else [],
        }

        value_counts = {k: len(v) for k, v in result.items()}
        if sum(value_counts.values()) <= input.limit:
            return {
                "message": f"The query returned the following number of records by type:\n{json.dumps(value_counts)}.\nComplete results have been cached and are searchable.",
                "results": result,
            }

        preview = {}
        limit = input.limit
        for k, v in result.items():
            preview[k] = v[:limit]
            limit -= len(preview[k])

        return {
            "message": f"The query returned the following number of records by type:\n{json.dumps(value_counts)}.\nComplete results have been cached and are searchable.\nYou are being shown a preview of {input.limit} records.\nConsider using an IOC search to filter for relevant records.",
            "results": preview,
        }

    @tracer.start_as_current_span("find_siem_events_by_iocs_async")
    async def find_siem_events_by_iocs_async(
        self, input: FindSiemEventsByIOCsInput
    ) -> dict[str, str | dict[str, list[dict]]]:
        """
        Find SIEM events that contain specific IOCs over a specified time interval.
        """

        all_siem_events = await self.client.get_siem_events(
            interval=input.interval, threat_status=input.threat_status
        )
        if input.event_type != "all":
            # filter to searchable events
            searchable_events = {
                snake_to_camel(input.event_type): all_siem_events.get(
                    snake_to_camel(input.event_type), []
                )
            }
        else:
            searchable_events = all_siem_events

        hits = {}
        for event_type, events in searchable_events.items():
            if events and isinstance(events, list):
                try:
                    hits[event_type] = search_for_iocs_in_records(events, input.iocs)
                except ValueError as e:
                    logger().exception(
                        "Error searching for IOCs in event type %s: %s.", event_type, e
                    )
                finally:
                    continue
        value_counts = {k: len(v) for k, v in hits.items()}
        if sum(value_counts.values()) <= input.limit:
            return {
                "message": f"The query returned the following number of records by type:\n{json.dumps(value_counts)}.",
                "results": hits,
            }

        preview = {}
        limit = input.limit
        for k, v in hits.items():
            preview[k] = v[:limit]
            limit -= len(preview[k])

        return {
            "message": f"The query returned the following number of records by type:\n{json.dumps(value_counts)}.\nYou are being shown a preview of {input.limit} records.",
            "results": preview,
        }

    @tracer.start_as_current_span("get_forensics_by_threat_id")
    async def get_forensics_by_threat_id(
        self, input: GetForensicsByThreatInput
    ) -> dict[str, Any]:
        """Fetch all evidence of a ProofPoint identified threat in our environment."""
        forensics = await self.client.get_threat_forensics(
            threat_id=input.threat_id,
            include_campaign_forensics=input.include_campaign_forensics,
        )
        return parse_proofpooint_forensics(
            forensics, include_nonmalicious=input.include_nonmalicious
        )

    @tracer.start_as_current_span("get_forensics_by_campaign_id")
    async def get_forensics_by_campaign_id(
        self, input: GetForensicsByCampaignInput
    ) -> dict[str, Any]:
        """Fetch all evidence for a specific ProofPoint identified campaign in our environment."""
        forensics = await self.client.get_campaign_forensics(
            campaign_id=input.campaign_id
        )
        return parse_proofpooint_forensics(
            forensics, include_nonmalicious=input.include_nonmalicious
        )

    def get_tools(self) -> list[Tool]:
        return [
            Tool(connector=ConnectorIdEnum.PROOFPOINT, name="get_campaign_ids", execute_fn=self.get_campaign_ids_async),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="get_campaign_details", execute_fn=self.get_campaign_details_async
            ),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="get_siem_events_for_time_range",
                execute_fn=self.get_siem_events_for_time_range_async,
            ),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="get_forensics_by_threat_id",
                execute_fn=self.get_forensics_by_threat_id,
            ),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="get_forensics_by_campaign_id",
                execute_fn=self.get_forensics_by_campaign_id,
            ),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="find_siem_events_by_iocs",
                execute_fn=self.find_siem_events_by_iocs_async,
            ),
            Tool(connector=ConnectorIdEnum.PROOFPOINT,
                name="find_campaigns_by_iocs",
                execute_fn=self.find_campaigns_by_iocs_async,
            ),
        ]
