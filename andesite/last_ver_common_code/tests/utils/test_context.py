import unittest
from unittest.mock import MagicMock, patch

from opentelemetry.trace import Span
from starlette.datastructures import Headers
from starlette.requests import Request

from common.utils.context import (
    context_llm_model_id,
    context_mock_mode,
    context_request_id,
    context_request_method,
    context_request_path,
    context_user_id,
    set_context_from_http_request,
    set_context_from_message_attributes,
    set_span_attributes,
)


class CommonContextTest(unittest.TestCase):
    def test_set_context_from_message_attributes(self):
        message_attributes = {
            "X-Request-Id": {"StringValue": "12345", "DataType": "String"},
            "X-User-ID": {"StringValue": "67890", "DataType": "String"},
            "X-Request-Method": {"StringValue": "GET", "DataType": "String"},
            "X-Request-Path": {"StringValue": "/api", "DataType": "String"},
            "X-LLM-ID": {"StringValue": "abcde", "DataType": "String"},
            "X-Mock-Mode": {"StringValue": "True", "DataType": "String"},
        }
        set_context_from_message_attributes(message_attributes)

        self.assertEqual(context_request_id.get(), "12345")
        self.assertEqual(context_user_id.get(), "67890")
        self.assertEqual(context_request_method.get(), "GET")
        self.assertEqual(context_request_path.get(), "/api")
        self.assertEqual(context_llm_model_id.get(), "abcde")
        self.assertEqual(context_mock_mode.get(), True)

    def test_set_context_from_http_request(self):
        request = Request(
            {
                "type": "http",
                "path": "/",
                "headers": Headers(
                    {
                        "X-Request-Id": "12345",
                        "X-LLM-ID": "abcde",
                        "X-Mock-Mode": "true",
                    }
                ).raw,
                "http_version": "1.1",
                "method": "GET",
                "scheme": "https",
                "client": ("127.0.0.1", 8080),
                "server": ("metamorph.com", 443),
            }
        )
        set_context_from_http_request(request, MagicMock())

        self.assertEqual(context_request_path.get(), "/")
        self.assertEqual(context_request_method.get(), "GET")
        self.assertEqual(context_request_id.get(), "12345")
        # User id does not get set in context by this handler
        self.assertEqual(context_user_id.get(), "unknown")
        self.assertEqual(context_llm_model_id.get(), "abcde")
        self.assertEqual(context_mock_mode.get(), True)

    @patch("common.utils.context.context_request_id")
    @patch("common.utils.context.context_user_id")
    @patch("common.utils.context.context_llm_model_id")
    @patch("common.utils.context.context_mock_mode")
    def test_set_span_attributes(
        self,
        mock_context_mock_mode,
        mock_context_llm_model_id,
        mock_context_user_id,
        mock_context_request_id,
    ):
        mock_context_request_id.get.return_value = "12345"
        mock_context_user_id.get.return_value = "67890"
        mock_context_llm_model_id.get.return_value = "abcdef"
        mock_context_mock_mode.get.return_value = True

        span = MagicMock(spec=Span)
        span.is_recording.return_value = True

        set_span_attributes(span, {})

        span.set_attribute.assert_any_call("X-Request-Id", "12345")
        span.set_attribute.assert_any_call("X-User-ID", "67890")
        span.set_attribute.assert_any_call("X-LLM-ID", "abcdef")
        span.set_attribute.assert_any_call("X-Mock-Mode", True)
