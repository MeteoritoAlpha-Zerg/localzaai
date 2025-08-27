from opentelemetry import metrics

meter = metrics.get_meter("connectors")


class ConnectorMetrics:
    llm_queries_counter = meter.create_counter(
        name="llm_queries", description="Number of ReAct and oneshot queries", unit="1"
    )

    iterations_histogram = meter.create_histogram(
        name="iterations_for_successful_react_query",
        description="Number of iterations in successful React queries",
        unit="1",
    )

    connector_queries_counter = meter.create_counter(
        "connector_queries",
        unit="1",
        description="Number of queries to connectors pivoted on by connector name (splunk, athena, etc.)",
    )

    splunk_alerts_retrieval_latency = meter.create_histogram(
        name="splunk_alerts_retrieval_latency",
        description="Latency for how long the splunk query itself takes to retrieve alerts",
        unit="s",
    )
