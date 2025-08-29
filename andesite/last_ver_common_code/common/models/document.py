from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from bson import ObjectId

from common.models.connectors import ConnectorScope

from pydantic import BaseModel, Field, SerializeAsAny, field_validator

from common.models.base_model import BaseModelConfig
from common.models.conversation import Conversation


class RiskScoreEnum(str, Enum):
    UNKNOWN = "unknown"
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExploratorySearch(BaseModel):
    conversation: Optional[Conversation] = None
    raises_concern: Optional[bool] = None
    raised_exception: bool = False


class IOCModel(BaseModel):
    indicator_name: str
    type: str
    value: str
    description: str

    @field_validator("value", mode="before")
    @classmethod
    def convert_list_to_string(cls, v):
        if isinstance(v, list):
            return ", ".join(map(str, v))
        return str(v)


class GeneratedPrompt(BaseModel):
    id: str
    question: str


class DocumentBaseModel(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    summary: Optional[str] = None
    file_name: str
    mime_type: str
    scopes: SerializeAsAny[list[ConnectorScope]] = Field(default=[])
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generated_prompts: Optional[list[GeneratedPrompt]] = None
    exploratory_searches: list[Optional[ExploratorySearch]] = []
    risk_score: RiskScoreEnum = Field(default=RiskScoreEnum.UNKNOWN)
    risk_assessment: Optional[str] = None
    recommended_actions: Optional[list[str]] = None
    processing_started_at: Optional[datetime] = (
        None  # Time at which document processing was started
    )
    processing_ended_at: Optional[datetime] = (
        None  # Time at which document processing was completed
    )
    processing_errors: Optional[list[str]] = None
    processing_status: ProcessingStatusEnum = Field(
        default=ProcessingStatusEnum.PENDING
    )
    processing_progress_percent: int = Field(default=0)
    llm_config: Optional[BaseModelConfig] = None
    iocs: Optional[list[IOCModel]] = None
    processing_conversation: Optional[Conversation] = (
        None  # Filled with messages for document processing
    )

    class Config:
        json_encoders = {datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat()}


class DocumentStorageModel(DocumentBaseModel):
    s3_bucket: str
    s3_key: str
    checksum: Optional[str] = None
    archived_at: Optional[datetime] = None  # Documents are never deleted from mongo

    def to_mongo(self):
        document = self.model_dump()
        del document["id"]
        document["_id"] = ObjectId(self.id)
        return document

    @staticmethod
    def from_mongo(document):
        if document is not None:
            document["id"] = str(document.pop("_id", None))
            return DocumentStorageModel(**document)

        return None


class DocumentProcessingStep(str, Enum):
    llm_config = "llm_config"
    connector = "connector"
    prompt_generation = "prompt_generation"
    prompt_answer = "prompt_answer"
    chunking = "chunking"
    success = "success"
    relevancy = "relevancy"
    risk_assesment = "risk_assesment"


class DocumentProcessingStepData(BaseModel):
    log_type: str = "document_processing_step"
    document_id: str
    type: DocumentProcessingStep
    metadata: Optional[
        dict[str, Any]
    ] = {}  # Allows any number of extra fields with any type of value
