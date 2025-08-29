from opentelemetry.sdk.metrics._internal.aggregation import ExplicitBucketHistogramAggregation
from opentelemetry.sdk.metrics._internal.view import View

from common.opentelemetry.initializer import OpenTelemetryInitializer

_token_granularity = [0, 5, 10, 25, 50, 75, 100, 250, 500, *list(range(1000, 200_000, 500))]

OpenTelemetryInitializer.register_view(
    [
        View(
            instrument_name="llm_tokens_used_per_request",
            aggregation=ExplicitBucketHistogramAggregation(_token_granularity),
        ),
        View(
            instrument_name="input_llm_tokens_used_per_request",
            aggregation=ExplicitBucketHistogramAggregation(_token_granularity),
        ),
        View(
            instrument_name="output_llm_tokens_used_per_request",
            aggregation=ExplicitBucketHistogramAggregation(_token_granularity),
        ),
    ]
)
