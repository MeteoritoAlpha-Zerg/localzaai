from pydantic import BaseModel


class QueryResultMetadata(BaseModel):
    query_format: str
    query: str
    column_headers: list[str] | None
    results: list[list[str]] | None
