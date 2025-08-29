from typing import Any
from pydantic import BaseModel, Field
from connectors.connector_id_enum import ConnectorIdEnum
from datetime import datetime, timezone
from common.models.conversation import Conversation


class AlertEnrichmentId(BaseModel):
    connector: ConnectorIdEnum
    id: str


class AlertEnrichmentConversation(BaseModel):
    connector_display_name: str
    conversation: Conversation


class AlertEnrichment(AlertEnrichmentId):
    time_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str | None = None
    proposed_followups: str | None = None
    connector_enrichments: list[AlertEnrichmentConversation] = []

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "AlertEnrichment | None":
        if document is not None:
            return AlertEnrichment(**document)

        return None

    class Config:
        json_encoders = {datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat()}
