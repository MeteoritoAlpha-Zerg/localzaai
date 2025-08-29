# 7-test_get_incidents.py

async def test_get_incidents(zerg_state=None):
    """Test retrieving incidents from Microsoft Sentinel"""
    print("Attempting to retrieve incidents using Microsoft Sentinel connector")

    assert zerg_state, "this test requires valid zerg_state"

    azure_tenant_id = zerg_state.get("azure_tenant_id").get("value")
    client_id = zerg_state.get("client_id").get("value")
    client_secret = zerg_state.get("client_secret").get("value")
    subscription_id = zerg_state.get("subscription_id").get("value")
    resource_group = zerg_state.get("resource_group").get("value")

    from connectors.microsoft_sentinel.config import MicrosoftSentinelConnectorConfig
    from connectors.microsoft_sentinel.connector import MicrosoftSentinelConnector
    from connectors.microsoft_sentinel.tools import MicrosoftSentinelConnectorTools, GetIncidentsInput
    from connectors.microsoft_sentinel.target import MicrosoftSentinelTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = MicrosoftSentinelConnectorConfig(
        tenant_id=azure_tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        subscription_id=subscription_id,
        resource_group=resource_group,
    )
    assert isinstance(config, ConnectorConfig), "MicrosoftSentinelConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MicrosoftSentinelConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MicrosoftSentinelConnector should be of type Connector"

    # get query target options
    sentinel_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentinel_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select workspaces to target
    workspace_selector = None
    for selector in sentinel_query_target_options.selectors:
        if selector.type == 'workspace_names':  
            workspace_selector = selector
            break

    assert workspace_selector, "failed to retrieve workspace selector from query target options"

    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_name = workspace_selector.values[0] if workspace_selector.values else None
    print(f"Selecting workspace name: {workspace_name}")

    assert workspace_name, f"failed to retrieve workspace name from workspace selector"

    # set up the target with workspace names
    target = MicrosoftSentinelTarget(workspace_names=[workspace_name])
    assert isinstance(target, ConnectorTargetInterface), "MicrosoftSentinelTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_incidents tool and execute it with workspace name
    get_incidents_tool = next(tool for tool in tools if tool.name == "get_incidents")
    incidents_result = await get_incidents_tool.execute(workspace_name=workspace_name)
    incidents = incidents_result.result

    print("Type of returned incidents:", type(incidents))
    print(f"len incidents: {len(incidents)} incidents: {str(incidents)[:200]}")

    # Verify that incidents is a list
    assert isinstance(incidents, list), "incidents should be a list"
    # Note: Incidents can be empty if no security incidents exist, so we don't assert len > 0
    
    # If there are incidents, verify their structure
    if len(incidents) > 0:
        # Limit the number of incidents to check if there are many
        incidents_to_check = incidents[:5] if len(incidents) > 5 else incidents
        
        # Verify structure of each incident object
        for incident in incidents_to_check:
            # Verify essential Microsoft Sentinel incident fields
            assert "id" in incident, "Each incident should have an 'id' field"
            assert "name" in incident, "Each incident should have a 'name' field"
            
            # Check if incident belongs to the requested workspace
            # Azure resource IDs typically contain the workspace/resource group info
            incident_id = incident.get("id", "")
            if subscription_id in incident_id and resource_group in incident_id:
                print(f"Incident {incident.get('name')} belongs to the correct workspace")
            
            # Verify common Microsoft Sentinel incident fields
            assert "properties" in incident, "Each incident should have a 'properties' object"
            properties = incident["properties"]
            
            # Check for essential properties
            essential_fields = ["title", "severity", "status", "createdTimeUtc"]
            for field in essential_fields:
                assert field in properties, f"Incident properties should contain '{field}'"
            
            # Additional optional fields to check (if present)
            optional_fields = ["description", "owner", "labels", "firstActivityTimeUtc", "lastActivityTimeUtc", "incidentNumber"]
            present_optional = [field for field in optional_fields if field in properties]
            
            print(f"Incident {properties.get('title')} contains these optional fields: {', '.join(present_optional)}")
            
            # Verify severity is valid
            valid_severities = ["High", "Medium", "Low", "Informational"]
            severity = properties.get("severity")
            assert severity in valid_severities, f"Incident severity '{severity}' should be one of {valid_severities}"
            
            # Verify status is valid
            valid_statuses = ["New", "Active", "Closed"]
            status = properties.get("status")
            assert status in valid_statuses, f"Incident status '{status}' should be one of {valid_statuses}"
            
            # Log the structure of the first incident for debugging
            if incident == incidents_to_check[0]:
                print(f"Example incident structure: {incident}")

        print(f"Successfully retrieved and validated {len(incidents)} Microsoft Sentinel incidents")
        
        # Store first incident ID for potential use in other tests
        if hasattr(zerg_state, 'set'):
            first_incident_id = incidents[0].get("id")
            zerg_state.set('last_incident_id', first_incident_id)
            print(f"Stored incident ID for future tests: {first_incident_id}")
            
    else:
        print("No incidents found in workspace. This is normal if there are no active security incidents.")

    # Test with limited results to verify pagination works
    limited_incidents_result = await get_incidents_tool.execute(
        workspace_name=workspace_name,
        limit=3
    )
    limited_incidents = limited_incidents_result.result
    
    assert isinstance(limited_incidents, list), "limited incidents should be a list"
    if len(incidents) > 3:
        assert len(limited_incidents) <= 3, "limited query should return at most 3 incidents"
        print(f"Successfully tested incident limit functionality: requested 3, got {len(limited_incidents)}")
    else:
        print(f"Limited query returned {len(limited_incidents)} incidents (total available: {len(incidents)})")

    print(f"Successfully retrieved incidents from workspace {workspace_name}")

    return True