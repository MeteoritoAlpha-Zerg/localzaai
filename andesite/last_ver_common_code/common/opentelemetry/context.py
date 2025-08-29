from typing import Optional, Dict
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry import context
from opentelemetry.context.context import Context
from starlette.requests import Request


class OpenTelemetryContext:
    @classmethod
    def get_context_carrier(cls) -> dict:
        """
        Injects the current context into a carrier. Use this within a span context.

        This function uses the `TraceContextTextMapPropagator` to inject the current context into a carrier.
        The carrier is a dictionary that will be modified with the necessary context information.

        Returns:
            dict: The modified carrier dictionary with the injected context information.
        """
        carrier: Dict[str, str] = {}
        TraceContextTextMapPropagator().inject(carrier)
        return carrier

    @classmethod
    def set_context_from_headers(cls, request: Request) -> None:
        """
        Sets the context from the headers of the given request.

        Args:
            request (Request): The incoming request object.

        Returns:
            None
        """
        traceparent = request.headers.get("traceparent")
        if traceparent:
            carrier = {"traceparent": traceparent}
        else:
            carrier = None
        cls.set_context(carrier)

    @classmethod
    def extract_context_from_headers(cls, request: Request) -> Context:
        """
        Extracts the context from the headers of the given request.

        Args:
            request (Request): The incoming request object.

        Returns:
            Context: The extracted context.
        """
        traceparent = request.headers.get("traceparent")
        if traceparent:
            carrier = {"traceparent": traceparent}
        else:
            carrier = None
        return cls.extract_context(carrier)

    @classmethod
    def set_context(cls, carrier: Optional[dict]) -> None:
        """
        Sets the context from the given carrier.

        Args:
            carrier (Optional[dict]): The carrier containing the trace context information. If not provided, an empty dictionary will be used.

        Returns:
            None
        """
        if carrier is None:
            carrier = {}
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        context.attach(ctx)

    @classmethod
    def extract_context(cls, carrier: Optional[dict]) -> Context:
        """
        Extracts the context from the given carrier.

        Args:
            carrier (Optional[dict]): The carrier containing the trace context information. If not provided, an empty dictionary will be used.

        Returns:
            Context: The extracted context.
        """
        if carrier is None:
            carrier = {}
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        return ctx
