from unittest.mock import MagicMock, patch

from connectors.domaintools.connector.connector import DomainToolsConnector, _get_alert_enrichment_prompt, _get_tools


async def test_enrichment_prompt():
    DomainToolsConnector.config = MagicMock()
    info = DomainToolsConnector.get_info()
    assert info.can_enrich_alerts

    prompt = _get_alert_enrichment_prompt()
    assert isinstance(prompt, str)


async def test_tools():
    DomainToolsConnector.config = MagicMock()
    with patch(
        "connectors.domaintools.connector.tools.DomainToolsConnectorTools.get_tools", MagicMock(return_value=[])
    ):
        tools = _get_tools(MagicMock(), MagicMock(), MagicMock(), None)
        assert tools == []
