import json
import logging
import sys
import traceback
from collections.abc import Callable

from pydantic import BaseModel

from common.utils.context import (
    context_conversation_id,
    context_llm_model_id,
    context_mock_mode,
    context_request_id,
    context_request_method,
    context_request_path,
    context_user_id,
)

JSON_LOGGER_FORMAT_STR = (
    '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", '
    '"eventData": %(event_data)s, "trace": %(trace)s}'
)


class JsonLoggingFormatter(logging.Formatter):
    def __init__(self, fmt, default_event_data=None):
        super().__init__(fmt)
        self.default_event_data = default_event_data

    @staticmethod
    def escape_quotes(record):
        for attr in ["msg", "name", "levelname"]:
            value = getattr(record, attr, None)
            if value and isinstance(value, str):
                escaped_value = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                setattr(record, attr, escaped_value)

        record.args = tuple(
            arg.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") if isinstance(arg, str) else arg
            for arg in record.args
        )

    def __addTrace(self, record):
        trace_data = {
            "module": record.module,
            "filename": record.filename,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "process": record.process,
            "processName": record.processName,
            "thread": record.thread,
            "threadName": record.threadName,
        }

        if context_conversation_id.get():
            trace_data["conversation_id"] = context_conversation_id.get()
        if context_request_method.get():
            trace_data["method"] = context_request_method.get()
        if context_request_path.get():
            trace_data["path"] = context_request_path.get()

        trace_data["request_id"] = context_request_id.get()
        trace_data["user_id"] = context_user_id.get()
        trace_data["llm_id"] = context_llm_model_id.get()
        trace_data["mock_mode"] = context_mock_mode.get()

        record.trace = json.dumps(trace_data)

    def format(self, record):
        try:
            if isinstance(record.msg, BaseModel):
                record.msg = record.msg.model_dump()

            self.escape_quotes(record)

            self.__addTrace(record)

            if not hasattr(record, "event_data"):
                record.event_data = self.default_event_data

            if isinstance(record.event_data, BaseModel):
                record.event_data = record.event_data.model_dump()

            record.event_data = json.dumps(record.event_data, default=lambda o: getattr(o, "__dict__", str(o)))

        except Exception as e:
            print(f"Error formatting log record: {e}")
            traceback.print_exc()

        return super().format(record)

    def formatException(self, ei):
        type, msg, trace = ei
        tb_list = traceback.extract_tb(trace)
        formatted_traceback = []
        for filename, line_number, function_name, text in tb_list:
            formatted_traceback.append(
                {
                    "filename": filename,
                    "line_number": line_number,
                    "function_name": function_name,
                    "text": text,
                }
            )
        formatted_exception = {
            "type": type.__name__,
            "msg": str(msg),
            "stackTrace": formatted_traceback,
        }
        return json.dumps(formatted_exception)


def _get_json_logger(name: str, level: str | int) -> logging.Logger:
    logger = logging.getLogger(name)

    if not getattr(logger, "is_json_configured", False):
        if isinstance(level, str):
            level = _level_from_string(level)
        logger.setLevel(level)
        formatter = JsonLoggingFormatter(JSON_LOGGER_FORMAT_STR)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)
        logger.is_json_configured = True  # type: ignore[attr-defined]

    return logger


def _level_from_string(level_name: str):
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return log_levels.get(level_name.upper(), logging.INFO)


def to_str(data: object):
    return json.dumps(data, default=str)


class Logging:
    level: str | int = logging.INFO

    @classmethod
    def initialize(cls, level: str | int):
        cls.level = level

    @classmethod
    def get_logger(cls, name: str) -> Callable[[], logging.Logger]:
        # Provide a getter that we know will always return the latest class log level
        def getter():
            return _get_json_logger(name, cls.level)

        return getter
