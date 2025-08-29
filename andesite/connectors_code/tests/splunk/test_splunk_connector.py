from unittest.mock import MagicMock, patch

from connectors.splunk.connector.connector import _get_tools


async def test_tools():
    with (
        patch("connectors.splunk.connector.connector._get_query_instance", MagicMock()),
        patch("connectors.splunk.connector.tools.SplunkConnectorTools.get_tools", MagicMock(return_value=[])),
    ):
        tools = _get_tools(MagicMock(), MagicMock(), None, None)
        assert tools == []
