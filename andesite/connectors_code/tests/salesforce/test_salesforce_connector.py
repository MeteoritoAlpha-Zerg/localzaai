from unittest.mock import MagicMock, patch

from connectors.salesforce.connector.connector import SalesforceConnector, _get_tools


async def test_tools():
    SalesforceConnector.config = MagicMock()
    with (
        patch("connectors.salesforce.connector.tools.SalesforceConnectorTools.get_tools", MagicMock(return_value=[])),
        patch("connectors.salesforce.connector.connector._get_instance", MagicMock()),
    ):
        tools = _get_tools(MagicMock(), MagicMock(), None, None)
        assert tools == []
