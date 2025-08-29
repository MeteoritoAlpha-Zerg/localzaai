from typing import Any, Dict, List, Optional

from common.utils.pydantic_helper import CamelModel
from pydantic import BaseModel

from connectors.sentinel_one.connector.model.base import OptionalStr


class Pagination(CamelModel):
    total_items: int
    next_cursor: OptionalStr


class SentinelOneApiResponse[T](BaseModel):
    data: List[T]
    pagination: Optional[Pagination] = None
    errors: Optional[List[Dict[str, Any]]] = None
