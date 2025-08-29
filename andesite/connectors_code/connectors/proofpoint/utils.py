import datetime


def validate_ISO8601_interval(value: str) -> str:
    """
    Validates a provided interval adheres to expected ISO8601 format
    """
    try:
        start_str, end_str = value.split("/")
        datetime.datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%SZ")
        datetime.datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%SZ")
        return value
    except ValueError:
        raise ValueError("Invalid interval format. Expected 'YYYY-MM-DDTHH:MM:SSZ/YYYY-MM-DDTHH:MM:SSZ'.")


def round_time_down_to_nearest_increment(value: datetime.datetime, increment: int) -> datetime.datetime:
    """
    Rounds a datetime object down to the nearest specified increment in seconds.
    """
    if increment <= 0:
        raise ValueError("Increment must be a positive integer.")

    total_seconds = (value - datetime.datetime(1970, 1, 1)).total_seconds()
    rounded_seconds = (total_seconds // increment) * increment
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=rounded_seconds)


def round_time_up_to_nearest_increment(value: datetime.datetime, increment: int) -> datetime.datetime:
    """
    Rounds a datetime object up to the nearest specified increment in seconds.
    """
    if increment <= 0:
        raise ValueError("Increment must be a positive integer.")

    total_seconds = (value - datetime.datetime(1970, 1, 1)).total_seconds()
    rounded_seconds = ((total_seconds + increment - 1) // increment) * increment
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=rounded_seconds)


def interval_end_more_than_timedelta_ago(interval: str, timedelta: datetime.timedelta) -> bool:
    """Checks if the end of the provided interval is more than 24 hours ago from now."""
    _, end = interval.split("/")
    return (datetime.datetime.now() - datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")) > timedelta
