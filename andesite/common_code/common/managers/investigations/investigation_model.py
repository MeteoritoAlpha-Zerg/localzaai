import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from common.jsonlogging.jsonlogger import Logging
from common.models.context import ResourceReference
from common.models.conversation import ConversationReference

logger = Logging.get_logger(__name__)


class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    edited_by: str | None = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class EventTypeEnum(StrEnum):
    OPEN = "open"
    PRIORITY = "priority"
    TITLE = "title"
    DESCRIPTION = "description"
    CREATION_TIME = "creation_time"
    SECTIONS = "sections"


class InvestigationEvent(BaseModel):
    """
    This model is used to track changes to the investigation.
    Shouldn't be used/modified anywhere else.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: EventTypeEnum
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_value: Any

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class SectionContentTypeEnum(StrEnum):
    NOTE = "note"
    CONVERSATION = "conversation"
    RESOURCE = "resource"


# This is responsible for storing the context for each section.
# It will later need to support a distinction between an old conversation added and a query that was ran using the other context in the section.
class SectionContent(BaseModel):
    type: SectionContentTypeEnum
    content: Note | ConversationReference | ResourceReference

    @model_validator(mode="after")
    def check_type_matches_model(self) -> "SectionContent":
        type_to_model = {
            SectionContentTypeEnum.NOTE: Note,
            SectionContentTypeEnum.CONVERSATION: ConversationReference,
            SectionContentTypeEnum.RESOURCE: ResourceReference,
        }
        expected_model = type_to_model[self.type]
        if not isinstance(self.content, expected_model):
            raise ValueError(f"For type '{self.type}', content must be of model {expected_model.__name__}")
        return self


class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    summary: str = ""
    confidence: int = 0
    contents: list[SectionContent] = []

    @model_validator(mode="before")
    def migrate_description_to_summary(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "summary" not in values and "description" in values:
            values["summary"] = values.pop("description")
        if "summary" in values and values["summary"] is None:
            values["summary"] = ""
        return values

    def get_unique_resources(self) -> list[ResourceReference]:
        unique_resources = {}
        for content in self.contents:
            resource = content.content
            if isinstance(resource, ResourceReference):
                unique_resources[resource.resource_id] = resource
        return list(unique_resources.values())

    def get_unique_conversations(self) -> list[ConversationReference]:
        unique_conversations = {}
        for content in self.contents:
            conversation = content.content
            if isinstance(conversation, ConversationReference):
                unique_conversations[conversation.conversation_id] = conversation
        return list(unique_conversations.values())


class AbbreviatedInvestigation(BaseModel):
    id: str
    open: bool
    user_id: str
    title: str
    priority: int = 10
    description: str | None = None
    creation_time: datetime
    archived_at: datetime | None = None
    last_updated: datetime | None = None
    sections: list[Section] = []

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class Investigation(AbbreviatedInvestigation, BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    open: bool = True
    creation_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    timeline: list[InvestigationEvent] = []
    sections: list[Section] = [Section(name="Findings")]

    # DEMO ONLY
    users: list[str] | None = None

    # This is needed since demo investigations used to hold legacy timeline events
    # This can be removed once all demo investigations had been migrated
    # Technically there are no "production" investigations so this is just extra safety
    @model_validator(mode="before")
    def remove_legacy_timeline_events(cls, values: dict[str, Any]) -> dict[str, Any]:
        timeline = values.get("timeline")
        if timeline and isinstance(timeline, list):
            filtered_timeline = []
            for event in timeline:
                event_type = event.get("event_type") if isinstance(event, dict) else getattr(event, "event_type", None)
                if event_type in EventTypeEnum.__members__.values() or event_type in EventTypeEnum.__members__:
                    filtered_timeline.append(event)
            values["timeline"] = filtered_timeline
        return values

    def __setattr__(self, name, value):
        if name.upper() in EventTypeEnum.__members__:
            try:
                event_type = EventTypeEnum(name)
                self.timeline.append(
                    InvestigationEvent(
                        user_id=self.user_id,
                        event_type=event_type,
                        updated_value=value,
                    )
                )
            except ValidationError:
                logger().exception(
                    f"Failed to update investigation timeline due to unknown event type: {name}",
                )
                pass

        super().__setattr__(name, value)

    def to_mongo(self):
        model = self.model_dump(exclude={"id"})
        model["_id"] = self.id
        return model

    @staticmethod
    def from_mongo(document: Any) -> "Investigation | None":
        if document is not None:
            document["id"] = str(document.pop("_id", None))
            return Investigation(**document)

        return None

    def get_abbreviated(self) -> AbbreviatedInvestigation:
        return AbbreviatedInvestigation.model_validate(self.model_dump())

    def get_unique_resources_from_sections(self) -> list[ResourceReference]:
        unique_resources = {}
        for section in self.sections:
            for resource in section.get_unique_resources():
                unique_resources[resource.resource_id] = resource
        return list(unique_resources.values())

    def get_unique_conversations_from_sections(self) -> list[ConversationReference]:
        unique_conversations = {}
        for section in self.sections:
            for conversation in section.get_unique_conversations():
                unique_conversations[conversation.conversation_id] = conversation
        return list(unique_conversations.values())

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})
