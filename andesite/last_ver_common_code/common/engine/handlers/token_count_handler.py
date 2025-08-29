from common.utils.context import (
    context_llm_model_id,
    context_token_count,
)
from opentelemetry import metrics

meter = metrics.get_meter(__name__)


class TokenCountHandler:
    tokens_used_histogram = meter.create_histogram(
        name="llm_tokens_used_per_request",
        description="Number of tokens used for llama index requests per API/doc/etc call",
        unit="1",
    )

    @staticmethod
    def add_to_token_count(token_count: int):
        current_token_count = context_token_count.get()
        context_token_count.set(current_token_count + token_count)

    @staticmethod
    def finalize_token_count():
        model_id = context_llm_model_id.get()
        token_count = context_token_count.get()

        if model_id is not None:
            TokenCountHandler.tokens_used_histogram.record(
                token_count,
                {"model_id": model_id},
            )
