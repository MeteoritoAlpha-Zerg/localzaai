from datetime import UTC
from enum import StrEnum, auto

from bson import ObjectId
from pydantic import BaseModel, ConfigDict

from common.base.types import UtcDatetime
from common.managers.alert_attributes.alert_attribute_model import AlertAttributeDb
from common.models.connector_id_enum import ConnectorIdEnum


class AlertAttributeContext(StrEnum):
    """
    AttributeContext represents the context in which an attribute weight is applied.
    """

    grouping = auto()


class AlertAttribute(BaseModel):
    """
    AttributeModel represents the model for a canonical attribute, including its mappings and context weights.
    """

    id: str
    attribute_name: str
    mappings: dict[ConnectorIdEnum, list[str]]
    context_weights: dict[AlertAttributeContext, float]
    created_at: UtcDatetime

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    def weight(self, context: AlertAttributeContext) -> float:
        """
        Returns the weight for a given context based on the context_weights dictionary.
        :param context: The context for which to retrieve the weight.
        :return: The weight as a float, or 0.0 if the context is not found.
        """
        return self.context_weights.get(context, 0.0)

    @staticmethod
    def from_db(document: AlertAttributeDb) -> "AlertAttribute":
        object_id: ObjectId = document.id
        context_weights = {AlertAttributeContext[k]: v for k, v in document.context_weights.items()}
        mappings = {ConnectorIdEnum[k.upper()]: v for k, v in document.mappings.items()}
        return AlertAttribute(
            id=str(object_id),
            attribute_name=document.attribute_name,
            mappings=mappings,
            context_weights=context_weights,
            created_at=object_id.generation_time.astimezone(tz=UTC),
        )

    def to_db(self) -> AlertAttributeDb:
        context_weights = {k.value: v for k, v in self.context_weights.items()}
        mappings = {k.value: v for k, v in self.mappings.items()}
        return AlertAttributeDb(
            id=ObjectId(self.id),
            attribute_name=self.attribute_name,
            mappings=mappings,
            context_weights=context_weights,
        )
