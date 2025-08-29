from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    DUPLICATE_REVOKED = "duplicate_revoked"


class Task(BaseModel):
    task_name: str
    args: Optional[dict[str, Any]] = None


class TaskMetadata(Task, BaseModel):
    task_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING)

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "TaskMetadata | None":
        if document is not None:
            return TaskMetadata(**document)

        return None

    class Config:
        json_encoders = {datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat()}
