from unittest.mock import MagicMock, patch

from connectors.tenable.connector.connector import TenableConnector, _get_alert_enrichment_prompt, _get_tools


async def test_enrichment_prompt():
    TenableConnector.config = MagicMock()
    info = TenableConnector.get_info()
    assert info.can_enrich_alerts

    prompt = _get_alert_enrichment_prompt()
    assert isinstance(prompt, str)


async def test_tools():
    TenableConnector.config = MagicMock()
    with patch("connectors.tenable.connector.tools.TenableConnectorTools.get_tools", MagicMock(return_value=[])):
        tools = _get_tools(MagicMock(), MagicMock(), None, None)
        assert tools == []
