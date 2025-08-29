# 4-test_list_collectors.py

async def test_list_collectors(zerg_state=None):
    """Test Sumo Logic collector and source enumeration by way of connector tools"""
    print("Attempting to authenticate using Sumo Logic connector")

    assert zerg_state, "this test requires valid zerg_state"

    sumologic_url = zerg_state.get("sumologic_url").get("value")
    sumologic_access_id = zerg_state.get("sumologic_access_id").get("value")
    sumologic_access_key = zerg_state.get("sumologic_access_key").get("value")

    from connectors.sumologic.config import SumoLogicConnectorConfig
    from connectors.sumologic.connector import SumoLogicConnector
    from connectors.sumologic.tools import SumoLogicConnectorTools
    from connectors.sumologic.target import SumoLogicTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = SumoLogicConnectorConfig(
        url=sumologic_url,
        access_id=sumologic_access_id,
        access_key=sumologic_access_key,
    )
    assert isinstance(config, ConnectorConfig), "SumoLogicConnectorConfig should be of type ConnectorConfig"

    connector = SumoLogicConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SumoLogicConnector should be of type Connector"

    sumologic_query_target_options = await connector.get_query_target_options()
    assert isinstance(sumologic_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    collector_selector = None
    for selector in sumologic_query_target_options.selectors:
        if selector.type == 'collector_ids':  
            collector_selector = selector
            break

    assert collector_selector, "failed to retrieve collector selector from query target options"

    num_collectors = 2
    assert isinstance(collector_selector.values, list), "collector_selector values must be a list"
    collector_ids = collector_selector.values[:num_collectors] if collector_selector.values else None
    print(f"Selecting collector IDs: {collector_ids}")

    assert collector_ids, f"failed to retrieve {num_collectors} collector IDs from collector selector"

    target = SumoLogicTarget(collector_ids=collector_ids)
    assert isinstance(target, ConnectorTargetInterface), "SumoLogicTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    sumologic_get_collectors_tool = next(tool for tool in tools if tool.name == "get_sumologic_collectors")
    sumologic_collectors_result = await sumologic_get_collectors_tool.execute()
    sumologic_collectors = sumologic_collectors_result.result

    print("Type of returned sumologic_collectors:", type(sumologic_collectors))
    print(f"len collectors: {len(sumologic_collectors)} collectors: {str(sumologic_collectors)[:200]}")

    assert isinstance(sumologic_collectors, list), "sumologic_collectors should be a list"
    assert len(sumologic_collectors) > 0, "sumologic_collectors should not be empty"
    assert len(sumologic_collectors) == num_collectors, f"sumologic_collectors should have {num_collectors} entries"
    
    for collector in sumologic_collectors:
        assert "id" in collector, "Each collector should have an 'id' field"
        assert collector["id"] in collector_ids, f"Collector ID {collector['id']} is not in the requested collector_ids"
        assert "name" in collector, "Each collector should have a 'name' field"
        assert "collectorType" in collector, "Each collector should have a 'collectorType' field"
        
        descriptive_fields = ["category", "hostName", "timeZone", "ephemeral", "sourceSyncMode"]
        present_fields = [field for field in descriptive_fields if field in collector]
        
        print(f"Collector {collector['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if collector == sumologic_collectors[0]:
            print(f"Example collector structure: {collector}")

    print(f"Successfully retrieved and validated {len(sumologic_collectors)} Sumo Logic collectors")

    return True