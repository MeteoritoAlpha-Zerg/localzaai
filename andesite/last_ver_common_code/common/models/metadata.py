from pydantic import BaseModel
from typing import Optional


class QueryResultMetadata(BaseModel):
    query_format: str
    query: str
    column_headers: Optional[list[str]]
    results: Optional[list[list[str]]]
