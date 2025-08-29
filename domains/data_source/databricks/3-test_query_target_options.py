# 3-test_query_target_options.py

async def test_schema_table_enumeration_options(zerg_state=None):
    """Test Databricks schema and table enumeration by way of query target options"""
    print("Attempting to authenticate using Databricks connector")

    assert zerg_state, "this test requires valid zerg_state"

    databricks_workspace_url = zerg_state.get("databricks_workspace_url").get("value")
    databricks_access_token = zerg_state.get("databricks_access_token").get("value")
    databricks_cluster_id = zerg_state.get("databricks_cluster_id").get("value")

    from connectors.databricks.config import DatabricksConnectorConfig
    from connectors.databricks.connector import DatabricksConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DatabricksConnectorConfig(
        workspace_url=databricks_workspace_url,
        access_token=databricks_access_token,
        cluster_id=databricks_cluster_id,
    )
    assert isinstance(config, ConnectorConfig), "DatabricksConnectorConfig should be of type ConnectorConfig"

    connector = DatabricksConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DatabricksConnector should be of type Connector"

    databricks_query_target_options = await connector.get_query_target_options()
    assert isinstance(databricks_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert databricks_query_target_options, "Failed to retrieve query target options"

    print(f"databricks query target option definitions: {databricks_query_target_options.definitions}")
    print(f"databricks query target option selectors: {databricks_query_target_options.selectors}")

    return True