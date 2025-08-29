from typing import Dict, Optional

import opentelemetry.sdk.resources as OpenTelemetrySDKResources

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation
from opentelemetry.sdk.metrics._internal.view import View

from opentelemetry_resourcedetector_docker import DockerResourceDetector
from opentelemetry_resourcedetector_kubernetes import KubernetesResourceDetector

from common.opentelemetry.constants import OpenTelemetryConstants
from common.opentelemetry.config import OpenTelemetryConfig
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


def is_enabled(config: OpenTelemetryConfig) -> bool:
    if not config.is_otel_enabled:
        logger().info(
            "IS_OTEL_ENABLED flag is set to false. OpenTelemetry instrumentation is disabled."
        )
        return False
    else:
        return True


def get_collector_url(config: OpenTelemetryConfig) -> str:
    collector_url: Optional[str] = None
    if config.grafana_alloy_url:
        collector_url = config.grafana_alloy_url.strip()

    if not collector_url:
        logger().info(
            "GRAFANA_ALLOY_URL is not configured. OpenTelemetry instrumentation is disabled."
        )
        return ""

    if collector_url.endswith("/"):
        collector_url = collector_url[:-1]

    return collector_url


def is_enabled_and_configured_correctly(config: OpenTelemetryConfig) -> bool:
    if not is_enabled(config):
        return False
    if not get_collector_url(config):
        return False
    return True


def initialize_open_telemetry(
    config: OpenTelemetryConfig, service_name: str, service_version: str
):
    logger().info("Instrumenting OpenTelemetry")
    if not is_enabled_and_configured_correctly(config):
        return

    collector_url: str = get_collector_url(config)

    base_attributes: Dict[str, OpenTelemetrySDKResources.LabelValue] = {
        OpenTelemetrySDKResources.SERVICE_NAMESPACE: "metamorph",
        OpenTelemetrySDKResources.SERVICE_NAME: service_name,
        OpenTelemetrySDKResources.SERVICE_VERSION: service_version,
    }
    base_attributes[OpenTelemetryConstants.STACK_NAME] = config.stack_name
    if isinstance(config.environment, (tuple, list)) and len(config.environment) > 0:
        base_attributes[OpenTelemetrySDKResources.DEPLOYMENT_ENVIRONMENT] = (
            config.environment[0]
        )
    else:
        base_attributes[OpenTelemetrySDKResources.DEPLOYMENT_ENVIRONMENT] = (
            config.environment
        )

    resource = OpenTelemetrySDKResources.Resource(attributes=base_attributes)

    resource = OpenTelemetrySDKResources.get_aggregated_resources(
        # attaches k8s.pod.uid, container.id, container.runtime as attributes
        detectors=[DockerResourceDetector(), KubernetesResourceDetector()],
        initial_resource=resource,
    )

    # traces
    trace_provider = TracerProvider(resource=resource)

    if config.is_otel_console_export_enabled:
        logger().debug(
            "IS_OTEL_CONSOLE_EXPORT_ENABLED flag is set to true. OpenTelemetry traces will be exported to the console."
        )
        processor = BatchSpanProcessor(ConsoleSpanExporter())
    else:
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{collector_url}/v1/traces")
        )
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

    # metrics
    if config.is_otel_console_export_enabled:
        logger().debug(
            "IS_OTEL_CONSOLE_EXPORT_ENABLED flag is set to true. OpenTelemetry metrics will be exported to the console."
        )
        reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    else:
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{collector_url}/v1/metrics")
        )
    meterProvider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
        views=[
            View(
                instrument_name="iterations_for_successful_react_query",
                aggregation=ExplicitBucketHistogramAggregation(
                    [i for i in range(1, 11)]
                ),
            ),
            View(
                instrument_name="llm_tokens_used_per_request",
                aggregation=ExplicitBucketHistogramAggregation(
                    [i for i in range(0, 200_000, 5000)]
                ),
            ),
            View(
                instrument_name="http.server.duration",
                aggregation=ExplicitBucketHistogramAggregation(
                    [
                        0.0,
                        5.0,
                        10.0,
                        25.0,
                        50.0,
                        75.0,
                        100.0,
                        250.0,
                        500.0,
                        750.0,
                        1000.0,
                        2500.0,
                        5000.0,
                        7500.0,
                        10000.0,
                        25000.0,
                        50000.0,
                        100000.0,
                    ]
                ),
            ),
        ],
    )
    metrics.set_meter_provider(meterProvider)
    logger().info("OpenTelemetry instrumentation complete")
