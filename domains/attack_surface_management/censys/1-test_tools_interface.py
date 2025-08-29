# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector
    from connectors.censys.target import CensysTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = CensysConnectorConfig(
        api_id=censys_api_id,
        api_secret=censys_api_secret,
        base_url=censys_base_url,
    )
    assert isinstance(config, ConnectorConfig), "CensysConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CensysConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CensysConnector should be of type Connector"

    target = CensysTarget()
    assert isinstance(target, ConnectorTargetInterface), "CensysTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True