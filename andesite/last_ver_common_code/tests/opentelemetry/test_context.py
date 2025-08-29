import unittest

from starlette.requests import Request
from starlette.datastructures import Headers
from opentelemetry.context.context import Context

from common.opentelemetry.context import OpenTelemetryContext


class OpenTelemetryContextTest(unittest.TestCase):
    def test_get_context_carrier(self):
        carrier = OpenTelemetryContext.get_context_carrier()
        self.assertIsInstance(carrier, dict)

    def test_set_context_from_headers(self):
        request = Request(
            {
                "type": "http",
                "path": "/",
                "headers": Headers({"traceparent": "12345"}).raw,
                "http_version": "1.1",
                "method": "GET",
                "scheme": "https",
                "client": ("127.0.0.1", 8080),
                "server": ("metamorph.com", 443),
            }
        )
        returned = OpenTelemetryContext.set_context_from_headers(request)
        assert returned is None

    def test_extract_context_from_headers(self):
        request = Request(
            {
                "type": "http",
                "path": "/",
                "headers": Headers({"traceparent": "12345"}).raw,
                "http_version": "1.1",
                "method": "GET",
                "scheme": "https",
                "client": ("127.0.0.1", 8080),
                "server": ("metamorph.com", 443),
            }
        )
        context = OpenTelemetryContext.extract_context_from_headers(request)
        self.assertIsInstance(context, Context)

    def test_set_context(self):
        carrier = {"traceparent": "12345"}
        returned = OpenTelemetryContext.set_context(carrier)
        assert returned is None

    def test_extract_context(self):
        carrier = {"traceparent": "12345"}
        context = OpenTelemetryContext.extract_context(carrier)
        self.assertIsInstance(context, Context)
