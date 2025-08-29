import json
import logging
import uuid
from contextvars import ContextVar
from typing import Optional, Union, overload
from opentelemetry import trace
from opentelemetry.trace import Span
from starlette.datastructures import Headers
from starlette.requests import Request
from common.opentelemetry.context import OpenTelemetryContext
from common.utils.timer import TotalAccess

tracer = trace.get_tracer(__name__)

TMessageAttributes = dict[str, dict[str, Optional[str]]]

context_request_id = ContextVar("request_id", default="unknown")
context_user_id = ContextVar("user_id", default="unknown")
context_request_path: ContextVar[Optional[str]] = ContextVar(
    "request_path", default=None
)
context_request_method: ContextVar[Optional[str]] = ContextVar(
    "request_method", default=None
)
context_request_timer: ContextVar[Optional[TotalAccess]] = ContextVar(
    "request_timer", default=None
)
context_token_count = ContextVar("token_count", default=0)
context_mock_mode = ContextVar("mock_mode", default=False)
context_llm_model_id: ContextVar[Optional[str]] = ContextVar("llm_model", default=None)
context_experimental_chat = ContextVar("experimental_chat", default=False)
context_experimental_document_processing = ContextVar(
    "experimental_document_processing", default=False
)


@overload
def get_header_value(
    headers: Headers, key: str, default: Optional[None] = None
) -> str | None: ...


@overload
def get_header_value(headers: Headers, key: str, default: str) -> str: ...


def get_header_value(
    headers: Headers, key: str, default: Union[str, Optional[None]] = None
):
    """
    Starlette overrides the __getitem__ implementation for headers to make their retrieval case insensitive

    This provides a safe (shouldn't throw) way to get a header's value w/ an optional default if the value doesn't exist
    """
    try:
        return headers[key]
    except KeyError:
        return default


def get_message_attributes_new() -> TMessageAttributes:
    message_attributes: TMessageAttributes = {
        "X-Request-Id": {"StringValue": str(uuid.uuid4()), "DataType": "String"},
    }
    return message_attributes


def get_message_attributes_from_context() -> TMessageAttributes:
    message_attributes: TMessageAttributes = {
        "X-Request-Id": {"StringValue": context_request_id.get(), "DataType": "String"},
        "X-User-ID": {"StringValue": context_user_id.get(), "DataType": "String"},
        "X-Mock-Mode": {
            "StringValue": str(context_mock_mode.get()),
            "DataType": "String",
        },
        "X-Experimental-Chat": {
            "StringValue": str(context_experimental_chat.get()),
            "DataType": "String",
        },
        "X-Experimental-Document-Processing": {
            "StringValue": str(context_experimental_document_processing.get()),
            "DataType": "String",
        },
    }

    if context_request_method.get():
        message_attributes["X-Request-Method"] = {
            "StringValue": context_request_method.get(),
            "DataType": "String",
        }
    if context_request_path.get():
        message_attributes["X-Request-Path"] = {
            "StringValue": context_request_path.get(),
            "DataType": "String",
        }
    if context_llm_model_id.get():
        message_attributes["X-LLM-ID"] = {
            "StringValue": context_llm_model_id.get(),
            "DataType": "String",
        }
    message_attributes["span-context"] = {
        "StringValue": json.dumps(OpenTelemetryContext.get_context_carrier()),
        "DataType": "Dict",
    }
    return message_attributes


def set_context_from_message_attributes(message_attributes: TMessageAttributes):
    context_llm_model_id.set(message_attributes.get("X-LLM-ID", {}).get("StringValue"))

    request_id = message_attributes.get("X-Request-Id", {}).get("StringValue")
    if not request_id:
        request_id = str(uuid.uuid4)

    context_request_id.set(request_id)
    context_request_path.set(
        message_attributes.get("X-Request-Path", {}).get("StringValue")
    )
    context_request_method.set(
        message_attributes.get("X-Request-Method", {}).get("StringValue")
    )

    user_id = message_attributes.get("X-User-ID", {}).get("StringValue")
    if not user_id:
        user_id = "unknown"
    context_user_id.set(user_id)

    context_mock_mode.set(
        message_attributes.get("X-Mock-Mode", {}).get("StringValue", "") == "True"
    )
    context_experimental_chat.set(
        message_attributes.get("X-Experimental-Chat", {}).get("StringValue", "")
        == "True"
    )
    context_experimental_document_processing.set(
        message_attributes.get("X-Experimental-Document-Processing", {}).get(
            "StringValue", ""
        )
        == "True"
    )


def with_context_from_message_attributes(func):
    """
    Decorator that sets context variables and trace propagation from `message_attributes` passed in through kwargs
    """

    def wrapper(*args, **kwargs):
        func_name = func.__name__

        ctx = None
        # add a request id if it doesn't exist (this happens when a scheduled task starts in processor)
        message_attributes = kwargs.get(
            "message_attributes", get_message_attributes_new()
        )
        if "message_attributes" in kwargs:
            # we do not want to pass message_attributes to the function to avoid them getting saved to the TaskMetadataManager
            del kwargs["message_attributes"]

        if not isinstance(message_attributes, dict):
            raise ValueError("message_attributes must be a dictionary")

        set_context_from_message_attributes(message_attributes)
        span_context = message_attributes.get("span-context", {}).get("StringValue")
        if span_context:
            ctx = OpenTelemetryContext.extract_context(json.loads(span_context))

        with tracer.start_as_current_span(func_name, context=ctx):
            return func(*args, **kwargs)

    return wrapper


def set_context_from_http_request(request: Request, logger: logging.Logger):
    """
    Sets relevant context variables from an http request. Throws if any mandatory values/headers are not present
    """
    context_request_path.set(request.scope.get("path", None))
    context_request_method.set(request.method)
    headers = request.headers
    request_id = get_header_value(headers, "X-Request-Id")
    if request_id is not None:
        context_request_id.set(request_id)
    if get_header_value(headers, "X-LLM-ID"):
        context_llm_model_id.set(get_header_value(headers, "X-LLM-ID"))
    if get_header_value(headers, "X-Mock-Mode", "false").strip().lower() == "true":
        context_mock_mode.set(True)

    if (
        get_header_value(headers, "X-Experimental-Chat", "false").strip().lower()
        == "true"
    ):
        context_experimental_chat.set(True)

    if (
        get_header_value(headers, "X-Experimental-Document-Processing", "false")
        .strip()
        .lower()
        == "true"
    ):
        context_experimental_document_processing.set(True)


def set_span_attributes(span: Span, message: dict):
    if span and span.is_recording():
        span.set_attribute("X-Request-Id", context_request_id.get())
        span.set_attribute("X-User-ID", context_user_id.get())
        span.set_attribute("X-Mock-Mode", context_mock_mode.get())
        span.set_attribute("X-Experimental-Chat", context_experimental_chat.get())
        span.set_attribute(
            "X-Experimental-Document-Processing",
            context_experimental_document_processing.get(),
        )
        if context_llm_model_id.get() is not None:
            span.set_attribute("X-LLM-ID", context_llm_model_id.get())  # type: ignore[arg-type]
        if context_request_method.get() is not None:
            span.set_attribute("X-Request-Method", context_request_method.get())  # type: ignore[arg-type]
        if context_request_path.get() is not None:
            span.set_attribute("X-Request-Path", context_request_path.get())  # type: ignore[arg-type]
