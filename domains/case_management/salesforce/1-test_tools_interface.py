# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector
    from connectors.salesforce.target import SalesforceTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    from common.models.tool import Tool

    # set up the config
    config = SalesforceConnectorConfig(
        username=salesforce_username,
        password=salesforce_password,
        security_token=salesforce_security_token,
        domain=salesforce_domain
    )
    assert isinstance(config, ConnectorConfig), "SalesforceConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SalesforceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SalesforceConnector should be of type Connector"

    target = SalesforceTarget()
    assert isinstance(target, ConnectorTargetInterface), "SalesforceTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True