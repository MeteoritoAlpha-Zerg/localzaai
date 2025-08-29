# 4-test_list_service_requests.py

async def test_list_service_requests(zerg_state=None):
    """Test SysAid service request enumeration by way of connector tools"""
    print("Attempting to authenticate using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    from connectors.sysaid.tools import SysAidConnectorTools
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

    # grab the first two service requests 
    num_service_requests = 2
    assert isinstance(service_request_selector.values, list), "service_request_selector values must be a list"
    service_request_ids = service_request_selector.values[:num_service_requests] if service_request_selector.values else None
    print(f"Selecting service request ids: {service_request_ids}")

    assert service_request_ids, f"failed to retrieve {num_service_requests} service request ids from service request selector"

    # set up the target with service request ids
    target = SysAidTarget(service_request_ids=service_request_ids)
    assert isinstance(target, ConnectorTargetInterface), "SysAidTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_sysaid_service_requests tool
    sysaid_get_service_requests_tool = next(tool for tool in tools if tool.name == "get_sysaid_service_requests")
    sysaid_service_requests_result = await sysaid_get_service_requests_tool.execute()
    sysaid_service_requests = sysaid_service_requests_result.result

    print("Type of returned sysaid_service_requests:", type(sysaid_service_requests))
    print(f"len service_requests: {len(sysaid_service_requests)} service_requests: {str(sysaid_service_requests)[:200]}")

    # ensure that sysaid_service_requests are a list of objects with the id being the service request id
    # and the object having the service request description and other relevant information from the sysaid specification
    # as may be descriptive
    # Verify that sysaid_service_requests is a list
    assert isinstance(sysaid_service_requests, list), "sysaid_service_requests should be a list"
    assert len(sysaid_service_requests) > 0, "sysaid_service_requests should not be empty"
    assert len(sysaid_service_requests) == num_service_requests, f"sysaid_service_requests should have {num_service_requests} entries"
    
    # Verify structure of each service request object
    for service_request in sysaid_service_requests:
        assert "id" in service_request, "Each service request should have an 'id' field"
        assert service_request["id"] in service_request_ids, f"Service request id {service_request['id']} is not in the requested service_request_ids"
        
        # Verify essential SysAid service request fields
        # These are common fields in SysAid service requests based on SysAid API specification
        assert "title" in service_request, "Each service request should have a 'title' field"
        assert "status" in service_request, "Each service request should have a 'status' field"
        
        # Check for additional descriptive fields (optional in some SysAid instances)
        descriptive_fields = ["description", "priority", "category", "subcategory", "requestUser", "assignedUser", "createDate", "modifyDate", "closeDate"]
        present_fields = [field for field in descriptive_fields if field in service_request]
        
        print(f"Service request {service_request['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if service_request == sysaid_service_requests[0]:
            print(f"Example service request structure: {service_request}")

    print(f"Successfully retrieved and validated {len(sysaid_service_requests)} SysAid service requests")

    return True