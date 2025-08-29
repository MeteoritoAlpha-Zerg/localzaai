from typing import Any
from enum import StrEnum
from datetime import datetime, timezone
from pydantic import BaseModel
from common.models.alerts import AbbreviatedAlert
from connectors.connector_id_enum import ConnectorIdEnum


class AlertReference(BaseModel):
    alert_id: str
    connector_id: ConnectorIdEnum

    model_config = {"use_enum_values": True}


class AlertGroupStatus(StrEnum):
    CLOSED = "closed"
    OPEN = "open"


class AlertGroup(BaseModel):
    """
    Represents a group of alerts with associated metadata and functionality for
    MongoDB serialization and deserialization.

    Attributes:
        id (str): Unique identifier for the alert group.
        title (str): Title of the alert group.
        status (AlertGroupStatus): Current status of the alert group. Defaults to AlertGroupStatus.OPEN.
        description (str): Description of the alert group.
        time (datetime): Timestamp associated with the alert group.
        priority (int): Priority level of the alert group.
        total_alerts_all_time (int): Total number of alerts associated with this group over time. We cannot get this from len(alerts) because they might be filtered out by time.
        alerts (list[AbbreviatedAlert]): List of abbreviated alert objects in the group.
        alert_ids (list[str]): List of alert IDs associated with the group.
        similarity_score (float): Similarity score for the alert group.
        explanation (str): Explanation or additional context for the alert group.

    Methods:
        to_mongo():
            Converts the AlertGroup instance into a dictionary suitable for MongoDB storage.

        from_mongo(document: Any) -> "AlertGroup | None":
            Creates an AlertGroup instance from a MongoDB document.

    Config:
        json_encoders (dict): Custom JSON encoders for specific data types, such as datetime.
    """

    id: str
    title: str
    status: AlertGroupStatus = AlertGroupStatus.OPEN
    description: str
    time: datetime
    priority: int
    total_alerts_all_time: int  # We cannot simply calculate len(alerts) because they might be filtered out by time and we still want to know the total the group holds
    alerts: list[AbbreviatedAlert]
    alert_ids: list[str]
    similarity_score: float
    explanation: str

    def to_mongo(self):
        model = self.model_dump(exclude={"id"})
        model["_id"] = self.id
        return model

    @staticmethod
    def from_mongo(document: Any) -> "AlertGroup | None":
        if document is not None:
            document["id"] = str(document.pop("_id", None))
            return AlertGroup(**document)

        return None

    class Config:
        json_encoders = {datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat()}


class AlertGroupDeleteResult(BaseModel):
    deleted_count: int
    total_count: int
