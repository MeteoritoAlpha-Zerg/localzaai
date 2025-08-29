from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    CANCELLED_BY_USER = "cancelled_by_user"
    FAILURE = "failure"
    DUPLICATE_REVOKED = "duplicate_revoked"


class Task(BaseModel):
    task_name: str
    args: dict[str, Any] | None = None


class TaskMetadata(Task, BaseModel):
    task_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING)

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "TaskMetadata | None":
        if document is not None:
            return TaskMetadata(**document)

        return None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})
