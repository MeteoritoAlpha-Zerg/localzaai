from common.models.context import ResourceReference, ResourceTypeEnum
from common.models.conversation import ChatMessage
from common.models.react import ChatEventType
from core.llms.types import LLMMessageType


def test_event_to_alert_resource_migration():
    old = {"type": "event", "resource_id": "12345"}
    new = ResourceReference.model_validate(old)
    assert new.type == ResourceTypeEnum.alert

    new = ResourceReference(type="event", resource_id="1234")  # type: ignore
    assert new.type == ResourceTypeEnum.alert

    chat_message = ChatMessage(
        id="msg-1",
        role=LLMMessageType.USER,
        type=ChatEventType.thought,
        resources=[
            ResourceReference.model_validate(old),
            ResourceReference(type="event", resource_id="1234"),  # type: ignore
        ],
        content="Mocked search query",
    )
    assert all(
        resource.type == ResourceTypeEnum.alert for resource in chat_message.resources
    )
