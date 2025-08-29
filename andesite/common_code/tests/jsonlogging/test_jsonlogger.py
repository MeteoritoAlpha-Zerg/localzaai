import io
import json
import logging
import unittest

from common.jsonlogging.jsonlogger import (
    JSON_LOGGER_FORMAT_STR,
    JsonLoggingFormatter,
    Logging,
)


class LoggingHelperTest(unittest.TestCase):
    @staticmethod
    def setup_test_logger(name: str) -> tuple[logging.Logger, io.StringIO]:
        Logging.initialize("DEBUG")
        logger_getter = Logging.get_logger(name)
        logger = logger_getter()
        log_output = io.StringIO()
        handler = logging.StreamHandler(log_output)
        formatter = JsonLoggingFormatter(JSON_LOGGER_FORMAT_STR)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger, log_output

    def test_log(self):
        logger, log_output = self.setup_test_logger("test")
        logger.info("test log")
        log = json.loads(log_output.getvalue())

        assert log["level"] == "INFO"
        assert log["name"] == "test"
        assert log["message"] == "test log"
        assert log["eventData"] == "null"

    def test_log_error(self):
        logger, log_output = self.setup_test_logger("test error")
        logger.error("test error message")
        log = json.loads(log_output.getvalue())

        assert log["level"] == "ERROR"
        assert log["name"] == "test error"
        assert log["message"] == "test error message"
        assert log["eventData"] == "null"

    def test_escaping(self):
        logger, log_output = self.setup_test_logger("test escaping")
        logger.info("I'm testing the \"escaping\" of 'quotes' and \\backslashes\\")
        log = json.loads(log_output.getvalue())

        assert log["message"] == "I'm testing the \\\"escaping\\\" of 'quotes' and \\\\backslashes\\\\"

    def test_escaping_custom_message(self):
        logger, log_output = self.setup_test_logger("spl-query")
        spl = 'search index=main (dest_ip:"137" OR dest_ip:"139" OR dest_ip:"445") sourcetype!=*sysmon src_ip!*=*localhost* src_ip!*=*127.0.0.1* | table _time, src_ip, dest_ip'
        response = []
        logger.info(
            "Splunk query (%s) produced %d results: %s...",
            spl,
            len(response),
            str(response[:1]),
        )

        log = json.loads(log_output.getvalue())
        assert (
            log["message"]
            == 'Splunk query (search index=main (dest_ip:\\"137\\" OR dest_ip:\\"139\\" OR dest_ip:\\"445\\") sourcetype!=*sysmon src_ip!*=*localhost* src_ip!*=*127.0.0.1* | table _time, src_ip, dest_ip) produced 0 results: []...'
        )

    def test_escaping_newlines(self):
        logger, log_output = self.setup_test_logger("newlines")
        logger.info("I'm testing\nnewlines")

        log = json.loads(log_output.getvalue())
        assert log["message"] == "I'm testing\\nnewlines"

    def test_logging_json(self):
        logger, log_output = self.setup_test_logger("json")
        response = """
        {
            "question": "Please verify if any SMB connections were made outbound in the last 7 days.",
            "spl_query": "index=main sourcetype=* (dest_port=139 OR dest_port=445) AND dest_ip:* ORDER BY _time DESC",
            "spl_start": "-7d",
            "spl_end": "now",
            "spl_explanation": "This query searches for events with dest_port as 139 or 445 (common SMB ports) in the 'main' index. It includes both IPv4 and IPv6 addresses. The results are ordered by timestamp in descending order to show the most recent events first."
            "spl_result": "... | eventtype=zeek_conn dest_port=139 dest_ip="10.17.4.2" src_ip="1.134.179.127" | eventtype=zeek_conn dest_port=445 dest_ip="10.17.4.2" src_ip="1.134.179.127" | ...",
            "answer": "Yes, there were SMB connections made outbound in the last 7 days. The specific IP addresses and other details can be found in the splResult."
        }
        """
        logger.error("Error parsing JSON response from LLM. Response was %s", response)

        log = json.loads(log_output.getvalue())
        assert "Error parsing JSON response from LLM. Response was \\n" in log["message"]

    def test_exception(self):
        logger, log_output = self.setup_test_logger("exception")
        try:
            raise ValueError("This is a test exception")
        except ValueError as e:
            logger.exception("An exception was encountered: %s", e)

        first_line = log_output.getvalue().split("\n")[0]
        log = json.loads(first_line)
        assert log["message"] == "An exception was encountered: This is a test exception"
