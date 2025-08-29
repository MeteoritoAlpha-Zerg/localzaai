from enum import Enum
from typing import Any

from pydantic import BaseModel, model_validator

from common.models.connector_id_enum import ConnectorIdEnum


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
    For an alert resource, we need to know what connector the alert is from
    """
    connector: ConnectorIdEnum | None = None

    @model_validator(mode="before")
    def migrate_event_to_alert(cls, values: dict[str, Any]) -> dict[str, Any]:
        type = values.get("type")
        if str(type) == "event":
            values["type"] = "alert"
        return values
