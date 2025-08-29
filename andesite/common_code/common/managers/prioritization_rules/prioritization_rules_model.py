from typing import Any

from pydantic import BaseModel, Field, field_validator


class PrioritizationRule(BaseModel):
    rule_name: str = Field(min_length=1)
    field_name: str
    field_regex: str
    priority_boost: float

    @field_validator("rule_name", mode="before")
    def validate_rule_name(cls, value: str) -> str:
        return value.strip()

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "PrioritizationRule | None":
        if document is not None:
            return PrioritizationRule(**document)

        return None
