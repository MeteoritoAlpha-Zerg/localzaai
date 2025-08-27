from collections.abc import Callable
from typing import TypeVar

from pydantic import ValidationError

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)

C = TypeVar("C")


def fallback_none(model_builder: Callable[[], C]) -> C | None:
    """
    A helper function to fallback to None rather than throwing when validating pydantic models
    """
    try:
        return model_builder()
    except ValidationError:
        logger().exception("Could not instantiate connector configuration")
        return None
