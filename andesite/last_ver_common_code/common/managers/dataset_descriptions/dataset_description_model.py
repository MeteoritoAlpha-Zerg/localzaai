from typing import Any, Optional
from connectors.connector_id_enum import ConnectorIdEnum
from pydantic import BaseModel
from common.jsonlogging.jsonlogger import Logging


logger = Logging.get_logger("dataset-descriptions-model")


class UpsertDatasetDescription(BaseModel):
    path: list[str]
    description: Optional[str] = None


CSV_DELIMITER = ">>"


class DatasetDescription(BaseModel):
    connector: ConnectorIdEnum
    # Path to respective dataset being described
    path: list[str]
    description: str

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
