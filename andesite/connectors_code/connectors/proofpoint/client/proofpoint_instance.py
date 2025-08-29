import asyncio
from enum import StrEnum
from typing import Any, Callable
from opentelemetry import trace

from httpx import AsyncClient, HTTPStatusError
from pydantic import BaseModel, SecretStr, field_validator, ConfigDict, Field

from connectors.cache import Cache
from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.proofpoint.utils import (
    validate_ISO8601_interval,
    round_time_down_to_nearest_increment,
    round_time_up_to_nearest_increment,
    interval_end_more_than_timedelta_ago,
)
from datetime import timedelta, datetime, timezone, UTC


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class Interval(BaseModel):
    interval: str

    @field_validator("interval")
    def validate_interval(cls, value: str) -> str:
        """Validate the interval format."""
        try:
            start_str, end_str = value.split("/")
            datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%SZ")
            datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%SZ")
            return value
        except ValueError:
            raise ValueError(
                "Invalid interval format. Expected 'YYYY-MM-DDTHH:MM:SSZ/YYYY-MM-DDTHH:MM:SSZ'."
            )

    def parse_as_datetimes(self) -> tuple[datetime, datetime]:
        """Parse the interval into datetime objects."""
        start_str, end_str = self.interval.split("/")
        start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%SZ")
        end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%SZ")
        return start, end

    def overlaps_with(self, other: "Interval") -> bool:
        """Return True if this interval overlaps with another."""
        start1, end1 = self.parse_as_datetimes()
        start2, end2 = other.parse_as_datetimes()

        return max(start1, start2) < min(end1, end2)


class SegmentTimeUnit(StrEnum):
    """Enum for time units used in segmenting intervals."""

    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"


class ProofpointCampaign(BaseModel):
    """Model for a single Proofpoint campaign
       https://help.proofpoint.com/Threat_Insight_Dashboard/API_Documentation/Campaign_API
    """
    model_config = ConfigDict(extra='allow')  # Allow additional fields from API

    id: str = Field(..., description="Unique campaign identifier")
    lastUpdatedAt: str = Field(..., description="Last updated timestamp")

class ProofpointCampaignIdApiResponse(BaseModel):
    """Model for Proofpoint API response structure"""
    model_config = ConfigDict(extra='allow')  # Allow additional API fields

    campaigns: list[ProofpointCampaign] = Field(default_factory=list)
    page: int | None = None
    total: int | None = None

class ProofPointCampaignIdsResponse(BaseModel):
    campaigns: list[ProofpointCampaign] = Field(default_factory=list)

def make_key(method: str, url: str, params: dict[str, Any]) -> str:
    """
    Creates a cache key based on the method, URL, and parameters.

    :param method: HTTP method
    :param url: URL for the request
    :param params: Query parameters for the request
    :return: A string key for caching
    """
    if params:
        sorted_params = dict(sorted(params.items()))
        params_key = "-".join([f"{k}-{v}" for k, v in sorted_params.items()])
        return f"{method}-{url}-{params_key}"
    return f"{method}-{url}-{{}}"

async def _add_cache_to_request_function(
    request_fn: Callable,
    method: str,
    url: str,
    auth: tuple[str, str],
    params: dict[str, Any],
    timeout: int,
    max_retries: int,
    cache: Cache,
    connector_id: ConnectorIdEnum,
    expiry_sec: int,
) -> Any:
    """
    Makes an HTTP request, checking the cache first. If the response is not cached, it will make the request and store the result in the cache.

    :param method: HTTP method (GET, POST, etc.)
    :param url: URL to make the request to
    :param auth: Authentication tuple (username, password)
    :param params: Query parameters for the request
    :param timeout: Timeout for the request in seconds
    :param max_retries: Maximum number of retries for the request
    :param cache: An instance of Cache to store results
    :param connector_id: The ID of the connector for which the cache is being used
    :param expiry_sec: Expiry time for the cache in seconds
    :return: The response from the HTTP request, either from cache or the actual request
    """
    key = make_key(method, url, params)
    try:
        response = await cache.get(connector=connector_id, key=key)
    except Exception as e:
        response = None
        logger().exception(f"Cache retrieval failed: {e}")

    if response:
        logger().info(f"Cache hit for key: {key}")
        return response

    logger().info(f"Cache miss for key: {key}. Making HTTP request.")
    response = await request_fn(
        method=method,
        url=url,
        params=params,
        auth=auth,
        timeout=timeout,
        max_retries=max_retries,
    )

    if response:
        try:
            await cache.set(
                connector=connector_id, key=key, data=response, expiry_sec=expiry_sec
            )
        except Exception as e:
            logger().exception(f"Cache storage failed: {e}")
    return response


def _segment_interval_by_unit(interval: str, unit: SegmentTimeUnit) -> list[str]:
    """Helper function to segment a time interval into 24-hour segments."""

    if unit == SegmentTimeUnit.DAY:
        delta = timedelta(days=1)
    elif unit == SegmentTimeUnit.HOUR:
        delta = timedelta(hours=1)
    elif unit == SegmentTimeUnit.MINUTE:
        delta = timedelta(minutes=1)
    else:
        raise ValueError("unit must be an instance of SegmentTimeUnit.")

    try:
        start_str, end_str = interval.split("/")
        start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception as exc:
        raise ValueError(
            "Invalid interval format. Expected 'YYYY-MM-DDTHH:MM:SSZ/YYYY-MM-DDTHH:MM:SSZ'."
        ) from exc

    current_start = start_time
    segments: list[str] = []
    while current_start < end_time:
        current_end = min(current_start + delta, end_time)
        segments.append(
            f"{current_start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{current_end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
        current_start = current_end
    return segments


async def _request_with_retry(
    method: str,
    url: str,
    auth: tuple[str, str],
    params: dict[str, Any],
    timeout: int,
    max_retries: int,
) -> Any:
    """
    Throws if max retries is exceeded
    """
    retries = 0
    while retries < max_retries:
        try:
            async with AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    url=url, method=method, auth=auth, params=params
                )
                response.raise_for_status()
                return response.json()
        except HTTPStatusError as exc:
            logger().exception(f"Encountered an HTTP error: {exc.response.status_code}, message: {exc.response.text}")
            if exc.response.status_code == 429 and retries < max_retries:
                await asyncio.sleep(2**retries)
                retries += 1
                continue
            raise exc
    raise Exception("Max retries exceeded")





class ProofpointInstance:
    def __init__(
        self,
        api_host: str,
        principal: str,
        token: SecretStr | None,
        request_timeout: int,
        max_retries: int,
        cache: Cache | None = None,
    ):
        self.base_url = api_host.rstrip("/")
        self.auth = (principal, token.get_secret_value() if token else "UNSET_TOKEN")
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.cache = cache



    async def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any],
        expiry_sec: int | None = None,
    ) -> Any:
        if expiry_sec and not self.cache:
            raise ValueError(
                "Expiry time is set but cache is not provided. Please provide a Cache instance."
            )
        if expiry_sec and self.cache:
            return await _add_cache_to_request_function(
                request_fn=_request_with_retry,
                method=method,
                url=url,
                params=params,
                auth=self.auth,
                max_retries=self.max_retries,
                timeout=self.request_timeout,
                cache=self.cache,
                connector_id=ConnectorIdEnum.PROOFPOINT,
                expiry_sec=expiry_sec,
            )
        return await _request_with_retry(
            method=method,
            url=url,
            params=params,
            auth=self.auth,
            max_retries=self.max_retries,
            timeout=self.request_timeout,
        )

    async def _request_all_results(
        self, url: str, params: dict[str, Any], expiry_sec: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Helper function to make a paginated HTTP GET requests that terminate on 404.
        """
        results: list[dict[str, Any]] = []
        params["page"] = 1
        while True:
            try:
                page_data = await self.request(
                    method="GET", url=url, params=params, expiry_sec=expiry_sec
                )
                results.append(page_data)
                params["page"] += 1
            except HTTPStatusError as exc:
                # This condition indicates that there are no more pages to fetch
                logger().exception(
                    f"Encountered an HTTP error: {exc.response.status_code}"
                )
                if exc.response.status_code == 404:
                    return results
                raise exc

    async def check_connection_async(self) -> bool:
        url = f"{self.base_url}/v2/siem/all"
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(minutes=1)
        threat_status = ["falsePositive", "active", "cleared"]
        interval = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        params: dict[str, str | list[str]] = {"interval": interval, "format": "json", "threatStatus": threat_status}

        try:
            return bool(self.request(method="GET", url=url, params=params))
        except Exception:
            return False



    async def _get_campaign_ids_unsafe(
        self,
        interval: str,
        size: int,
        segment_unit: SegmentTimeUnit = SegmentTimeUnit.DAY,
    ) -> ProofPointCampaignIdsResponse:
        """
        Note: The 'v2/campaign/ids' endpoint is rate limited to 50 requests per 24 hours
        (https://help.proofpoint.com/Threat_Insight_Dashboard/API_Documentation/Campaign_API)
        """

        interval = validate_ISO8601_interval(interval)
        # Note on rounding the time interval.
        # We ensure that the interval start uses the beginning of the day containing the request
        # since we fetch and cache campaign IDs in 1-day segments.
        # The last segment is rounded up to the next hour to avoid making excessive API requests that could exhaust
        # the quota.
        start, end = interval.split("/")

        # Ensure that the interval start is rounded down to the beginning of the day containing the request
        start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        start_dt_rounded = round_time_down_to_nearest_increment(
            start_dt, increment=60 * 60 * 24
        )
        start_str = start_dt_rounded.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Ensure that the interval end is rounded up to the beginning of the hour after the request
        end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        end_dt_rounded = round_time_up_to_nearest_increment(end_dt, increment=60 * 60)
        end_str = end_dt_rounded.strftime("%Y-%m-%dT%H:%M:%SZ")

        rounded_interval = f"{start_str}/{end_str}"

        results: dict[str, Any] = {"campaigns": []}
        for segment in _segment_interval_by_unit(rounded_interval, unit=segment_unit):
            url = f"{self.base_url}/v2/campaign/ids"
            params: dict[str, Any] = {"interval": segment, "size": size}

            try:
                segment_pages = await self._request_all_results(
                    url, params, expiry_sec=24 * 60 * 60 if self.cache else None
                )
            except HTTPStatusError as exc:
                logger().exception(
                    f"Encountered an HTTP error: {exc.response.status_code}"
                )
                raise exc

            segment_campaigns = []
            for page in segment_pages:
                segment_campaigns += page.get("campaigns", [])

            results["campaigns"].extend(segment_campaigns)

        return ProofPointCampaignIdsResponse.model_validate(results)

    async def get_campaign(self, campaign_id: str) -> Any:
        url = f"{self.base_url}/v2/campaign/{campaign_id}"
        # Cache for 1 min since there are no rate limits, but we need a value to avoid immortal keys
        return await self.request("GET", url, {}, expiry_sec=60 if self.cache else None)

    async def get_siem_events(
        self,
        interval: str,
        threat_status: list[str],
        segment_unit: SegmentTimeUnit = SegmentTimeUnit.HOUR,
    ) -> dict[str, list[dict[str, Any]]]:
        interval = validate_ISO8601_interval(interval)
        # Note on rounding the time interval.
        # We ensure that the interval start uses the beginning of the hour containing the SIEM endpoint request
        # since we fetch and cache the SIEM events in 1-hour segments.
        # The exception is the last segment which bounded by the current time. This last segment is rounded down to
        # the previous hour to avoid making excessive API requests that could exhaust the quota.
        start, end = interval.split("/")

        # Ensure that the interval start is rounded down to the beginning of the hour containing the request
        start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        start_dt_rounded = round_time_down_to_nearest_increment(
            start_dt, increment=60 * 60
        )
        start_str = start_dt_rounded.strftime("%Y-%m-%dT%H:%M:%SZ")

        if interval_end_more_than_timedelta_ago(interval, timedelta(hours=1)):
            # If the interval end is more than 1 hour old, we can round up to the next hour to guarantee we include the
            # target interval while snapping the interval to 1-hr segments to avoid making excessive API requests.
            end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
            end_dt_rounded = round_time_up_to_nearest_increment(
                end_dt, increment=60 * 60
            )
            end_str = end_dt_rounded.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            # Otherwise, the interval end is within a 1-hr segment that is still receiving new events. We ensure that
            # the interval end is rounded down to the beginning of the minute containing the request.
            # We round down to prevent 404 errors resulting from an interval end that is in the future.
            end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
            end_dt_rounded = round_time_down_to_nearest_increment(end_dt, increment=60)
            end_str = end_dt_rounded.strftime("%Y-%m-%dT%H:%M:%SZ")

        rounded_interval = f"{start_str}/{end_str}"

        siem_events: dict[str, list[dict[str, Any]]] = {}

        for segment in _segment_interval_by_unit(rounded_interval, unit=segment_unit):
            url = f"{self.base_url}/v2/siem/all"
            params: dict[str, Any] = {
                "format": "json",
                "interval": segment,
                "threatStatus": threat_status,
            }

            # Cache for 1 day if interval ended more than 24 hours ago, otherwise 5 min.
            # This assumes that older events are less likely to change and can be cached longer.
            ttl = (
                24 * 60 * 60
                if interval_end_more_than_timedelta_ago(
                    segment, timedelta(days=1)
                )
                else 5 * 60
            )
            segment_events = await self.request(
                "GET", url, params, expiry_sec=ttl if self.cache else None
            )
            for key in segment_events.keys():
                new_siem_events = [event for event in segment_events.get(key, [])]
                if key not in siem_events:
                    siem_events[key] = []
                siem_events[key].extend(new_siem_events)

        return siem_events

    async def get_campaign_forensics(self, campaign_id: str) -> Any:
        url = f"{self.base_url}/v2/forensics"

        params: dict[str, Any] = {
            "campaignId": campaign_id,
        }
        # Cache for 10 min since the rate limit is 1800 per day, but we may be sharing the quota
        return await self.request(
            "GET", url, params, expiry_sec=10 * 60 if self.cache else None
        )

    async def get_threat_forensics(
        self, threat_id: str, include_campaign_forensics: bool
    ) -> Any:
        url = f"{self.base_url}/v2/forensics"

        params: dict[str, Any] = {
            "includeCampaignForensics": include_campaign_forensics,
            "threatId": threat_id,
        }
        # If no campaign forensics, limit is 50 per day per threat id so use 1 hour,
        # otherwise the limit is 1800 per day, so use 10 minutes
        expiry_sec = 60 * 60 if not include_campaign_forensics else 10 * 60
        return await self.request(
            "GET", url, params, expiry_sec=expiry_sec if self.cache else None
        )
