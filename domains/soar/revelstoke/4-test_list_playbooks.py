# 4-test_list_playbooks.py

async def test_list_playbooks(zerg_state=None):
    """Test Revelstoke SOAR playbook and case enumeration by way of connector tools"""
    print("Attempting to authenticate using Revelstoke SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    revelstoke_url = zerg_state.get("revelstoke_url").get("value")
    revelstoke_api_key = zerg_state.get("revelstoke_api_key", {}).get("value")
    revelstoke_username = zerg_state.get("revelstoke_username", {}).get("value")
    revelstoke_password = zerg_state.get("revelstoke_password", {}).get("value")
    revelstoke_tenant_id = zerg_state.get("revelstoke_tenant_id", {}).get("value")

    from connectors.revelstoke.config import RevelstokeSoarConnectorConfig
    from connectors.revelstoke.connector import RevelstokeSoarConnector
    from connectors.revelstoke.tools import RevelstokeSoarConnectorTools
    from connectors.revelstoke.target import RevelstokeSoarTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # prefer API key over username/password
    if revelstoke_api_key:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            api_key=revelstoke_api_key,
            tenant_id=revelstoke_tenant_id,
        )
    elif revelstoke_username and revelstoke_password:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            username=revelstoke_username,
            password=revelstoke_password,
            tenant_id=revelstoke_tenant_id,
        )
    else:
        raise Exception("Either revelstoke_api_key or both revelstoke_username and revelstoke_password must be provided")

    assert isinstance(config, ConnectorConfig), "RevelstokeSoarConnectorConfig should be of type ConnectorConfig"

    connector = RevelstokeSoarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RevelstokeSoarConnector should be of type Connector"

    revelstoke_query_target_options = await connector.get_query_target_options()
    assert isinstance(revelstoke_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    playbook_selector = None
    for selector in revelstoke_query_target_options.selectors:
        if selector.type == 'playbook_ids':  
            playbook_selector = selector
            break

    assert playbook_selector, "failed to retrieve playbook selector from query target options"

    num_playbooks = 2
    assert isinstance(playbook_selector.values, list), "playbook_selector values must be a list"
    playbook_ids = playbook_selector.values[:num_playbooks] if playbook_selector.values else None
    print(f"Selecting playbook IDs: {playbook_ids}")

    assert playbook_ids, f"failed to retrieve {num_playbooks} playbook IDs from playbook selector"

    target = RevelstokeSoarTarget(playbook_ids=playbook_ids)
    assert isinstance(target, ConnectorTargetInterface), "RevelstokeSoarTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    revelstoke_get_playbooks_tool = next(tool for tool in tools if tool.name == "get_revelstoke_playbooks")
    revelstoke_playbooks_result = await revelstoke_get_playbooks_tool.execute()
    revelstoke_playbooks = revelstoke_playbooks_result.result

    print("Type of returned revelstoke_playbooks:", type(revelstoke_playbooks))
    print(f"len playbooks: {len(revelstoke_playbooks)} playbooks: {str(revelstoke_playbooks)[:200]}")

    assert isinstance(revelstoke_playbooks, list), "revelstoke_playbooks should be a list"
    assert len(revelstoke_playbooks) > 0, "revelstoke_playbooks should not be empty"
    assert len(revelstoke_playbooks) == num_playbooks, f"revelstoke_playbooks should have {num_playbooks} entries"
    
    for playbook in revelstoke_playbooks:
        assert "id" in playbook, "Each playbook should have an 'id' field"
        assert playbook["id"] in playbook_ids, f"Playbook ID {playbook['id']} is not in the requested playbook_ids"
        assert "name" in playbook, "Each playbook should have a 'name' field"
        assert "status" in playbook, "Each playbook should have a 'status' field"
        
        descriptive_fields = ["description", "category", "created_by", "modified_at", "version", "enabled"]
        present_fields = [field for field in descriptive_fields if field in playbook]
        
        print(f"Playbook {playbook['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if playbook == revelstoke_playbooks[0]:
            print(f"Example playbook structure: {playbook}")

    print(f"Successfully retrieved and validated {len(revelstoke_playbooks)} Revelstoke SOAR playbooks")

    return True