from typing import Any

from common.jsonlogging.jsonlogger import Logging
from core.framework import (
    BaseEventHandler,
    BaseEvent,
    LLMChatEndEvent,
    LLMChatStartEvent,
    LLMChatInProgressEvent,
    SpanDropEvent,
    StreamChatErrorEvent,
)

from pydantic import BaseModel

from common.engine.handlers.token_count_handler import TokenCountHandler


class _LogData(BaseModel):
    event_name: str
    event_id: str
    span_id: str
    payload: dict[str, Any] = {}
    kwargs: Any


def generic_json_serializer(obj):
    return getattr(obj, "__dict__", str(obj))


logger = Logging.get_logger(__name__)


class LlamaEventHandler(BaseEventHandler):
    """
    Event handler for Llama events.

    This class handles different types of Llama events (like start, end, in-progress) and logs relevant information.

    Args:
        BaseEventHandler: The base event handler class.

    Attributes:
        None

    Methods:
        handle: Handles the Llama event and logs relevant information.

    """

    def handle(self, event: BaseEvent, **kwargs: Any) -> None:
        """
        Handles the Llama event and logs relevant information like start and end of chats.

        Args:
            event (BaseEvent): The Llama event to handle.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None

        """

        if isinstance(event, LLMChatStartEvent):
            eventLog = _LogData(
                event_name="llama-index.event.start",
                event_id=str(event.id_),
                span_id=event.span_id or "",
                payload={
                    "messages": event.messages,
                    "additional_kwargs": event.additional_kwargs,
                    "model_dict": event.model_dict,
                },
                kwargs=kwargs,
            )
            logger().debug("LLM Event Start", extra={"event_data": eventLog})

        elif isinstance(event, StreamChatErrorEvent):
            eventLog = _LogData(
                event_name="llama-index.event.error.stream-chat",
                event_id=str(event.id_),
                span_id=event.span_id or "",
                payload={
                    "exception": event.exception,
                },
                kwargs=kwargs,
            )
            logger().error("LLM Exception", extra={"event_data": eventLog})

        elif isinstance(event, SpanDropEvent):
            eventLog = _LogData(
                event_name="llama-index.event.error.span-drop",
                event_id=str(event.id_),
                span_id=event.span_id or "",
                payload={
                    "err_str": event.err_str,
                },
                kwargs=kwargs,
            )
            logger().error("LLM Exception", extra={"event_data": eventLog})

        elif isinstance(event, LLMChatInProgressEvent):
            eventLog = _LogData(
                event_name="llama-index.event.in-progress",
                event_id=str(event.id_),
                span_id=event.span_id or "",
                payload={"messages": event.messages, "response": event.response},
                kwargs=kwargs,
            )
            logger().debug("LLM Event In Progress", extra={"event_data": eventLog})

        elif isinstance(event, LLMChatEndEvent):
            eventLog = _LogData(
                event_name="llama-index.event.end",
                event_id=str(event.id_),
                span_id=event.span_id or "",
                payload={"messages": event.messages, "response": event.response},
                kwargs=kwargs,
            )
            try:
                TokenCountHandler.add_to_token_count(
                    event.response.raw.usage.total_tokens  # type: ignore[union-attr]
                )
            except Exception as e:
                logger().exception("Exception while parsing token count: %s", str(e))
            logger().debug("LLM Event End", extra={"event_data": eventLog})
