from common.models.conversation import ChatMessage, MessageRole
from common.models.react import ChatEventType


def test_chat_message_defaults():
    message = ChatMessage(role=MessageRole.USER, type=ChatEventType.answer, content="Test content")
    assert message.id is not None
    assert message.role == MessageRole.USER
    assert message.type == ChatEventType.answer
    assert message.content == "Test content"
    assert message.timestamp is not None
    assert message.metadata is None
    assert message.resources == []
    assert message.scopes == []
    assert message.proposed_followups is None
    assert message.connector_utilized is None
    assert message.parent_id is None
    assert message.charts is None
