# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    elastic_url = zerg_state.get("elastic_url").get("value")
    elastic_api_key = zerg_state.get("elastic_api_key").get("value")
    elastic_username = zerg_state.get("elastic_username", {}).get("value")
    elastic_password = zerg_state.get("elastic_password", {}).get("value")

    from connectors.elastic.config import ElasticConnectorConfig
    from connectors.elastic.connector import ElasticConnector
    from connectors.elastic.target import ElasticTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config - prefer API key over username/password
    if elastic_api_key:
        config = ElasticConnectorConfig(
            url=elastic_url,
            api_key=elastic_api_key,
        )
    elif elastic_username and elastic_password:
        config = ElasticConnectorConfig(
            url=elastic_url,
            username=elastic_username,
            password=elastic_password,
        )
    else:
        raise Exception("Either elastic_api_key or both elastic_username and elastic_password must be provided")

    assert isinstance(config, ConnectorConfig), "ElasticConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ElasticConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ElasticConnector should be of type Connector"

    target = ElasticTarget()
    assert isinstance(target, ConnectorTargetInterface), "ElasticTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True