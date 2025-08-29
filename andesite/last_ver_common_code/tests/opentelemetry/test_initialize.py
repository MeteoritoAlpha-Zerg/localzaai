import unittest
from common.opentelemetry.config import OpenTelemetryConfig
from common.opentelemetry.initialize import is_enabled_and_configured_correctly


class OpenTelemetryInitializeTest(unittest.TestCase):
    def test_otel_enabled_false(self) -> None:
        config = OpenTelemetryConfig(is_otel_enabled=False)

        assert not is_enabled_and_configured_correctly(config)

    def test_grafana_alloy_url_not_configured(self) -> None:
        config = OpenTelemetryConfig(is_otel_enabled=True)
        assert not is_enabled_and_configured_correctly(config)

    def test_grafana_alloy_url_configured(self) -> None:
        config = OpenTelemetryConfig(
            is_otel_enabled=True, grafana_alloy_url="http://example.com"
        )

        assert is_enabled_and_configured_correctly(config)
