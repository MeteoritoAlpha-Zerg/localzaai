# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    databricks_workspace_url = zerg_state.get("databricks_workspace_url").get("value")
    databricks_access_token = zerg_state.get("databricks_access_token").get("value")
    databricks_cluster_id = zerg_state.get("databricks_cluster_id").get("value")

    from connectors.databricks.config import DatabricksConnectorConfig
    from connectors.databricks.connector import DatabricksConnector
    from connectors.databricks.target import DatabricksTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = DatabricksConnectorConfig(
        workspace_url=databricks_workspace_url,
        access_token=databricks_access_token,
        cluster_id=databricks_cluster_id,
    )
    assert isinstance(config, ConnectorConfig), "DatabricksConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DatabricksConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DatabricksConnector should be of type Connector"

    target = DatabricksTarget()
    assert isinstance(target, ConnectorTargetInterface), "DatabricksTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True