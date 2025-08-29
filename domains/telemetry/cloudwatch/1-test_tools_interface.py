# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token").get("value")

    from connectors.cloudwatch.config import CloudwatchConnectorConfig
    from connectors.cloudwatch.connector import CloudwatchConnector
    from connectors.cloudwatch.target import CloudwatchTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = CloudwatchConnectorConfig(
        aws_region=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )
    assert isinstance(config, ConnectorConfig), "CloudwatchConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CloudwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CloudwatchConnector should be of type Connector"

    target = CloudwatchTarget()
    assert isinstance(target, ConnectorTargetInterface), "CloudwatchTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True