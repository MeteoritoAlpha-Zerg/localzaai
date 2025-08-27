from abc import ABC, abstractmethod
from typing import Any

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class QueryInstance(ABC):
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        earliest: str | None = "-1h",
        latest: str | None = "now",
        limit: int | None = 100,
    ) -> list[dict[str, Any]]:
        pass

    @staticmethod
    @tracer.start_as_current_span("result_to_sparse_table")
    def result_to_sparse_table(
        result: list[dict[str, str]],
    ) -> tuple[list[str], list[list[str]]]:
        columns: dict[str, None] = {}
        for d in result:
            columns.update({key: None for key in d})

        column_keys = list(columns.keys())

        rows: list[list[str]] = []
        for d in result:
            row = [str(d.get(col, "")) for col in columns]
            rows.append(row)

        return column_keys, rows
