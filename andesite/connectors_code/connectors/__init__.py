from opentelemetry.sdk.metrics._internal.aggregation import ExplicitBucketHistogramAggregation
from opentelemetry.sdk.metrics._internal.view import View

from common.opentelemetry.initializer import OpenTelemetryInitializer

OpenTelemetryInitializer.register_view([
    View(
        instrument_name="iterations_for_successful_react_query",
        aggregation=ExplicitBucketHistogramAggregation(list(range(1, 11))),
    )
])
