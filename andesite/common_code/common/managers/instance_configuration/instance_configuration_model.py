from enum import Enum
from typing import Any

from pydantic import BaseModel


class InstanceConfigurationSettingEnum(str, Enum):
    CHAT_TTL = "chat_ttl"
    DOC_PROCESSOR_MAX_QUESTIONS = "doc_processor_max_questions"
    DOC_PROCESSOR_LOOKBACK_PERIOD_IN_DAYS = "doc_processor_lookback_period_in_days"
    ALERT_GROUPING_LOOKBACK_PERIOD_IN_SECONDS = "alert_grouping_lookback_period_in_seconds"
    MIN_ALERTS_PER_ANOMALY_GROUP = "alert_anomaly_minimum_alerts_in_group"
    ALERT_ANOMALY_LOOKBACK_PERIOD_IN_SECONDS = "alert_anomaly_lookback_period_in_seconds"

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
