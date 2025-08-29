from datetime import datetime, timezone
import json
import re
from typing import Annotated, Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny

from connectors.connector_id_enum import ConnectorIdEnum

from common.managers.prioritization_rules.prioritization_rules_model import (
    PrioritizationRule,
)
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


class AlertFilter(BaseModel):
    """
    The AlertFilter defines alert filters like "earliest", "latest", "group_by", etc.
    """

    # these defaults gives alerts in the last hour
    earliest: int = Field(
        default=3600, description="The earliest time to search for alerts, in seconds"
    )
    latest: int = Field(
        default=0, description="The latest time to search for alerts, in seconds"
    )


class AlertDetailsTable(BaseModel):
    model_config = ConfigDict(extra="allow")

    def get_or_default(self, field_name: str, default_value: Optional[Any]):
        if self.__pydantic_extra__:
            if field_name in self.__pydantic_extra__:
                return self.__pydantic_extra__[field_name]
        return default_value


class AlertDetailsLink(BaseModel):
    display_text: str
    link: str


class AlertTime(BaseModel):
    time: datetime


SummaryTableType = Annotated[
    Optional[Dict[str, Union[str, List[AlertDetailsLink], AlertTime, int]]],
    "SummaryTableType",
]

MitreTechniqueId = str


class AbbreviatedAlert(BaseModel):
    id: str
    connector: ConnectorIdEnum
    time: datetime
    priority: int = Field(default=999)
    title: str
    doc_id: Optional[str] = None
    doc_name: Optional[str] = None
    description: str

    class Config:
        json_encoders = {datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat()}


class Alert(AbbreviatedAlert):
    mitre_techniques: list[MitreTechniqueId] = []

    summary: Optional[str] = None
    summary_table: SummaryTableType = None
    details_table: Optional[SerializeAsAny[AlertDetailsTable]] = None

    def assign_alert_priority(
        self,
        highest_mitre_priority: float | None,
        priority_boosts: list[PrioritizationRule],
    ):
        """
        Get the priority of an alert based on the MITRE ATTACK technique used.
        This will apply priority boosts to alerts that match certain criteria
        defined in the PrioritizationRuleManager.
        """
        lowest_priority = 999.0
        if not self.details_table:
            return lowest_priority

        priority = min(lowest_priority, highest_mitre_priority or lowest_priority)

        for boost in priority_boosts:
            field_value = self.details_table.get_or_default(boost.field_name, None)
            if not field_value:
                continue
            field_value_as_str = json.dumps(field_value)
            if not field_value_as_str or not isinstance(field_value_as_str, str):
                continue
            is_found = re.search(boost.field_regex, field_value_as_str)
            if is_found:
                new_priority = priority * (1 - boost.priority_boost)
                priority = new_priority

        self.priority = int(max(0, min(priority, lowest_priority)))


class ConnectorGenerateAlert(BaseModel):
    tid: str
    title: str
    description: str
    category: str
    additional_fields: Optional[list[tuple[str, str]]] = None
