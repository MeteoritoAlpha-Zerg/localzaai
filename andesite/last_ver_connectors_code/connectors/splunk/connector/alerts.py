import datetime
import hashlib
from typing import Annotated, Any, List, Optional

from common.jsonlogging.jsonlogger import Logging
from connectors.parse import format_data_to_string, parse_summary_table, parse_texts_to_string
from opentelemetry import trace
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pydantic_core.core_schema import ValidationInfo
from splunklib.binding import AuthenticationError  # type: ignore[import-untyped]

from connectors.connector_id_enum import ConnectorIdEnum
from common.models.alerts import (
    Alert,
    AlertDetailsTable,
    AlertFilter,
)
from connectors.splunk.connector.config import AlertSummaryTableConfig
from connectors.splunk.database.splunk_instance import SplunkInstance

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def multivalue_validator(value: Any, info: ValidationInfo) -> list[str]:
    if isinstance(value, list):
        entries = []
        for entry in value:
            entries.extend([item.strip() for item in entry.split("\r\n")])
        return entries
    elif isinstance(value, str):
        return [item.strip() for item in value.split("\r\n")]
    else:
        raise ValueError(
            f"Invalid field type for {info.field_name}: expected str or list[str]"
        )


MultivalueType = Annotated[list[str], BeforeValidator(multivalue_validator)]


class NecessarySplunkFields(BaseModel):
    killchain: MultivalueType = Field(default=[])
    event_id: str = Field(default="")
    doc_id: Optional[str] = None
    doc_name: Optional[str] = None

    model_config = ConfigDict(extra="allow")

async def get_splunk_alerts(
    alert_filter: AlertFilter,
    mitre_attack_id_field_name: str,
    splunk_instance: SplunkInstance,
    alert_summary_table_configs: List[AlertSummaryTableConfig],
    alert_title_format: str,
    alert_description_format: str,
    alert_summary_text_format: str,
) -> list[Alert]:
    earliest = f"-{alert_filter.earliest}s"
    latest = f"-{alert_filter.latest}s"

    try:
        alerts = await splunk_instance.fetch_alerts(earliest, latest)
    except AuthenticationError:
        logger().exception("Splunk token invalid")
        raise Exception("Invalid Splunk token")

    returned_alerts: list[Alert] = []

    for alert_dict in alerts:
        necessary_splunk_fields = NecessarySplunkFields.model_validate(alert_dict)

        utc = datetime.timezone.utc
        andesite_time = alert_dict.get("andesite_time", 0)
        t = int(andesite_time if not isinstance(andesite_time, list) else 0)
        time = datetime.datetime.fromtimestamp(t, utc)

        # in es mode fields will be dynamically generated/changed in raw so we need to use alert_id to get a consistent id
        id = hashlib.md5(
            (
                necessary_splunk_fields.event_id
                if splunk_instance._es
                else (str(time) + str(alert_dict))
            ).encode()
        ).hexdigest()

        details_table = AlertDetailsTable.model_validate(alert_dict)
        mitre_techniques = details_table.get_or_default(mitre_attack_id_field_name, default_value=None)
        if mitre_techniques is None:
            mitre_techniques = []
        elif type(mitre_techniques) is str:
            mitre_techniques = [mitre_techniques]

        alert = Alert(
            id=id,
            time=time,
            connector=ConnectorIdEnum.SPLUNK,
            title=parse_texts_to_string(necessary_splunk_fields.killchain)
            if necessary_splunk_fields.doc_name
            else format_data_to_string(alert_title_format, alert_dict),
            doc_id=necessary_splunk_fields.doc_id,
            doc_name=necessary_splunk_fields.doc_name,
            description=format_data_to_string(
                alert_description_format, alert_dict
            ),
            details_table=details_table,
            summary_table=parse_summary_table(summary_table_configs=alert_summary_table_configs, alert_dict=alert_dict),
            summary=format_data_to_string(
                alert_summary_text_format, alert_dict, join_with="\n"
            ),
            mitre_techniques=mitre_techniques
        )

        returned_alerts.append(alert)

    return returned_alerts
