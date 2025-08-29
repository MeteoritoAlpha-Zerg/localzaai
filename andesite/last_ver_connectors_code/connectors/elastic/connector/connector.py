from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
from typing import Any

from common.models.alerts import Alert, AlertDetailsTable, AlertFilter
from connectors.elastic.connector.client import ElasticClient
from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.models.tool import Tool
from connectors.parse import format_data_to_string, parse_summary_table
from opentelemetry import trace

from connectors.elastic.connector.config import ElasticConnectorConfig
from connectors.elastic.connector.target import ElasticTarget
from connectors.elastic.connector.tools import ElasticConnectorTools
from connectors.connector import Connector, ConnectorTargetInterface
from connectors.connector_id_enum import ConnectorIdEnum
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from pydantic import SecretStr

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()


async def _get_query_target_options(config: ElasticConnectorConfig) -> ConnectorQueryTargetOptions:
    INDEX = "index"

    definitions = [
        ScopeTargetDefinition(name=INDEX),
    ]

    selectors: list[ScopeTargetSelector] = []

    try:
        indices = ElasticClient.get_client(config.url, config.api_key).list_indices()
        index_selector = ScopeTargetSelector(type=INDEX, values=indices)
        pass
    except Exception as e:
        logger().exception(
            "Failed to get ScopeTargetSelector options from Elastic: %s", str(e)
        )
        raise e

    selectors = [index_selector]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )


async def _merge_dataset_descriptions(
    config: ElasticConnectorConfig, token: SecretStr | None, existing_data_dictionary: list[DatasetDescription], path_prefix: list[str]
) -> list[DatasetDescription]:
    new_data_dictionary: list[DatasetDescription] = []
    indices = ElasticClient.get_client(config.url, config.api_key).list_indices()
    for index in indices:
        if path_prefix and index not in path_prefix:
            continue

        existing_index_description = next(
            (dd for dd in existing_data_dictionary if dd.path == [index]),
            None,
        )
        index_description = (
            existing_index_description.description
            if existing_index_description
            else ""
        )
        new_data_dictionary.append(
            DatasetDescription(
                connector=ConnectorIdEnum.ELASTIC,
                path=[index],
                description=index_description,
            )
        )

    return new_data_dictionary

def _get_tools(_display_name: str, config: ElasticConnectorConfig, target: ConnectorTargetInterface, token: SecretStr | None) -> list[Tool]:
    elastic_target = ElasticTarget(**target.model_dump())
    return ElasticConnectorTools(
        ElasticConnectorConfig(**config.model_dump()),
        elastic_target,
    ).get_tools()

async def _get_alerts(
        config: ElasticConnectorConfig, token: SecretStr | None, filter: AlertFilter
    ) -> list[Alert]:
    def _is_alert_in_filter(alert: Alert) -> bool:
        after = datetime.now(timezone.utc) - timedelta(seconds=filter.earliest)
        before = datetime.now(timezone.utc) - timedelta(seconds=filter.latest)
        alert_time = alert.time.replace(tzinfo=timezone.utc)
        return alert_time >= after and alert_time <= before

    raw_alerts: list[dict[Any, Any]] = ElasticClient.get_client(config.url, config.api_key).search(config.alert_index, query={})

    parsed_alerts: list[Alert] = []
    for alert in raw_alerts:
        source = alert.get("_source", {})
        threat: list[dict[Any, Any]] = source.get(config.mitre_attack_id_field_name, [{}])
        if len(threat) == 0:
            threat = [{}]

        mitre_techniques : list[str] = [technique.get("id") for el in threat for technique in el.get("technique", {})]
        id = hashlib.md5(
            (
                alert.get("_id", alert)
            ).encode()
        ).hexdigest()
        parsed_alerts.append(Alert(
            id=id,
            connector=ConnectorIdEnum.ELASTIC,
            time=source.get("@timestamp", 0),
            title=format_data_to_string(config.alert_title_format, source),
            description=format_data_to_string(
                config.alert_description_format, source
            ),
            details_table=AlertDetailsTable.model_validate(source),
            summary_table=parse_summary_table(summary_table_configs=config.alert_summary_table_configs, alert_dict=source),
            summary=format_data_to_string(
                config.alert_summary_text_format, source, join_with="\n"
            ),
            mitre_techniques=mitre_techniques
        ))

    parsed_alerts = [alert for alert in parsed_alerts if _is_alert_in_filter(alert)]

    return parsed_alerts

ElasticConnector = Connector[ElasticConnectorConfig, ElasticTarget](
    display_name="Elastic",
    id=ConnectorIdEnum.ELASTIC,
    query_target_type=ElasticTarget,
    config_cls=ElasticConnectorConfig,
    description="Elastic is a search platform that allows you to search and gather insights across your data.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "elastic.svg")),

    get_tools=_get_tools,
    get_alerts=_get_alerts,
    merge_data_dictionary=_merge_dataset_descriptions,
    get_query_target_options=_get_query_target_options,
)
