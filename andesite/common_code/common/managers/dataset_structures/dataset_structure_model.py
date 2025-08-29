from typing import Any

from pydantic import BaseModel


class DatasetStructure(BaseModel):
    connector: str
    dataset: str
    attributes: Any

    def to_mongo(self):
        dataset_structure = self.model_dump()
        return dataset_structure

    @staticmethod
    def from_mongo(document: Any) -> "DatasetStructure | None":
        if document is not None:
            return DatasetStructure(**document)

        return None
