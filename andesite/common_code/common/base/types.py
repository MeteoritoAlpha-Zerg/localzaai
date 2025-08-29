from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, Field


def has_utc_timezone(datetime: AwareDatetime):
    if datetime.tzinfo != UTC:
        raise ValueError("Input should be in UTC timezone")
    return datetime


# Enforce UTC datetime storage
UtcDatetime = Annotated[
    AwareDatetime,  # Pydantic time that requires datetime with timezone
    AfterValidator(has_utc_timezone),
    Field(default_factory=lambda: datetime.now(UTC)),
]
