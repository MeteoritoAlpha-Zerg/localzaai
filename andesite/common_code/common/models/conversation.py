import enum
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from common.models.connectors import ConnectorScope
from common.models.context import ResourceReference
from common.models.metadata import QueryResultMetadata
from common.models.react import Chart, ChatEventType


def current_iso_time():
    return datetime.now(UTC).isoformat()


class MessageRole(str, enum.Enum):
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"
    SYSTEM = "system"
    ERROR = "error"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str = ""
    type: ChatEventType
    # This does not need to be super exact, so we will just consider creation time as the time when the message was sent
    timestamp: str = Field(default_factory=current_iso_time)
    metadata: QueryResultMetadata | None = None
    # The resources this chat message is referencing
    resources: list[ResourceReference] = []
    # The connectors and targets this chat message is referencing
    scopes: list[ConnectorScope] = []
    proposed_followups: list[str] | None = None
    connector_utilized: str | None = None
    parent_id: str | None = None
    charts: list[Chart] | None = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class ConversationReference(BaseModel):
    user_id: str
    conversation_id: str


class Conversation(ConversationReference, BaseModel):
    messages: list[ChatMessage]
