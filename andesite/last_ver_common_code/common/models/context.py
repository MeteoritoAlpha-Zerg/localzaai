from enum import Enum
from typing import Any
from connectors.connector_id_enum import ConnectorIdEnum
from pydantic import BaseModel, model_validator


class ResourceTypeEnum(str, Enum):
    alert = "alert"
    document = "document"
    alert_group = "alert_group"


class ResourceReference(BaseModel):
    type: ResourceTypeEnum

    """
    A specific resource that a query references as context
    """
    resource_id: str
    """
    For an alert and alert group resource, we need to know what connector the alert is from
    """
    connector: ConnectorIdEnum | None = None
    """
    For an alert and alert group resource we must know the exact filter to query the alert connector for in order to find the alert
    """
    lookback: int | None = None

    @model_validator(mode="before")
    def migrate_event_to_alert(cls, values: dict[str, Any]) -> dict[str, Any]:
        type = values.get("type")
        if str(type) == "event":
            values["type"] = "alert"
        return values


"""
Resources that can be provided as context to the agent to query against
"""


class Resource(BaseModel):
    type: ResourceTypeEnum
    data: (
        dict[str, Any] | Any
    )  # TODO: transition off of dict and add Document, AlertGroup, and Alert models
