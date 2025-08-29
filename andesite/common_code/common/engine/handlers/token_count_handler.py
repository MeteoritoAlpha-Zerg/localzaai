from opentelemetry import metrics

from common.utils.context import (
    context_llm_model_id,
    context_token_count,
)

meter = metrics.get_meter(__name__)


class TokenCountHandler:
    tokens_used_histogram = meter.create_histogram(
        name="llm_tokens_used_per_request",
        description="Number of total tokens used for llm call",
        unit="1",
    )
    input_tokens_used_histogram = meter.create_histogram(
        name="input_llm_tokens_used_per_request",
        description="Number of input tokens used for llm call",
        unit="1",
    )
    output_tokens_used_histogram = meter.create_histogram(
        name="output_llm_tokens_used_per_request",
        description="Number of output tokens used for llm call",
        unit="1",
    )

    @staticmethod
    def add_to_token_count(token_count: int):
        current_token_count = context_token_count.get()
        context_token_count.set(current_token_count + token_count)

    @staticmethod
    def finalize_token_count(caller_context: str | None = None):
        model_id = context_llm_model_id.get()
        token_count = context_token_count.get()
        metadata = caller_context or "unknown_caller_context"

        if model_id is not None:
            TokenCountHandler.tokens_used_histogram.record(
                token_count,
                {"model_id": model_id, "caller_context": metadata},
            )

    @staticmethod
    def finalize_input_token_count(token_count: int, caller_context: str | None = None):
        model_id = context_llm_model_id.get()
        metadata = caller_context or "unknown_caller_context"

        if model_id is not None:
            TokenCountHandler.input_tokens_used_histogram.record(
                token_count,
                {"model_id": model_id, "caller_context": metadata},
            )

    @staticmethod
    def finalize_output_token_count(token_count: int, caller_context: str | None = None):
        model_id = context_llm_model_id.get()
        metadata = caller_context or "unknown_caller_context"

        if model_id is not None:
            TokenCountHandler.output_tokens_used_histogram.record(
                token_count,
                {"model_id": model_id, "caller_context": metadata},
            )
