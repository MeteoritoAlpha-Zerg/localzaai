from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, TypeAdapter

from common.base.types import UtcDatetime


def test_datetime_no_tz():
    ta = TypeAdapter(UtcDatetime)
    with pytest.raises(ValueError, match="Input should have timezone info"):
        ta.validate_python(datetime.now())


def test_datetime_invalid_tz():
    ta = TypeAdapter(UtcDatetime)
    with pytest.raises(ValueError, match="Input should be in UTC timezone"):
        ta.validate_python(datetime.now(timezone(timedelta(hours=-5))))


def test_datetime_valid():
    ta = TypeAdapter(UtcDatetime)
    ta.validate_python(datetime.now(UTC))


class SomeModel(BaseModel):
    time_field: UtcDatetime


def test_default_factory():
    model = SomeModel()
    assert model.time_field


def test_serialization():
    current_time = datetime(2025, 4, 9, 23, 40, 30, tzinfo=UTC)
    model = SomeModel(time_field=current_time)
    assert model.model_dump_json() == '{"time_field":"2025-04-09T23:40:30Z"}'
    assert model.model_dump() == {"time_field": current_time}
