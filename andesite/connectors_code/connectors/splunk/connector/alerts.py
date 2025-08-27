import asyncio
import datetime
from typing import Annotated, Any, List, Optional, Union

from common.jsonlogging.jsonlogger import Logging
from common.models.alerts import Alert, AlertDetailsTable, AlertFilter
from common.models.connector_id_enum import ConnectorIdEnum
from opentelemetry import trace
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationInfo
from splunklib.binding import AuthenticationError  # type: ignore[import-untyped]

from connectors.parse_alert_configs import format_data_to_string, parse_summary_table, parse_texts_to_string
from connectors.splunk.connector.config import AlertSummaryTableConfig
from connectors.splunk.database.saved_search import SplunkSavedSearch
from connectors.splunk.database.splunk_instance import SplunkInstance

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def multivalue_validator(value: Any, info: ValidationInfo) -> list[str]:
    if isinstance(value, list):
        entries: list[Any] = []
        for entry in value:
            entries.extend([item.strip() for item in entry.split("\r\n")])
        return entries
    elif isinstance(value, str):
        return [item.strip() for item in value.split("\r\n")]
    else:
        raise ValueError(f"Invalid field type for {info.field_name}: expected str or list[str]")


MultivalueType = Annotated[list[str], BeforeValidator(multivalue_validator)]


class NecessarySplunkFields(BaseModel):
    killchain: MultivalueType = Field(default=[])
    event_id: str
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
        saved_searches_task = asyncio.create_task(splunk_instance.saved_searches_async())
        if alert_filter.alert_ids is not None:
            alerts_task = asyncio.create_task(splunk_instance.fetch_alerts_by_ids(alert_ids=alert_filter.alert_ids))
        else:
            alerts_task = asyncio.create_task(splunk_instance.fetch_alerts(earliest, latest))

        splunk_saved_searches, alerts = await asyncio.gather(saved_searches_task, alerts_task)

    except AuthenticationError:
        logger().exception("Splunk token invalid")
        raise Exception("Invalid Splunk token")

    returned_alerts = _convert_splunk_dicts_to_alerts(
        mitre_attack_id_field_name,
        splunk_saved_searches,
        alert_summary_table_configs,
        alert_title_format,
        alert_description_format,
        alert_summary_text_format,
        alerts,
    )

    return returned_alerts


def _convert_splunk_dicts_to_alerts(
    mitre_attack_id_field_name: str,
    splunk_saved_searches: list[SplunkSavedSearch],
    alert_summary_table_configs: List[AlertSummaryTableConfig],
    alert_title_format: str,
    alert_description_format: str,
    alert_summary_text_format: str,
    alerts: list[dict[str, Union[str, list[str]]]],
) -> list[Alert]:
    returned_alerts: list[Alert] = []

    for alert_dict in alerts:
        necessary_splunk_fields = NecessarySplunkFields.model_validate(alert_dict)

        utc = datetime.timezone.utc
        andesite_time = alert_dict.get("andesite_time", 0)
        t = int(andesite_time if not isinstance(andesite_time, list) else 0)
        time = datetime.datetime.fromtimestamp(t, utc)

        # in es mode fields will be dynamically generated/changed in raw so we need to use alert_id to get a consistent id
        id = necessary_splunk_fields.event_id

        mitre_techniques = alert_dict.get(mitre_attack_id_field_name, [])
        if isinstance(mitre_techniques, str):
            mitre_techniques = [mitre_techniques]
        alert_details_table = AlertDetailsTable.model_validate(alert_dict)
        rule_name = alert_dict.get("search_name", None)

        alert = Alert(
            id=id,
            time=time,
            detection_logic=next(
                (saved_search.spl for saved_search in splunk_saved_searches if saved_search.name == rule_name), None
            ),
            connector=ConnectorIdEnum.SPLUNK,
            title=parse_texts_to_string(necessary_splunk_fields.killchain)
            if necessary_splunk_fields.doc_name
            else format_data_to_string(alert_title_format, alert_details_table, inner_key_pattern=r"\$(.*?)\$"),
            doc_id=necessary_splunk_fields.doc_id,
            doc_name=necessary_splunk_fields.doc_name,
            description=format_data_to_string(alert_description_format, alert_details_table),
            details_table=alert_details_table,
            summary_table=parse_summary_table(
                summary_table_configs=alert_summary_table_configs, alert_details=alert_details_table
            ),
            summary=format_data_to_string(alert_summary_text_format, alert_details_table, join_with="\n"),
            mitre_techniques=mitre_techniques,
        )

        returned_alerts.append(alert)
    return returned_alerts
