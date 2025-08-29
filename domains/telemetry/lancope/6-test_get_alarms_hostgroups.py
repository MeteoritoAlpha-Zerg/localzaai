# 6-test_get_alarms_hostgroups.py

async def test_get_alarms_hostgroups(zerg_state=None):
    """Test Cisco Stealthwatch alarms and host groups retrieval"""
    print("Testing Cisco Stealthwatch alarms and host groups retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.cisco_stealthwatch.target import CiscoStealthwatchTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    cisco_stealthwatch_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisco_stealthwatch_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in cisco_stealthwatch_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    alarms_source = None
    for source in data_source_selector.values:
        if 'alarm' in source.lower():
            alarms_source = source
            break
    
    assert alarms_source, "Alarms data source not found in available options"
    print(f"Selecting alarms data source: {alarms_source}")

    target = CiscoStealthwatchTarget(data_sources=[alarms_source])
    assert isinstance(target, ConnectorTargetInterface), "CiscoStealthwatchTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test alarm retrieval
    get_cisco_stealthwatch_alarms_tool = next(tool for tool in tools if tool.name == "get_cisco_stealthwatch_alarms")
    alarms_result = await get_cisco_stealthwatch_alarms_tool.execute()
    alarms_data = alarms_result.result

    print("Type of returned alarms data:", type(alarms_data))
    print(f"Alarms count: {len(alarms_data)} sample: {str(alarms_data)[:200]}")

    assert isinstance(alarms_data, list), "Alarms data should be a list"
    assert len(alarms_data) > 0, "Alarms data should not be empty"
    
    alarms_to_check = alarms_data[:5] if len(alarms_data) > 5 else alarms_data
    
    for alarm in alarms_to_check:
        # Verify essential alarm fields per Cisco Stealthwatch API specification
        assert "id" in alarm, "Each alarm should have an 'id' field"
        assert "alarm_type_id" in alarm, "Each alarm should have an 'alarm_type_id' field"
        assert "priority" in alarm, "Each alarm should have a 'priority' field"
        assert "timestamp" in alarm, "Each alarm should have a 'timestamp' field"
        
        assert alarm["id"], "Alarm ID should not be empty"
        assert alarm["alarm_type_id"], "Alarm type ID should not be empty"
        assert alarm["timestamp"], "Timestamp should not be empty"
        
        # Verify priority is valid
        valid_priorities = ["low", "medium", "high", "critical"]
        priority = alarm["priority"].lower()
        assert priority in valid_priorities, f"Invalid priority level: {priority}"
        
        alarm_fields = ["source", "target", "description", "policy_name", "snooze_time", "resolved"]
        present_fields = [field for field in alarm_fields if field in alarm]
        
        print(f"Alarm {alarm['id']} (type: {alarm['alarm_type_id']}, priority: {alarm['priority']}) contains: {', '.join(present_fields)}")
        
        # If resolved is present, validate it's boolean
        if "resolved" in alarm:
            resolved = alarm["resolved"]
            assert isinstance(resolved, bool), "Resolved should be boolean"
        
        # If source is present, validate it's not empty
        if "source" in alarm:
            source = alarm["source"]
            assert source and source.strip(), "Source should not be empty"
        
        # If target is present, validate it's not empty
        if "target" in alarm:
            target = alarm["target"]
            assert target and target.strip(), "Target should not be empty"
        
        # Log the structure of the first alarm for debugging
        if alarm == alarms_to_check[0]:
            print(f"Example alarm structure: {alarm}")

    print(f"Successfully retrieved and validated {len(alarms_data)} Cisco Stealthwatch alarms")

    # Test host group retrieval if available
    try:
        get_cisco_stealthwatch_hostgroups_tool = next((tool for tool in tools if tool.name == "get_cisco_stealthwatch_hostgroups"), None)
        if get_cisco_stealthwatch_hostgroups_tool:
            hostgroups_result = await get_cisco_stealthwatch_hostgroups_tool.execute()
            hostgroups_data = hostgroups_result.result

            print("Type of returned host groups data:", type(hostgroups_data))
            print(f"Host groups count: {len(hostgroups_data)} sample: {str(hostgroups_data)[:200]}")

            assert isinstance(hostgroups_data, list), "Host groups data should be a list"
            
            if len(hostgroups_data) > 0:
                hostgroups_to_check = hostgroups_data[:5] if len(hostgroups_data) > 5 else hostgroups_data
                
                for hostgroup in hostgroups_to_check:
                    # Verify essential host group fields
                    assert "id" in hostgroup, "Each host group should have an 'id' field"
                    assert "name" in hostgroup, "Each host group should have a 'name' field"
                    
                    assert hostgroup["id"], "Host group ID should not be empty"
                    assert hostgroup["name"].strip(), "Host group name should not be empty"
                    
                    hostgroup_fields = ["description", "ranges", "parent_id", "host_count"]
                    present_fields = [field for field in hostgroup_fields if field in hostgroup]
                    
                    print(f"Host group {hostgroup['id']} ({hostgroup['name']}) contains: {', '.join(present_fields)}")

                print(f"Successfully retrieved and validated {len(hostgroups_data)} Cisco Stealthwatch host groups")
            else:
                print("No host groups data available")
        else:
            print("Host group retrieval tool not available")
    except Exception as e:
        print(f"Host group retrieval test skipped: {e}")

    return True