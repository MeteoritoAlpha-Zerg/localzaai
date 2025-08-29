from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, computed_field

from common.managers.alert_enrichments.alert_enrichment_model import AlertEnrichment
from common.managers.alert_groups.alert_group_model import AlertGroup
from common.models.alerts import Alert
from common.models.context import ResourceTypeEnum
from common.models.document import DocumentStorageModel


class DocumentResource(BaseModel):
    document: DocumentStorageModel


class AlertResource(BaseModel):
    alert: Alert
    enrichment: AlertEnrichment | None = None


class AlertGroupResource(BaseModel):
    group: AlertGroup
    enrichment: AlertEnrichment | None = None
    raw_alerts: list[Alert]

    model_config = ConfigDict(extra="ignore")


RESOURCE_ID_NAMESPACE = UUID("d49a9351-ec3c-4eb5-bbbe-24c15b4f9c48")


def get_deterministic_uuid(input_text: str) -> str:
    """Generate a deterministic UUID based on the input text."""
    return str(uuid5(RESOURCE_ID_NAMESPACE, input_text))


class Resource(BaseModel):
    type: ResourceTypeEnum
    data: DocumentResource | AlertResource | AlertGroupResource

    @computed_field
    def resource_id(self) -> str:
        # If the resource id is different, then the whole resource will be sent to the LLM again
        # The resource id of the same resource should only change if the LLM needs to be updated with new context

        # For alert groups, anytime we add or remove an alert, or an enrichment gets updated by a workflow, the resource id needs to change so the LLM has updated context
        # For documents, anytime the document is updated as it is processed, the resource id needs to change so the LLM has updated context
        # For alerts, the resource id is based on the alert id and the enrichment id
        try:
            if isinstance(self.data, AlertGroupResource):
                return get_deterministic_uuid(
                    self.data.group.id + self.data.group.time_alerts_last_modified.isoformat() + self.data.enrichment.id
                    if self.data.enrichment
                    else ""
                )
            if isinstance(self.data, DocumentResource):
                return get_deterministic_uuid(
                    self.data.document.id + str(self.data.document.processing_progress_percent)
                )
            if isinstance(self.data, AlertResource):
                return get_deterministic_uuid(
                    self.data.alert.id + self.data.enrichment.id if self.data.enrichment else ""
                )
            return get_deterministic_uuid(self.data.model_dump_json())
        except Exception as e:
            raise ValueError("Data must be a json serializable Pydantic model") from e
