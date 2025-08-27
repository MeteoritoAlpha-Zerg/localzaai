from typing import Any

from pydantic import BaseModel, Field, model_validator

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum

logger = Logging.get_logger("dataset-descriptions-model")


class UpsertDatasetDescription(BaseModel):
    path: list[str]
    description: str | None = None


CSV_DELIMITER = ">>"


class DatasetDescriptionEnrichment(BaseModel):
    enriched_field_description: str | None = Field(default=None)
    examples: list[str] | None = Field(default=None)
    last_updated: str | None = Field(default=None)
    is_deprecated: bool | None = Field(default=None)
    usage_notes: str | None = Field(default=None)
    preferred_alternative: str | None = Field(default=None)
    top_fields: list[str] | None = Field(default=None)


class DatasetDescription(BaseModel):
    connector: ConnectorIdEnum
    # Path to respective dataset being described
    path: list[str]
    description: str
    enrichment: DatasetDescriptionEnrichment | None = Field(default=None)

    def to_mongo(self):
        dataset_description = self.model_dump()
        return dataset_description

    @staticmethod
    def from_mongo(document: Any) -> "DatasetDescription | None":
        if document is not None:
            return DatasetDescription(**document)

        return None

    @staticmethod
    def path_to_mongo_filter(path_prefix: list[str]) -> dict[str, str]:
        """
        Converts the path into a partial mongo filter that will return any paths starting with the provided prefix
        """
        filter: dict[str, str] = {}
        for i, el in enumerate(path_prefix):
            filter[f"path.{i}"] = el
        return filter

    @staticmethod
    def string_to_path(path_str: str) -> list[str]:
        """
        Splits a string into a path delimited by the CSV_DELIMITER
        """
        return path_str.split(CSV_DELIMITER)

    @model_validator(mode="before")
    def ensure_backward_compatible(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "enrichment" not in values:
            values["enrichment"] = None
        return values
