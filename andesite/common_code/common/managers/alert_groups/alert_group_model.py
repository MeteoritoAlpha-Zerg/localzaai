from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from common.models.alerts import AlertReference
from common.models.connector_id_enum import ConnectorIdEnum


class AlertGroupStatus(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    MIGRATED = "migrated"


class AlertGroup(BaseModel):
    """
    Represents a group of alerts with associated metadata and functionality for
    MongoDB serialization and deserialization.

    Attributes:
        id (str): Unique identifier for the alert group.
        title (str): Title of the alert group.
        status (AlertGroupStatus): Current status of the alert group. Defaults to AlertGroupStatus.OPEN.
        description (str): Short Description of the alert group.
        summary (str): Longer summary of the alert group.
        time (datetime): Timestamp associated with the alert group.
        priority (int): Priority level of the alert group.
        alerts (list[AbbreviatedAlert]): List of abbreviated alert objects in the group.
        similarity_score (float): Similarity score for the alert group.
        group_migrated_to (list[str]): List of alert groups to which this group has been migrated.

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
    summary: str
    time_created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    time_alerts_last_modified: datetime = Field(default_factory=lambda: datetime.now(UTC))
    alerts: list[AlertReference]
    similarity_score: float
    archived_at: datetime | None = None
    group_migrated_to: list[str] | None = None
    attribute_info: dict[ConnectorIdEnum, dict[str, str]] = Field(default_factory=dict)

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

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class AlertGroupDeleteResult(BaseModel):
    deleted_count: int
    total_count: int
