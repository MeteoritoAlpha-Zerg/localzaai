async def test_add_ticket_comment(zerg_state=None):
    """Test adding a comment to a Zendesk ticket"""
    print("Attempting to add a comment to a ticket using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.tools import ZendeskConnectorTools
    from connectors.zendesk.target import ZendeskTarget

    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=SecretStr(zendesk_api_token)
    )
    connector = ZendeskConnector(config)

    connector_target = ZendeskTarget(config=config)
    
    # Get connector tools
    tools = ZendeskConnectorTools(
        zendesk_config=config, 
        target=ZendeskTarget, 
        connector_display_name="Zendesk"
    )
    
    # First get a list of tickets to find one to comment on
    zendesk_tickets = await tools.get_zendesk_tickets(limit=5)
    
    assert zendesk_tickets and len(zendesk_tickets) > 0, "No tickets found"
    
    # Select the first ticket
    first_ticket = zendesk_tickets[0]
    ticket_id = first_ticket.get('id')
    
    assert ticket_id, "Could not find an ID for the first ticket"
    
    # Add a comment to the ticket
    import time
    timestamp = int(time.time())
    comment_text = f"Test comment added by connector test at {timestamp}"
    comment_is_public = False  # Set to true for public comments, false for internal notes
    
    comment = await tools.add_comment_to_ticket(
        ticket_id=ticket_id,
        comment_text=comment_text,
        public=comment_is_public
    )
    
    assert comment, "Failed to add comment to ticket"
    
    # Verify the comment was added by retrieving ticket comments
    ticket_comments = await tools.get_ticket_comments(ticket_id=ticket_id)
    
    assert ticket_comments, f"Failed to retrieve comments for ticket {ticket_id}"
    
    # Find our comment in the list (should be the most recent)
    comment_found = False
    if ticket_comments and len(ticket_comments) > 0:
        most_recent_comment = ticket_comments[0]  # Assuming comments are sorted by date descending
        if most_recent_comment.get('body') == comment_text:
            comment_found = True
    
    assert comment_found, "Added comment was not found in ticket comments"
    
    print(f"Successfully added comment to ticket #{ticket_id}")
    
    return True