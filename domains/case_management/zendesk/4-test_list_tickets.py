# 4-test_list_tickets.py

async def test_list_tickets(zerg_state=None):
    """Test Zendesk ticket enumeration by way of connector tools"""
    print("Attempting to authenticate using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.target import ZendeskTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        api_token=zendesk_api_token,
        email=zendesk_email
    )
    assert isinstance(config, ConnectorConfig), "ZendeskConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ZendeskConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ZendeskConnector should be of type Connector"

    # get query target options
    zendesk_query_target_options = await connector.get_query_target_options()
    assert isinstance(zendesk_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select view to target
    view_selector = None
    for selector in zendesk_query_target_options.selectors:
        if selector.type == 'view_ids':  
            view_selector = selector
            break

    assert view_selector, "failed to retrieve view selector from query target options"

    assert isinstance(view_selector.values, list), "view_selector values must be a list"
    view_id = view_selector.values[0] if view_selector.values else None
    print(f"Selecting view ID: {view_id}")

    assert view_id, f"failed to retrieve view ID from view selector"

    # set up the target with view IDs
    target = ZendeskTarget(view_ids=[view_id])
    assert isinstance(target, ConnectorTargetInterface), "ZendeskTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_zendesk_tickets tool and execute it
    get_zendesk_tickets_tool = next(tool for tool in tools if tool.name == "get_zendesk_tickets")
    zendesk_tickets_result = await get_zendesk_tickets_tool.execute(view_id=view_id)
    zendesk_tickets = zendesk_tickets_result.result

    print("Type of returned zendesk_tickets:", type(zendesk_tickets))
    print(f"len tickets: {len(zendesk_tickets)} tickets: {str(zendesk_tickets)[:200]}")

    # Verify that zendesk_tickets is a list
    assert isinstance(zendesk_tickets, list), "zendesk_tickets should be a list"
    assert len(zendesk_tickets) > 0, "zendesk_tickets should not be empty"
    
    # Limit the number of tickets to check if there are many
    tickets_to_check = zendesk_tickets[:5] if len(zendesk_tickets) > 5 else zendesk_tickets
    
    # Verify structure of each ticket object
    for ticket in tickets_to_check:
        # Verify essential Zendesk ticket fields
        assert "id" in ticket, "Each ticket should have an 'id' field"
        assert "url" in ticket, "Each ticket should have a 'url' field"
        
        # Verify common Zendesk ticket fields
        assert "subject" in ticket, "Each ticket should have a 'subject' field"
        assert "status" in ticket, "Each ticket should have a 'status' field"
        assert "created_at" in ticket, "Each ticket should have a 'created_at' field"
        
        # Additional optional fields to check (if present)
        optional_fields = ["description", "requester_id", "assignee_id", "priority", "tags"]
        present_optional = [field for field in optional_fields if field in ticket]
        
        print(f"Ticket {ticket['id']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first ticket for debugging
        if ticket == tickets_to_check[0]:
            print(f"Example ticket structure: {ticket}")

    print(f"Successfully retrieved and validated {len(zendesk_tickets)} Zendesk tickets")

    return True