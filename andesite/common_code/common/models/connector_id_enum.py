from enum import StrEnum, auto
from typing import Any, Literal

from pydantic import ValidationError


class ConnectorIdEnum(StrEnum):
    ARCHER = auto()
    ATHENA = auto()
    CLOUDWATCH = auto()
    CONFLUENCE = auto()
    CROWDSTRIKE = auto()
    DOMAINTOOLS = auto()
    ELASTIC = auto()
    GITHUB = auto()
    GUARDDUTY = auto()
    JIRA = auto()
    PROOFPOINT = auto()
    SALESFORCE = auto()
    SENTINEL_ONE = auto()
    SERVICE_NOW = auto()
    SHAREPOINT = auto()
    SNOWFLAKE = auto()
    SPLUNK = auto()
    TENABLE = auto()
    ZENDESK = auto()

    def __str__(self):
        return str(self.value)

    @classmethod
    def _missing_(cls, value: Any) -> "ConnectorIdEnum":
        """Fallback for unknown or alternative values"""
        if isinstance(value, str):
            # Migrate old domain tools value
            if value == "DomainTools":
                return ConnectorIdEnum.DOMAINTOOLS
            if value != value.lower():
                return ConnectorIdEnum(value.lower())
        raise ValueError(f"Unknown Connector Id: {value}")

    @staticmethod
    def safe_parse(value: Any) -> "ConnectorIdEnum | Literal[False]":
        """
        For a given value attempts to parse into a ConnectorId, and returns False if the value is unable to be parsed
        """
        try:
            return ConnectorIdEnum(value=value)
        except ValidationError:
            return False
        except ValueError:
            return False
