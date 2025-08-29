from typing import Optional

from pydantic import BaseModel, field_validator


class SplunkSavedSearch(BaseModel):
    name: str
    spl: str
    description: str
    cron_schedule: str
    dispatchEarliestTime: str
    dispatchLatestTime: str
    path: Optional[str] = (
        None  # This is the path to the saved search in Splunk, not set until the search is created
    )

    @field_validator("spl", mode="before")
    @classmethod
    def replace_single_quotes(cls, v):
        return v.replace("'", '"')
