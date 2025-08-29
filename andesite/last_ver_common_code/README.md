# Common

Andesite Metamorph Utilities has been renamed Common, i.e. `common`.

The Common package is a library of tools and utilities for working within the Metamorph suite of
applications. This package is intended to be used as a dependency for other Metamorph applications and should not be used as a standalone application.

## OpenTelemetry
In order to instrument OpenTelemetry into a service, you must call `/common/opentelemetry/initialize.py initialize_open_telemetry` within application startup.

This will set up the exporter to Grafana as well as adding default attributes to be applied to your traces and metrics. The current default attributes are `service.namespace`, `service.name`, `deployment.environment`, `stack.name`, `k8s.pod.uid`,  `container.id`, `container.runtime`.

### Metrics
To create a [metric instrument](https://opentelemetry.io/docs/concepts/signals/metrics/#metric-instruments): (guage, counter, histogram, etc.)
```
from opentelemetry import metrics

meter = metrics.get_meter("document-processor") # Note that this name parameter essentially "prefixes" any metric

documents_in_queue_gauge = meter.create_gauge(
    "documents_in_queue_gauge", #this name, prefixed with the meter name must be unique
    description="Number of documents in the queue",
    unit="1",
)

documents_in_queue_gauge.set(5) # different types of metric instruments have different calls (histogram = "record", counter = "add", etc.)
```

Note that in order to record data to the same metric instrument your meter must share names. One example of this is within the `/engine/connectors/metrics.py` file where we define the meter for the whole folder as `connectors`.

### Traces
[Traces track the path of a request through your application. A path is divided up into spans (units of work).](https://opentelemetry.io/docs/concepts/signals/traces/) Each span has a parent span id. The root parent id is the trace id. In order to properly trace a request from system to system we must attach this context to every new span we want to track. This can be done automatically (within a service) or manually (between services).

In order to add tracing to your files, you must include the following at the type of file.
```
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
```

To instrument, you can place this above any function
```
@tracer.start_as_current_span("get_react_agent_tools")
def foo():
```

This will automatically grab the context of the caller and attach it to the span of foo's execution.

Context is not always propagated automatically, though. For example, calls between services (think: upload document in `backend` -> `processor` grabs that document) must have the trace context attached to it. You can use `OpenTelemetryContext.get_context_carrier(),` from `common` to grab the trace context. This will return a dictionary of "state" that should be attached to outgoing requests. There is a helper function for attaching this dictionary to an HTTP request as headers, for instance.

On the receiving service, if you must attach context manually, you can use
```
ctx = OpenTelemetryContext.extract_context(SPAN_CONTEXT) # The SPAN_CONTEXT is the same dictionary that we talked about above
with tracer.start_as_current_span("process_document", context=ctx):
    #code to be tracked here
```

For an example of this, see the call from `backend/app/routers/documents.py` to `processor/processor/document_processor.py`

#### FastApiInstrumentor
In `backend` we have an auto-instrumentor which starts traces for every route. Thus, there is no need to add `start_as_current_span` on functions which also have the decorators to indicate the initial point of entry for a route like `router.get()`.

This instrumentor also creates metrics for us like `http.server.duration` among others like request and response size.
```
def client_response_hook(span: Span, message: dict):
    set_span_attributes(span, message)


root_api = FastAPI(lifespan=lifespan)
initialize_open_telemetry(config, "backend")
FastAPIInstrumentor.instrument_app(root_api, excluded_urls="info/.*", client_response_hook=client_response_hook)
```

## Executing tests

```shell
poetry run pytest
```

### Running a Specific Test File:

If you want to run all tests in a specific file, provide the path to the test file after poetry run pytest. For example:

```bash
poetry run pytest tests/test_my_module.py
```

This command will run all tests in the test_my_module.py file.

### Running a Specific Test Function:

If you want to run a specific test function within a test file, you can append :: followed by the function name to the
file path. For example:

```bash
poetry run pytest tests/test_my_module.py::test_my_function
```

This will run only the test_my_function function in the test_my_module.py file.

### Calculating Test Coverage

To get a report of the current unit test coverage:

```bash
poetry run pytest --cov=common
```

This will exclude any files specified in the `tool.coverage.run` configuration.

To ingore any specific line from testing you can comment `# pragma: no cover` on the line.
