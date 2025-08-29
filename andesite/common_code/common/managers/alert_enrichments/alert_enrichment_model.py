from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from common.models.connector_id_enum import ConnectorIdEnum
from common.models.conversation import Conversation


class AlertEnrichmentId(BaseModel):
    connector: ConnectorIdEnum | None
    id: str


class AlertAnomaly(BaseModel):
    anomaly_score: float = Field(ge=0, le=1)


class AlertInsightConnectorEnrichment(BaseModel):
    connector_id: ConnectorIdEnum
    conversation: Conversation


class AlertInsightActionItem(BaseModel):
    proposed_followup: str
    conversation: Conversation | None = None


class AlertInsight(BaseModel):
    time_created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    short_summary: str | None = None
    summary: str | None = None
    action_items: list[AlertInsightActionItem] = []
    connector_enrichments: list[AlertInsightConnectorEnrichment] = []

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class AlertEnrichment(AlertEnrichmentId):
    insight: AlertInsight | None = None
    anomaly_info: AlertAnomaly | None = None
    archived_at: datetime | None = None

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "AlertEnrichment | None":
        if document is not None:
            return AlertEnrichment(**document)

        return None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})
