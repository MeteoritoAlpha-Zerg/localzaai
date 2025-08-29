from datetime import datetime, timezone
from typing import Optional, Union

from common.models.connectors import ConnectorScope
from common.models.context import ResourceReference
from common.models.metadata import QueryResultMetadata
from core.llms.types import LLMMessageType
from pydantic import BaseModel, Field
from uuid import uuid4


from common.models.react import Chart, ChatEventType, DocumentEventType


def current_iso_time():
    return datetime.now(timezone.utc).isoformat()


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: LLMMessageType
    content: str = ""
    type: Union[ChatEventType, DocumentEventType]
    # This does not need to be super exact, so we will just consider creation time as the time when the message was sent
    timestamp: str = Field(default_factory=current_iso_time)
    metadata: Optional[QueryResultMetadata] = None
    # The resources this chat message is referencing
    resources: list[ResourceReference] = []
    # The connectors and targets this chat message is referencing
    scopes: list[ConnectorScope] = []
    proposed_followups: Optional[list[str]] = None
    connector_utilized: Optional[str] = None
    parent_id: Optional[str] = None
    charts: Optional[list[Chart]] = None


class Conversation(BaseModel):
    user_id: str
    conversation_id: str
    messages: list[ChatMessage]
