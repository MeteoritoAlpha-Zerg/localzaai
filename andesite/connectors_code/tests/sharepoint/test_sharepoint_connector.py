from unittest.mock import MagicMock, patch

from connectors.zendesk.connector.connector import ZendeskConnector, _get_tools


async def test_tools():
    ZendeskConnector.config = MagicMock()
    with patch("connectors.zendesk.connector.tools.ZendeskConnectorTools.get_tools", MagicMock(return_value=[])):
        tools = _get_tools(MagicMock(), MagicMock(), None, None)
        assert tools == []
