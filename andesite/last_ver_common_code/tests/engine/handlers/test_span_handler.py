from common.engine.handlers.span_handler import LlamaSpanHandler, WrapperSpan


class TestLlamaSpanHandler:
    def test_new_span_without_parent_span_id(self):
        handler = LlamaSpanHandler()
        span_id = "span_id"
        bound_args = None
        instance = None

        span = handler.new_span(span_id, bound_args, instance)

        assert isinstance(span, WrapperSpan)
        assert span_id not in handler.open_spans
        assert span.id_ == span_id

    def test_new_span_with_parent_span_id(self):
        handler = LlamaSpanHandler()
        span_id = "span_id"
        parent_id = "parent_id"
        bound_args = None
        instance = None

        handler.new_span(parent_id, bound_args, instance)
        handler.span_enter(parent_id, bound_args=bound_args)
        span = handler.new_span(span_id, bound_args, instance, parent_span_id=parent_id)

        assert isinstance(span, WrapperSpan)
        assert span.id_ == span_id
        assert span.parent_id == parent_id

    def test_prepare_to_exit_span(self):
        handler = LlamaSpanHandler()
        span_id = "span_id"
        bound_args = None
        instance = None

        created_span = handler.new_span(span_id, bound_args, instance)
        handler.span_enter(span_id, bound_args, instance)
        exited_span = handler.prepare_to_exit_span(span_id, None)

        assert exited_span.id_ == created_span.id_

    def test_prepare_to_drop_span(self):
        handler = LlamaSpanHandler()
        span_id = "dropped_span"
        bound_args = None
        instance = None
        err = Exception("error")
        kwargs = {}

        span_created = handler.new_span(span_id, bound_args, instance)
        handler.span_enter(span_id, bound_args, instance)

        span_dropped = handler.prepare_to_drop_span(
            span_id, bound_args, instance, err, **kwargs
        )

        assert span_created.id_ == span_dropped.id_
