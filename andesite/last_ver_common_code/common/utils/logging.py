from typing import Any, Optional
from common.jsonlogging.jsonlogger import Logging
from common.models.document import DocumentProcessingStep, DocumentProcessingStepData

logger = Logging.get_logger(__name__)


def log_document_processing_step(
    doc_id: str,
    type: DocumentProcessingStep,
    message: str,
    metadata: Optional[dict[str, Any]] = None,
):
    intermediateStepData = DocumentProcessingStepData(
        document_id=doc_id, type=type, metadata=metadata
    )
    logger().info(
        message,
        extra={"event_data": intermediateStepData},
    )
