import json
from typing import Any

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.metadata import QueryResultMetadata
from common.models.tool import Tool
from domaintools import API  # type: ignore [import-untyped]
from opentelemetry import trace
from pydantic import BaseModel, Field

from connectors.domaintools.connector.config import DomainToolsConnectorConfig
from connectors.domaintools.connector.target import DomainToolsTarget
from connectors.domaintools.connector.secrets import DomainToolsSecrets
from connectors.tools import ConnectorToolsInterface

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)


class DomainToolsConnectorTools(ConnectorToolsInterface[DomainToolsSecrets]):
    """
    A collection of tools used by agents that query DomainTools.
    """

    def __init__(
        self,
        domain_tools_config: DomainToolsConnectorConfig,
        target: DomainToolsTarget,
        secrets: DomainToolsSecrets,
    ):
        """
        Initializes the tool collection for a specific DomainTools target.

        :param target: The DomainTools target the tools will target.
        """
        self.api = API(
            secrets.api_username.get_secret_value(),
            secrets.api_key.get_secret_value(),
        )
        super().__init__(ConnectorIdEnum.DOMAINTOOLS, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        tools.append(
            Tool(
                connector=ConnectorIdEnum.DOMAINTOOLS,
                name="get_iris_enrich",
                execute_fn=self.get_iris_enrich_async,
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.DOMAINTOOLS,
                name="get_pivot_domain_filters",
                execute_fn=self.get_pivot_domain_filters,
            )
        )
        tools.append(
            Tool(
                connector=ConnectorIdEnum.DOMAINTOOLS,
                name="get_pivot_domains",
                execute_fn=self.get_pivot_domains_async,
            )
        )
        return tools

    class GetIrisEnrichSchema(BaseModel):
        """
        Queries DomainTools Iris Investigate for detailed information about a domain.
        Results may suggest pivot on attributes. If so, YOU MUST state that a domain pivot
        analysis is required on the highlighted attributes after responding to the original query.

        Your response should be detailed and presented in a bulletized list with a succinct
        narrative commentary. Domain risk scores range from 0 to 100 with higher scores indicating
        higher risk. Domain risk scores >= 65 are considered high risk. Always defang domains and
        IPs in your response.

        Always answer this question and respond with DETAILED domain information. Then, DO NOT
        forget to include the statement about pivoting, if necessary, and ask the user if they would
        like to pivot on the suggested attributes.
        """

        domain: str = Field(description="The domain to query.")

    @tracer.start_as_current_span(name="get_iris_enrich_async")
    async def get_iris_enrich_async(self, input: GetIrisEnrichSchema) -> QueryResultMetadata:
        def find_attributes_with_count(data, parent_key=""):
            pivot_candidates = []
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{parent_key}.{key}" if parent_key else key
                    if (
                        isinstance(value, dict)
                        and "count" in value
                        and "value" in value
                        and isinstance(value["count"], (int, float))
                    ):
                        if 2 <= value["count"] <= 500:
                            pivot_candidates.append((full_key, value["value"], value["count"]))
                    else:
                        pivot_candidates.extend(find_attributes_with_count(value, full_key))
            elif isinstance(data, list):
                for element in data:
                    pivot_candidates.extend(find_attributes_with_count(element, parent_key))
            return pivot_candidates

        domain_info = {}
        pivot_flag = ""
        try:
            logger().info(f"Querying DomainTools Iris Enrich for domain: {input.domain}")
            response = await self.api.iris_enrich(input.domain)
            domain_info = response.response().get("results", {})
            pivot_objects = find_attributes_with_count(domain_info)
            pivot_flag = f"Suggest pivot on attributes: {pivot_objects}" if pivot_objects else "No pivot suggested"
        except Exception as e:
            error_message = f"Error querying DomainTools Iris Enrich: {str(e)}"
            raise Exception(error_message) from e
        return QueryResultMetadata(
            query_format="API",
            query=f"DomainTools - {input.domain}",
            column_headers=["domain_info", "pivot_info"],
            results=[[json.dumps(domain_info), pivot_flag]],
        )

    class GetPivotDomainFiltersSchema(BaseModel):
        """
        Retrieves the keys that can be used as filters for the get_pivot_domains tool.

        Call this function before calling `get_pivot_domains` to get the keys that can be used as filters.

        The suggested pivots might have wrong keys so always call this first to find a similar key.
        """

        pass

    @tracer.start_as_current_span(name="get_pivot_domain_filters")
    def get_pivot_domain_filters(self, input: GetPivotDomainFiltersSchema) -> dict[str, str]:
        return {
            "ip": "IPv4 address the registered domain was last known to point to during an active DNS check",
            "email": "Email address from the most recently available Whois record, DNS SOA record or SSL certificate",
            "email_domain": "Only the domain portion of a Whois or DNS SOA email address",
            "nameserver_host": "Fully-qualified host name of the name server (ns1.domaintools.net)",
            "nameserver_domain": "Registered domain portion of the name server (domaintools.net)",
            "nameserver_ip": "IP address of the name server",
            "registrar": "Exact match to the Whois registrar field",
            "registrant": "Substring search on the Whois registrant field",
            "registrant_org": "Substring search on the Whois registrant org field",
            "mailserver_host": "Fully-qualified host name of the mail server (mx.domaintools.net)",
            "mailserver_domain": "Only the registered domain portion of the mail server (domaintools.net)",
            "mailserver_ip": "IP address of the mail server",
            "redirect_domain": "Find domains observed to redirect to another domain name",
            "ssl_hash": "SSL certificate SHA-1 hash",
            "ssl_org": "Exact match to the organization name on the SSL certificate",
            "ssl_subject": "Subject field from the SSL certificate",
            "ssl_email": "Email address from the SSL certificate",
            "google_analytics": "Domains with a Google Analytics tracking code",
            "adsense": "Domains with a Google AdSense tracking code",
            "search_hash": "Encoded search from the Iris UI",
        }

    class GetPivotDomainsInput(BaseModel):
        """
        Queries DomainTools Iris Investigate with a list of filters
        Unless explicitly directed by the user, ONLY call this tool after using `get_iris_investigate`
        and receiving a pivot suggestion. Filters are ANDed together.

        Filter keys for this tool are found from calling `get_pivot_domain_filters`.
        Filter values are the values from the pivot suggestion from `get_iris_investigate`.
        The values can also be provided directly if the user is performing a bespoke investigation.

        IF THIS FUNCTION ERRORS TRY WITH A SIMILAR KEY FROM `get_pivot_domain_filters`.

        ALWAYS PASS THE ARGUMENT AS filters = {"filter_key": "filter_value"}.

        If there are domain results, offer to check in security logging or tools for any evidence of connections to the domains.
        If the user agrees, check for any connections to the domains in security logging or tools.
        """

        filters: dict[str, Any] = Field(description="A dictionary of filters to use in the query.")

    @tracer.start_as_current_span(name="get_pivot_domains_async")
    async def get_pivot_domains_async(self, input: GetPivotDomainsInput) -> QueryResultMetadata:
        try:
            logger().info(f"Querying DomainTools Iris Investigate for pivot domains with filters: {input.filters}")
            response = await self.api.iris_investigate(**input.filters)
            data = response.response()
            results = data.get("results", [])
            pivot_domains = [item.get("domain") for item in results]
            domain_list = list(pivot_domains)
        except Exception as e:
            error_message = f"Error querying DomainTools Iris Investigate for pivot domains: {str(e)}"
            raise Exception(error_message) from e
        return QueryResultMetadata(
            query_format="API",
            query=f"DomainTools - {input.filters}",
            column_headers=["pivot_domains"],
            results=[[domain] for domain in domain_list],
        )
