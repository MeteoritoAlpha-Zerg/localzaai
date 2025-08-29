import requests
from typing import Any, Optional
from pydantic import BaseModel
import pandas as pd
from common.jsonlogging.jsonlogger import Logging


logger = Logging.get_logger(__name__)


class CensysHostSearchPredictionModel(BaseModel):
    search_ip: str
    search_snapshot_date: str = "2024-07-10"
    num_results: int = 20
    distance_metric: str = "l2"


class CensysService(BaseModel):
    port: Optional[int]
    transport: Optional[str]
    service_name: Optional[str]
    software: Optional[str]


class CensysAutonomousSystem(BaseModel):
    asn: Optional[int]
    description: Optional[str]
    bgp_prefix: Optional[str]
    name: Optional[str]
    country_code: Optional[str]
    organization: Optional[str]


class CensysHost(BaseModel):
    ip: str
    snapshot_date: str
    l2: float
    services: Optional[list[CensysService]]
    location: Optional[str]
    operating_system: Optional[str]
    dns: list[str]


def simplify_service(service) -> dict[str, Any]:
    simple_service = {}

    for k, v in service.items():
        simple_service["port"] = service.get("port", None)
        simple_service["service_name"] = service.get("service_name", None)
        simple_service["transport"] = service.get("transport", None)
        software = service.get("software", [])
        if software:
            simple_service["software"] = software[0].get(
                "uniform_resource_identifier", None
            )
        else:
            simple_service["software"] = None
    return simple_service


def simplify_services(services) -> list[dict]:
    return [simplify_service(svc) for svc in services]


def preview_censys_records(records: list[dict]) -> list[dict]:
    if not records:
        return []

    fields = [
        "ip",
        "snapshot_date",
        "l2",
        "services",
        "location",
        "operating_system",
        "dns",
    ]

    df = pd.DataFrame(records)

    df["ip"] = df["host_identifier"].apply(lambda host: host["ipv4"])
    df["snapshot_date"] = df["date"]
    df["l2"] = df["l2"].apply(lambda l2: round(l2, 3))
    df["location"] = df["location"].apply(lambda loc: loc["country"])
    df["services"] = df["services"].apply(lambda svcs: simplify_services(svcs))
    df["operating_system"] = df["operating_system"].apply(
        lambda os: os["uniform_resource_identifier"] if os else os
    )
    df["dns"] = df["dns"].apply(lambda dns: dns["names"] if dns else [])

    return df[fields].to_dict(orient="records")


class EquinoxInstance:
    """
    Equinox instance is used by retrievers to interact with the Equinox search API.
    """

    def __init__(
        self,
        protocol,
        host,
        port,
    ):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.url = self._format_url()

    def _format_url(self):
        return f"{self.protocol}://{self.host}:{self.port}"

    def health_check(self) -> dict:
        try:
            response = requests.get(f"{self._format_url}/docs")
            if response.status_code == 200:
                return {"health": "ok"}
            else:
                return {"health": "not ok"}
        except requests.exceptions.RequestException:
            return {"health": "not ok"}

    def fetch_one_host(self, query: CensysHostSearchPredictionModel) -> dict[str, Any]:
        url = f"{self.url}/fetch_one"

        params = {
            "ip": query.search_ip,
            "snapshot_date": query.search_snapshot_date,
        }

        try:
            api_response = requests.post(url, params=params)
            api_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger().error(f"Failed to fetch host from {url}: {e}")
            raise

        logger().info(
            "Equinox Instance fetch_one_host API response: %s...",
            api_response.text[:500],
        )

        try:
            record = api_response.json()
            record["l2"] = 0.0
        except ValueError as e:
            logger().error(f"Failed to parse JSON response: {e}")
            raise

        return preview_censys_records([record])[0]

    def query_censys_host_search(
        self,
        query: CensysHostSearchPredictionModel,
    ) -> list[dict[str, Any]]:
        url = f"{self.url}/host_search"
        payload = {"queries": [dict(query)]}

        try:
            api_response = requests.post(url, json=payload)
            api_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger().error(f"Failed to query host search from {url}: {e}")
            raise

        logger().info(
            "Equinox Instance query_censys_host_search API response: %s...",
            api_response.text[:500],
        )

        try:
            records = api_response.json().get("records", [])
        except ValueError as e:
            logger().error(f"Failed to parse JSON response: {e}")
            raise

        return preview_censys_records(records)
