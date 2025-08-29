from typing import Any

from pydantic import BaseModel, Field

from common.models.connector_id_enum import ConnectorIdEnum


class ConnectorScope(BaseModel):  # pragma: no cover
    connector: ConnectorIdEnum
    target: dict[str, Any] = Field(
        default={},
        json_schema_extra={
            "additionalProperties": True,
        },
    )
