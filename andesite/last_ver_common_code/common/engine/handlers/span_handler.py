from typing import Any, Optional, cast
import inspect
from core.framework import (
    Field,
    SimpleSpanHandler,
    SimpleSpan,
)
from opentelemetry.trace import Span

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class WrapperSpan(SimpleSpan):
    open_tel_span: Span = Field()


class LlamaSpanHandler(SimpleSpanHandler):
    """
    A custom span handler that extends the SimpleSpanHandler class. This ties the spans created by llama index
    to open telemetry spans.
    """

    def new_span(
        self,
        id_: str,
        bound_args: inspect.BoundArguments,
        instance: Optional[Any] = None,
        parent_span_id: Optional[str] = None,
        tags: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> SimpleSpan:
        if parent_span_id and parent_span_id in self.open_spans:
            parent_span = self.open_spans[parent_span_id]
            parent_span = cast(WrapperSpan, parent_span)
            ctx = trace.set_span_in_context(parent_span.open_tel_span)
            span: Span = tracer.start_span(id_, context=ctx)
        else:
            ctx = trace.set_span_in_context(trace.get_current_span())
            span = tracer.start_span(id_, context=ctx)

        return WrapperSpan(id_=id_, parent_id=parent_span_id, open_tel_span=span)

    def prepare_to_exit_span(
        self,
        id_: str,
        bound_args: inspect.BoundArguments,
        instance: Optional[Any] = None,
        result: Optional[Any] = None,
        **kwargs: Any,
    ) -> SimpleSpan:
        span = self.open_spans[id_]
        span = cast(WrapperSpan, span)

        span.open_tel_span.set_attribute("result", str(result))
        span.open_tel_span.end()

        return SimpleSpanHandler.prepare_to_exit_span(
            self, id_, bound_args, instance, result, **kwargs
        )

    def prepare_to_drop_span(
        self,
        id_: str,
        bound_args: inspect.BoundArguments,
        instance: Optional[Any] = None,
        err: Optional[BaseException] = None,
        **kwargs: Any,
    ) -> SimpleSpan:
        if id_ in self.open_spans:
            span = self.open_spans[id_]
            span = cast(WrapperSpan, span)

            span.open_tel_span.set_attribute("error", str(err))
            span.open_tel_span.set_status(status=trace.StatusCode.ERROR)
            span.open_tel_span.end()

        return SimpleSpanHandler.prepare_to_drop_span(
            self, id_, bound_args, instance, err, **kwargs
        )  # type: ignore[return-value]
