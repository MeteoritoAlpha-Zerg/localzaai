from datetime import UTC, datetime
from enum import Enum, StrEnum, auto
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator

from common.models.base_model import BaseModelConfig
from common.models.connectors import ConnectorScope
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


class ProcessingErrorEnum(StrEnum):
    GENERIC = auto()
    ALERT_GENERATOR_CONFIG = auto()
    SCOPED_CONNECTORS_CONFIG = auto()
    USER_NOT_FOUND = auto()
    LLM_CONFIG = auto()
    CHUNKING = auto()
    RELEVANCY = auto()
    SUMMARY = auto()
    EXTRACT_IOCS = auto()
    GENERATE_QUESTIONS = auto()
    RUN_QUERIES = auto()
    DETERMINE_ANSWER_CONCERNING = auto()
    ASSESS_RISK = auto()
    GENERATE_RECOMMENDED_ACTIONS = auto()
    CREATE_ALERT = auto()


class RecommendationSourceEnum(StrEnum):
    DOCUMENT = auto()
    EXPLORATORY_SEARCH = auto()


class ExploratorySearch(BaseModel):
    conversation: Conversation | None = None
    raises_concern: bool | None = None
    raised_exception: bool = False
    lookback_days: int


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
    additional_context: str = ""


class Recommendation(BaseModel):
    source: RecommendationSourceEnum
    content: str


class DocumentBaseModel(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    comprehensive_summary: str | None = None
    single_sentence_summary: str | None = None
    file_name: str
    url: str | None = None  # URL if document was uploaded from a URL
    mime_type: str
    scopes: SerializeAsAny[list[ConnectorScope]] = Field(default=[])
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generated_prompts: list[GeneratedPrompt] | None = None
    exploratory_searches: list[ExploratorySearch | None] = []
    risk_score: RiskScoreEnum = Field(default=RiskScoreEnum.UNKNOWN)
    risk_assessment: str | None = None
    recommendations: list[Recommendation] | None = None
    processing_started_at: datetime | None = None  # Time at which processor picked up doc processing task
    processing_ended_at: datetime | None = None  # Time at which document processing was completed
    processing_error: ProcessingErrorEnum | None = None
    processing_status: ProcessingStatusEnum = Field(default=ProcessingStatusEnum.PENDING)
    processing_progress_percent: int = Field(default=0)
    iocs: list[IOCModel] | None = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})

    @field_validator("processing_error", mode="before")
    def _set_processing_error(cls, v):
        # this enables us to change the ProcessingErrorEnum values without worry about data migrations
        if isinstance(v, str):
            try:
                return ProcessingErrorEnum(v)
            except ValueError:
                return ProcessingErrorEnum.GENERIC
        return v


class DocumentStorageModel(DocumentBaseModel):
    s3_bucket: str
    s3_key: str
    llm_config: BaseModelConfig | None = None
    full_text: str | None = None
    checksum: str | None = None
    archived_at: datetime | None = None  # Documents are never deleted from mongo

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
    ioc_extraction = "ioc_extraction"
    prompt_generation = "prompt_generation"
    prompt_answer = "prompt_answer"
    parsing = "parsing"
    summary = "summary"
    success = "success"
    relevancy = "relevancy"
    risk_assesment = "risk_assesment"


class DocumentProcessingStepData(BaseModel):
    log_type: str = "document_processing_step"
    document_id: str
    type: DocumentProcessingStep
    metadata: dict[str, Any] | None = {}  # Allows any number of extra fields with any type of value
