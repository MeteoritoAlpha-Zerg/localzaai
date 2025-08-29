from enum import Enum

from pydantic import BaseModel, Field

from common.models.metadata import QueryResultMetadata
from common.utils.context import context_experimental_chat
from common.utils.pydantic_helper import CamelModel


class ChatEventType(str, Enum):
    """
    ChatEventType defines the type of events a ReAct agent can emit during the reasoning loop.
    """

    action = "action"
    thought = "thought"
    observation = "observation"
    answer = "answer"
    error = "error"


class ChartType(str, Enum):
    bar = "bar"
    line = "line"
    scatter = "scatter"
    histogram = "histogram"


class Chart(BaseModel):
    chart_type: ChartType
    x: str
    y: list[str]
    is_timestamp: bool = False  # indicates if the x axis is a timestamp, so we dont need to validate on frontend


class ChatEvent(BaseModel):
    """
    ReActEvent defines the data model a ReAct agent emits for reasoning steps.
    """

    type: ChatEventType
    content: str
    metadata: QueryResultMetadata | None = None
    proposed_followups: list[str] | None = None
    connector_utilized: str | None = None
    id: str
    parent_id: str | None = None
    charts: list[Chart] | None = None


class ChatEventData(CamelModel):
    """
    ChatEventData defines the data that is logged for a chat event
    """

    conversation_id: str | None = ""
    conversation_message: ChatEvent
    user_query: str
    experimental_chat_enabled: bool = Field(default_factory=lambda: context_experimental_chat.get())
    document_id: str | None = ""
    message_id: str | None = ""
    parent_id: str | None = ""
