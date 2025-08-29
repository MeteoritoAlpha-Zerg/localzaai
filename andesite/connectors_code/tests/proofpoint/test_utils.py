import datetime

import pytest

from connectors.proofpoint.utils import (
    interval_end_more_than_timedelta_ago,
    round_time_down_to_nearest_increment,
    round_time_up_to_nearest_increment,
    validate_ISO8601_interval,
)


def test_validate_good_ISO8601_interval():
    interval = "2025-05-28T00:01:00Z/2025-05-28T00:02:10Z"
    assert validate_ISO8601_interval(interval) == interval


def test_validate_bad_ISO8601_interval():
    interval = "2025-05-28 00:01:00Z/2025-05-28 00:02:10Z"
    with pytest.raises(
        ValueError, match="Invalid interval format. Expected 'YYYY-MM-DDTHH:MM:SSZ/YYYY-MM-DDTHH:MM:SSZ'."
    ):
        validate_ISO8601_interval(interval)


def test_round_time_down_to_nearest_increment():
    date = datetime.datetime(year=2025, month=5, day=28, hour=7, minute=42, second=30)
    assert round_time_down_to_nearest_increment(date, 60) == datetime.datetime(
        year=2025, month=5, day=28, hour=7, minute=42, second=0
    )
    assert round_time_down_to_nearest_increment(date, 24 * 60 * 60) == datetime.datetime(
        year=2025, month=5, day=28, hour=0, minute=0, second=0
    )


def test_round_time_up_to_nearest_increment():
    date = datetime.datetime(year=2025, month=5, day=28, hour=7, minute=42, second=30)
    assert round_time_up_to_nearest_increment(date, 60) == datetime.datetime(
        year=2025, month=5, day=28, hour=7, minute=43, second=0
    )
    assert round_time_up_to_nearest_increment(date, 24 * 60 * 60) == datetime.datetime(
        year=2025, month=5, day=29, hour=0, minute=0, second=0
    )


def test_interval_end_more_than_timedelta_ago():
    interval = "1999-12-31T23:00:00Z/1999-12-31T23:59:59Z"
    assert interval_end_more_than_timedelta_ago(interval, datetime.timedelta(days=1))
    assert not interval_end_more_than_timedelta_ago(interval, datetime.timedelta(days=100 * 365))
