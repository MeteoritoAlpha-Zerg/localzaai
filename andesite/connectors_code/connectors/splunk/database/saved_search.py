from typing import Any
from pydantic import BaseModel, field_validator


class SplunkSavedSearch(BaseModel):
    name: str
    spl: str

    @field_validator("spl", mode="before")
    @classmethod
    def replace_single_quotes(cls, v: Any):
        return v.replace("'", '"')
