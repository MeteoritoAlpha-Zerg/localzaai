from enum import Enum


class ConnectorIdEnum(str, Enum):
    SPLUNK = "splunk"
    ATHENA = "athena"
    ELASTIC = "elastic"
    TENABLE = "tenable"
    EQUINOX = "equinox"
    TEAMS = "teams"
    SLACK = "slack"
    DISCORD = "discord"
    JIRA = "jira"
    DATABRICKS = "databricks"
    REMEDY = "remedy"
    REQUEST_TRACKER = "request_tracker"
    SERVICE_NOW = "service_now"
    SWIMLANE = "swimlane"
    CHRONICLE = "chronicle"
    SIEMPLIFY = "siemplify"
    CROWDSTRIKE = "crowdstrike"
    XSIAM = "xsiam"
    RAPID7 = "rapid7"
    SNOWFLAKE = "snowflake"
    SENTINEL_ONE = "sentinel_one"
    DOMAINTOOLS = "DomainTools"

    def __str__(self):
        return str(self.value)
