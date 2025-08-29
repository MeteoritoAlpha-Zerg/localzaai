# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing RSA Archer connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector
    from connectors.rsa_archer.target import RSAArcherTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name,
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    target = RSAArcherTarget()
    assert isinstance(target, ConnectorTargetInterface), "RSAArcherTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True