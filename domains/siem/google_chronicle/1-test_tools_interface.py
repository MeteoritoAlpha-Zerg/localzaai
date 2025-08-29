# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Google Chronicle connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector
    from connectors.chronicle.target import ChronicleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id,
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    target = ChronicleTarget()
    assert isinstance(target, ConnectorTargetInterface), "ChronicleTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True