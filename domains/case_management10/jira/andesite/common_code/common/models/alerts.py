import json
import re
from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from common.jsonlogging.jsonlogger import Logging
from common.managers.prioritization_rules.prioritization_rules_model import (
    PrioritizationRule,
)
from common.models.connector_id_enum import ConnectorIdEnum
from common.utils.flatten_dict import flatten_dict

logger = Logging.get_logger(__name__)


class AlertFilter(BaseModel):
    """
    The AlertFilter defines alert filters like "earliest", "latest", "group_by", etc.
    """

    # these defaults gives alerts in the last hour
    earliest: int = Field(default=3600, description="The earliest time to search for alerts, in seconds")
    latest: int = Field(default=0, description="The latest time to search for alerts, in seconds")
    alert_ids: list[str] | None = Field(
        default=None,
        description="List of alert IDs to filter by. If None, all alerts are returned within lookback. If populated, earliest and latest are ignored",
    )


class AlertDetailsLink(BaseModel):
    display_text: str
    link: str


class AlertTime(BaseModel):
    time: datetime


SummaryTableType = Annotated[
    dict[str, str | list[AlertDetailsLink] | AlertTime | int],
    "SummaryTableType",
]

MitreTechniqueId = str


class AlertReference(BaseModel):
    id: str
    connector: ConnectorIdEnum
    added_to_group: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.replace(tzinfo=UTC).isoformat()})


class AbbreviatedAlert(AlertReference):
    priority: int = Field(default=999)
    title: str
    time: datetime
    doc_id: str | None = None
    doc_name: str | None = None
    description: str


class AlertDetailsTable(BaseModel):
    """
    The `AlertDetailsTable` class represents a table of details for an alert.
    It will flatten the details table to ensure all fields are at the same level.
    """

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    def flatten_table(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten the details table to ensure all fields are at the same level.
        """
        return flatten_dict(values)

    def get_field_value(self, field_name: str) -> Any | None:
        """
        Get the value of a field in the details table.
        If the field is not found, it will return None.
        Handles flattened fields by checking for indexed items (lists) and nested dict keys.
        """
        alert_details_dict = self.model_dump()
        field_value = alert_details_dict.get(field_name)

        if field_value is not None:
            return field_value

        prefix = field_name + "."
        indexed_items: list[tuple[int, Any]] = []
        nested_dict: dict[str, Any] = {}

        for key, value in alert_details_dict.items():
            if key.startswith(prefix):
                suffix = key[len(prefix) :]
                if suffix.isdigit():
                    # List-style flattened key, like annotations.mitre_attack.0
                    indexed_items.append((int(suffix), value))
                else:
                    # Dict-style flattened key, like annotations.metadata.foo
                    nested_dict[suffix] = value

        if indexed_items:
            return [item for _, v in sorted(indexed_items) for item in (v if isinstance(v, list) else [v])]
        elif nested_dict:
            # Reconstruct nested dict
            result: dict[str, Any] = {}
            for k, v in nested_dict.items():
                parts = k.split(".")
                current = result
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = v
            return result

        return None

    def get_field_keys(self, field_name: str) -> list[str]:
        """
        Get the expanded keys of field_name.
        - If field_name is a simple key, return [field_name].
        - If field_name refers to a flattened list (e.g., field_name.0), return all indexed keys.
        - If field_name refers to a flattened dict (e.g., field_name.foo), return all matching keys.
        """
        alert_details_dict = self.model_dump()
        field_value = alert_details_dict.get(field_name)

        if field_value is not None:
            return [field_name]

        prefix = field_name + "."

        return [key for key in alert_details_dict if key.startswith(prefix)]


class Alert(AbbreviatedAlert):
    """
    The `Alert` class represents an alert with associated MITRE ATT&CK techniques,
    summary information, and detailed data. It extends the `AbbreviatedAlert` class
    and provides additional fields and methods for handling alert prioritization.

    Attributes:
        mitre_techniques (list[MitreTechniqueId]): A list of MITRE ATT&CK technique IDs associated with the alert.
        summary (Optional[str]): A brief summary of the alert.
        summary_table (SummaryTableType): A table summarizing key details of the alert.
        details_table (AlertDetailsTable): The flattened version of the raw fields

    Methods:
        assign_alert_priority(highest_mitre_priority: float | None, priority_boosts: list[PrioritizationRule]):
            Calculates and assigns a priority to the alert based on the associated
            MITRE ATT&CK techniques and priority boost rules. The priority is determined
            by the lowest priority value and adjusted by matching prioritization rules.
    """

    mitre_techniques: list[MitreTechniqueId] = Field(default_factory=list)

    summary: str | None = None
    summary_table: SummaryTableType = {}
    details_table: AlertDetailsTable = Field(
        default_factory=AlertDetailsTable,
    )
    detection_logic: str | None = None

    def get_details_table_as_dict(self) -> dict[str, Any]:
        """
        Get the details table as a dictionary.
        This method is used to access the details table in a more convenient format.
        """
        return self.details_table.model_dump()

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
            field_value = self.get_details_table_as_dict().get(boost.field_name, None)
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

    def copy_with_translated_details_table(self, field_mappings: dict[str, str], exclude=False) -> "Alert":
        """
        Given a mapping of connector field names to canoncial field names,
        replace the attributes if present in the details table.

        field_mappings: dict[str, str]
        Mappings of the connector field name to the canonical field name.
        exclude: bool
        If exclude is True, fields that do not match the configured
        canonical attributes are excluded from the returned result.
        """
        if field_mappings is None:
            return self
        alert_copy = self.model_copy(deep=True)
        alert_copy_details_dict = alert_copy.get_details_table_as_dict()
        for connector_field_name in field_mappings:
            original_field_value = alert_copy.get_detail_value(connector_field_name)
            canonical_field_name = field_mappings[connector_field_name]
            if original_field_value is not None and canonical_field_name not in alert_copy_details_dict:
                alert_copy._set_detail_value(canonical_field_name, original_field_value)
                alert_copy._delete_detail_value(connector_field_name)

        if exclude:
            set_fields = alert_copy.fields() - self.fields()
            new_table = AlertDetailsTable()
            for field in set_fields:
                setattr(new_table, field, alert_copy.get_detail_value(field))
            alert_copy.details_table = new_table

        return alert_copy

    def get_detail_value(self, field_name: str):
        return self.get_detail_value_or_default(field_name, None)

    def get_detail_value_or_default(self, field_name: str, default: Any):
        return self.details_table.get_field_value(field_name) or default

    def _set_detail_value(self, field_name: str, value: Any):
        if self.details_table.get_field_value(field_name) is not None:
            return
        value_dict = flatten_dict({field_name: value})
        for key, value in value_dict.items():
            setattr(self.details_table, key, value)

    def _delete_detail_value(self, field_name: str):
        field_keys = self.details_table.get_field_keys(field_name)
        pydantic_extra = self.details_table.__pydantic_extra__
        if not pydantic_extra:
            return
        for key in field_keys:
            if key in pydantic_extra:
                del pydantic_extra[key]

    def fields(self) -> set[str]:
        return set(self.get_details_table_as_dict().keys())

    def matching_fields(self, other: "Alert", fields_to_filter: set[str] | None = None) -> set[str]:
        """Identify fields that match between two alerts."""
        matching_fields: set[str] = set()
        self_details_table_dict = self.get_details_table_as_dict()
        other_details_table_dict = other.get_details_table_as_dict()

        our_fields = self_details_table_dict.keys()
        other_fields = other_details_table_dict.keys()

        common_fields = our_fields & other_fields
        if fields_to_filter is not None:
            common_fields = common_fields.intersection(fields_to_filter)

        for field in common_fields:
            val_i = self_details_table_dict.get(field, None)
            val_j = other_details_table_dict.get(field, None)
            if val_i == val_j and val_i is not None:
                matching_fields.add(field)

        return matching_fields

    def matches_id(self, other: "Alert") -> bool:
        return self.id == other.id


class ConnectorGenerateAlert(BaseModel):
    tid: str
    title: str
    description: str
    category: str
    additional_fields: list[tuple[str, str]] | None = None
