from unittest.mock import MagicMock, patch

from connectors.proofpoint.connector.connector import _check_connection, _get_tools


async def test_check_connection():
    async def mock_fail(_):
        return False

    with patch(
        "connectors.proofpoint.client.proofpoint_instance.ProofpointInstance.check_connection_async",
        mock_fail,
    ):
        connected = await _check_connection(MagicMock(), MagicMock())
        assert not connected

    async def mock_success(_):
        return True

    with patch(
        "connectors.proofpoint.client.proofpoint_instance.ProofpointInstance.check_connection_async",
        mock_success,
    ):
        connected = await _check_connection(MagicMock(), MagicMock())
        assert connected


async def test_tools():
    with patch("connectors.proofpoint.connector.tools.ProofpointConnectorTools.get_tools", MagicMock(return_value=[])):
        tools = _get_tools(MagicMock(), MagicMock(), MagicMock(), None)
        assert tools == []
