import socket

import opentelemetry.sdk.resources as OpenTelemetrySDKResources
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.view import View
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from common.jsonlogging.jsonlogger import Logging
from common.opentelemetry.config import OpenTelemetryConfig
from common.opentelemetry.k8s_resource_detector import KubernetesEnvResourceDetector

logger = Logging.get_logger(__name__)


class OpenTelemetryInitializer:
    """
    Handles the initialization of OpenTelemetry instrumentation within a service.

    This class provides functionality to set up tracing and metrics providers
    for a service, leveraging configurations to determine the proper exporters,
    resources, and settings required. It facilitates OpenTelemetry's capability
    to instrument and generate telemetry data such as traces and metrics for
    observability purposes.

    :ivar config: The OpenTelemetryConfig object that determines how to configure Otel
    :ivar environment: The environment in which the service is running, such as development or production.
    :type environment: str
    :ivar stack_name: The name of the stack to which the service belongs.
    :type stack_name: str
    """

    _views: list[View] = []

    @classmethod
    def register_view(cls, views: list[View]):
        cls._views.extend(views)

    @classmethod
    def initialize(cls, config: OpenTelemetryConfig, service_name: str, service_version: str):
        logger().info("Instrumenting OpenTelemetry")

        if not config.otel_enabled:
            logger().info("OpenTelemetry is disabled, skipping instrumentation.")
            return

        resource = cls._get_base_resource(config, service_name, service_version)
        trace_provider = cls._init_trace_provider(config, resource)
        trace.set_tracer_provider(trace_provider)

        meter_provider = cls._init_meter_provider(config, resource, cls._views)
        metrics.set_meter_provider(meter_provider)

        logger().info("OpenTelemetry instrumentation complete")

    @staticmethod
    def _get_base_resource(
        config: OpenTelemetryConfig, service_name: str, service_version: str
    ) -> OpenTelemetrySDKResources.Resource:
        base_attributes: dict[str, OpenTelemetrySDKResources.LabelValue] = {
            OpenTelemetrySDKResources.SERVICE_NAMESPACE: "metamorph",
            OpenTelemetrySDKResources.SERVICE_NAME: service_name,
            OpenTelemetrySDKResources.SERVICE_VERSION: service_version,
            OpenTelemetrySDKResources.DEPLOYMENT_ENVIRONMENT: config.environment,
            OpenTelemetrySDKResources.HOST_NAME: socket.gethostname(),  # must be set and unique for traces (https://opentelemetry.io/docs/specs/semconv/registry/attributes/service/)
            "stack.name": config.stack_name,
        }

        base_resource = OpenTelemetrySDKResources.get_aggregated_resources(
            detectors=[
                OpenTelemetrySDKResources.OTELResourceDetector(),
                KubernetesEnvResourceDetector(),
            ],
            initial_resource=OpenTelemetrySDKResources.Resource(attributes=base_attributes),
        )
        return base_resource

    @staticmethod
    def _init_trace_provider(
        config: OpenTelemetryConfig, resource: OpenTelemetrySDKResources.Resource
    ) -> TracerProvider:
        trace_provider = TracerProvider(resource=resource)

        if config.otel_export_otlp_url:
            trace_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{config.otel_export_otlp_url}/v1/traces"))
            )

        if config.otel_export_console_enabled:
            trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        return trace_provider

    @staticmethod
    def _init_meter_provider(
        config: OpenTelemetryConfig, resource: OpenTelemetrySDKResources.Resource, views: list[View]
    ) -> MeterProvider:
        metric_readers = []

        if config.otel_export_otlp_url:
            metric_readers.append(
                PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{config.otel_export_otlp_url}/v1/metrics"))
            )

        if config.otel_export_console_enabled:
            metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))

        meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers, views=views)

        return meter_provider
