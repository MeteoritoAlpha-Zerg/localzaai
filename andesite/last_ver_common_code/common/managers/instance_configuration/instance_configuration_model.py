from typing import Any
from pydantic import BaseModel
from enum import Enum


class InstanceConfigurationSettingEnum(str, Enum):
    CHAT_TTL = "chat_ttl"
    DOC_PROCESSOR_MAX_QUESTIONS = "doc_processor_max_questions"
    DOC_PROCESSOR_LOOKBACK_PERIOD_IN_DAYS = "doc_processor_lookback_period_in_days"

    def __str__(self) -> str:
        return str(self.value)


class InstanceConfigurationSetting(BaseModel):
    setting_name: InstanceConfigurationSettingEnum
    setting_value: int

    def to_mongo(self):
        document = self.model_dump()
        return document

    @staticmethod
    def from_mongo(document: Any) -> "InstanceConfigurationSetting | None":
        if document is not None:
            return InstanceConfigurationSetting(**document)

        return None
