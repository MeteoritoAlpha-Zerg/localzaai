# 5-test_ticket_details.py

async def test_ticket_details(zerg_state=None):
    """Test Zendesk ticket details retrieval using connector tools"""
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

    # First, get a list of tickets to select one for detailed view
    get_zendesk_tickets_tool = next(tool for tool in tools if tool.name == "get_zendesk_tickets")
    zendesk_tickets_result = await get_zendesk_tickets_tool.execute(view_id=view_id)
    zendesk_tickets = zendesk_tickets_result.result

    # Verify that zendesk_tickets is a list
    assert isinstance(zendesk_tickets, list), "zendesk_tickets should be a list"
    assert len(zendesk_tickets) > 0, "zendesk_tickets should not be empty"
    
    # Select the first ticket to get details for
    ticket_id = zendesk_tickets[0]["id"]
    print(f"Selected ticket ID for details: {ticket_id}")

    # grab the get_zendesk_ticket_details tool and execute it with ticket_id
    get_ticket_details_tool = next(tool for tool in tools if tool.name == "get_zendesk_ticket_details")
    ticket_details_result = await get_ticket_details_tool.execute(ticket_id=ticket_id)
    ticket_details = ticket_details_result.result

    print("Type of returned ticket_details:", type(ticket_details))
    print(f"Ticket details: {str(ticket_details)[:200]}...")

    # Verify that ticket_details is a dictionary
    assert isinstance(ticket_details, dict), "ticket_details should be a dictionary"
    
    # Verify essential Zendesk ticket fields in the detailed view
    assert "id" in ticket_details, "Ticket details should have an 'id' field"
    assert ticket_details["id"] == ticket_id, "Ticket ID in details should match requested ID"
    assert "url" in ticket_details, "Ticket details should have a 'url' field"
    assert "subject" in ticket_details, "Ticket details should have a 'subject' field"
    assert "status" in ticket_details, "Ticket details should have a 'status' field"
    assert "created_at" in ticket_details, "Ticket details should have a 'created_at' field"
    
    # Check for required detailed fields
    detailed_fields = ["description", "type", "priority", "requester_id", "submitter_id", "updated_at"]
    for field in detailed_fields:
        assert field in ticket_details, f"Ticket details should contain '{field}'"
    
    # Check for comments if they are included
    if "comments" in ticket_details:
        assert isinstance(ticket_details["comments"], list), "Ticket comments should be a list"
        print(f"Ticket has {len(ticket_details['comments'])} comments")
        
        # Check structure of first comment if available
        if ticket_details["comments"] and len(ticket_details["comments"]) > 0:
            first_comment = ticket_details["comments"][0]
            assert "id" in first_comment, "Comment should have an 'id'"
            assert "author_id" in first_comment, "Comment should have an 'author_id'"
            assert "body" in first_comment, "Comment should have a 'body'"
            assert "created_at" in first_comment, "Comment should have a 'created_at'"
    
    # Check for custom fields if present
    if "custom_fields" in ticket_details and ticket_details["custom_fields"]:
        assert isinstance(ticket_details["custom_fields"], list), "Custom fields should be a list"
        print(f"Ticket has {len(ticket_details['custom_fields'])} custom fields")
    
    # Check for tags if present
    if "tags" in ticket_details:
        assert isinstance(ticket_details["tags"], list), "Tags should be a list"
        print(f"Ticket has {len(ticket_details['tags'])} tags")

    print(f"Successfully retrieved and validated details for Zendesk ticket {ticket_id}")

    return True