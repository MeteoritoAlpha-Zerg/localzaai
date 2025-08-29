# 5-test_service_request_details.py

async def test_service_request_details(zerg_state=None):
    """Test SysAid service request detail retrieval by way of connector tools"""
    print("Attempting to retrieve service request details using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    from connectors.sysaid.tools import SysAidConnectorTools, GetSysAidServiceRequestDetailsInput
    from connectors.sysaid.target import SysAidTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=sysaid_password,
    )
    assert isinstance(config, ConnectorConfig), "SysAidConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SysAidConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SysAidConnector should be of type Connector"

    # get query target options
    sysaid_query_target_options = await connector.get_query_target_options()
    assert isinstance(sysaid_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select service requests to target
    service_request_selector = None
    for selector in sysaid_query_target_options.selectors:
        if selector.type == 'service_request_ids':  
            service_request_selector = selector
            break

    assert service_request_selector, "failed to retrieve service request selector from query target options"

    assert isinstance(service_request_selector.values, list), "service_request_selector values must be a list"
    service_request_id = service_request_selector.values[0] if service_request_selector.values else None
    print(f"Selecting service request id: {service_request_id}")

    assert service_request_id, f"failed to retrieve service request id from service request selector"

    # set up the target with service request id
    target = SysAidTarget(service_request_ids=[service_request_id])
    assert isinstance(target, ConnectorTargetInterface), "SysAidTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_sysaid_service_request_details tool and execute it with service request id
    get_service_request_details_tool = next(tool for tool in tools if tool.name == "get_sysaid_service_request_details")
    service_request_details_result = await get_service_request_details_tool.execute(service_request_id=service_request_id)
    service_request_details = service_request_details_result.result

    print("Type of returned service_request_details:", type(service_request_details))
    print(f"service request details: {str(service_request_details)[:200]}")

    # Verify that service_request_details is a dict/object
    assert isinstance(service_request_details, dict), "service_request_details should be a dict"
    assert service_request_details, "service_request_details should not be empty"
    
    # Verify structure of the service request details object
    # Verify essential SysAid service request detail fields
    assert "id" in service_request_details, "Service request details should have an 'id' field"
    assert service_request_details["id"] == service_request_id, f"Service request id {service_request_details['id']} does not match requested service_request_id"
    
    # Verify common SysAid service request detail fields
    assert "title" in service_request_details, "Service request details should have a 'title' field"
    assert "status" in service_request_details, "Service request details should have a 'status' field"
    
    # Check for additional detailed fields that are typically available in service request details
    detailed_fields = ["description", "priority", "category", "subcategory", "requestUser", "assignedUser", "createDate", "modifyDate", "closeDate", "notes", "worklog", "attachments"]
    present_detailed = [field for field in detailed_fields if field in service_request_details]
    
    print(f"Service request {service_request_details['id']} contains these detailed fields: {', '.join(present_detailed)}")
    
    # Log the full structure for debugging
    print(f"Complete service request details structure: {service_request_details}")

    # Print some key information from the service request
    print(f"Retrieved details for service request: {service_request_id}")
    print(f"Title: {service_request_details.get('title')}")
    print(f"Status: {service_request_details.get('status')}")
    print(f"Priority: {service_request_details.get('priority')}")

    print(f"Successfully retrieved and validated service request details for SysAid service request {service_request_id}")

    return True