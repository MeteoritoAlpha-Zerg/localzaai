import os
from datetime import datetime, timedelta, timezone

from pathlib import Path
from typing import Any, cast

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.models.alerts import Alert, AlertDetailsTable, AlertFilter
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import SecretStr

from connectors.connector import Connector, ConnectorTargetInterface
from connectors.cache import Cache
from connectors.elastic.connector.client import ElasticClient
from connectors.elastic.connector.config import ElasticConnectorConfig
from connectors.elastic.connector.target import ElasticTarget
from connectors.elastic.connector.secrets import ElasticSecrets
from connectors.elastic.connector.tools import ElasticConnectorTools
from connectors.parse_alert_configs import format_data_to_string, parse_summary_table
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()


async def _get_query_target_options(config: ElasticConnectorConfig, secrets: ElasticSecrets) -> ConnectorQueryTargetOptions:
    INDEX = "index"

    definitions = [
        ScopeTargetDefinition(name=INDEX),
    ]

    selectors: list[ScopeTargetSelector] = []

    elastic_client = None
    try:
        elastic_client = ElasticClient.get_client(config.url, secrets.api_key)
        indices = await elastic_client.list_indices()
        index_selector = ScopeTargetSelector(type=INDEX, values=indices)
        pass
    except Exception as e:
        logger().exception("Failed to get ScopeTargetSelector options from Elastic: %s", str(e))
        raise e
    finally:
        if elastic_client:
            await elastic_client.close()

    selectors = [index_selector]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )


async def _merge_dataset_descriptions(
    config: ElasticConnectorConfig,
    secrets: ElasticSecrets,
    existing_data_dictionary: list[DatasetDescription],
    path_prefix: list[str],
) -> list[DatasetDescription]:
    new_data_dictionary: list[DatasetDescription] = []
    indices = await ElasticClient.get_client(config.url, secrets.api_key).list_indices()
    for index in indices:
        if path_prefix and index not in path_prefix:
            continue

        existing_index_description = next(
            (dd for dd in existing_data_dictionary if dd.path == [index]),
            None,
        )
        index_description = existing_index_description.description if existing_index_description else ""
        new_data_dictionary.append(
            DatasetDescription(
                connector=ConnectorIdEnum.ELASTIC,
                path=[index],
                description=index_description,
            )
        )

    return new_data_dictionary


def _get_tools(config: ElasticConnectorConfig, target: ConnectorTargetInterface, secrets: ElasticSecrets, cache: Cache | None) -> list[Tool]:
    elastic_target = ElasticTarget(**target.model_dump())
    return ElasticConnectorTools(
        ElasticConnectorConfig(**config.model_dump()),
        elastic_target,
        secrets,
    ).get_tools()


async def _get_alerts_unfiltered(
    config: ElasticConnectorConfig,
    secrets: ElasticSecrets,
    earliest: int | None = None,
    latest: int | None = None,
    specific_alert_ids: list[str] | None = None,
) -> list[Alert]:
    now = datetime.now(timezone.utc)

    # handle cases where one or the other is not set
    if earliest and not latest:
        latest = 0
    elif latest and not earliest:
        earliest = latest + 86400
    elif not earliest and not latest:
        earliest = 86400
        latest = 0

    latest_time = (now - timedelta(seconds=cast(int, latest))).isoformat()
    earliest_time = (now - timedelta(seconds=cast(int, earliest))).isoformat()

    query: dict[str, Any] = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": earliest_time,
                                "lte": latest_time
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"@timestamp": "desc"}
        ]
    }  if specific_alert_ids is None else {
        "query": {
            "ids": {
                "values": specific_alert_ids
                }
            },
        "sort": [
            {"@timestamp": "desc"},
        ]
    }
    logger().debug(f"Fetching elastic alerts using query: {query}")

    elastic_client = ElasticClient.get_client(config.url, secrets.api_key)
    try:
        raw_alerts = await elastic_client.paginated_search(index=config.alert_index, query=query)
        logger().info(f"ElasticClient search retrieved {len(raw_alerts)} alerts")
    except Exception as e:
        logger().exception("Failed to get alerts from Elastic: %s", str(e))
        raise e
    finally:
        await elastic_client.close()


    parsed_alerts: list[Alert] = []
    for alert in raw_alerts:
        source: dict[str, Any] = alert.get("_source", {})
        threat: list[dict[Any, Any]] = source.get(config.mitre_attack_id_field_name, [{}])
        if len(threat) == 0:
            threat = [{}]

        mitre_techniques: list[str] = [technique.get("id") for el in threat for technique in el.get("technique", {})]
        id = alert.get("_id")
        if id is None:
            raise ValueError("Alert ID is None")
        details_table = AlertDetailsTable.model_validate(source)

        # Pattern from https://www.elastic.co/docs/solutions/security/detect-and-alert/create-detection-rule#create-custom-rule
        index_patterns: list[str] | None = details_table.get_field_value("kibana.alert.rule.parameters.index")
        custom_query: str | None = details_table.get_field_value("kibana.alert.rule.parameters.query")
        detection_logic: str | None = None
        if index_patterns is not None and custom_query is not None:
            detection_logic = f"index patterns: [{', '.join(index_patterns)}]; custom query: {custom_query}"

        parsed_alerts.append(
            Alert(
                id=id,
                connector=ConnectorIdEnum.ELASTIC,
                time=source.get("@timestamp", 0),
                detection_logic=detection_logic,
                title=format_data_to_string(config.alert_title_format, details_table),
                description=format_data_to_string(config.alert_description_format, details_table),
                details_table=details_table,
                summary_table=parse_summary_table(
                    summary_table_configs=config.alert_summary_table_configs, alert_details=details_table
                ),
                summary=format_data_to_string(config.alert_summary_text_format, details_table, join_with="\n"),
                mitre_techniques=mitre_techniques,
            )
        )

    return parsed_alerts


async def _get_alerts(
    config: ElasticConnectorConfig,
    secrets: ElasticSecrets,
    filter: AlertFilter,
    cache: Cache | None
) -> list[Alert]:
    def _is_alert_in_filter(alert: Alert) -> bool:
        after = datetime.now(timezone.utc) - timedelta(seconds=filter.earliest)
        before = datetime.now(timezone.utc) - timedelta(seconds=filter.latest)
        alert_time = alert.time.replace(tzinfo=timezone.utc)
        return alert_time >= after and alert_time <= before

    unfiltered_alerts = await _get_alerts_unfiltered(config, secrets, filter.earliest, filter.latest, filter.alert_ids)
    if filter.alert_ids and len(filter.alert_ids) > 0:
        return [alert for alert in unfiltered_alerts if alert.id in filter.alert_ids]
    else:
        return [alert for alert in unfiltered_alerts if _is_alert_in_filter(alert)]


async def _get_secrets(config: ElasticConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> ElasticSecrets | None:
    api_key = user_token if user_token is not None else config.api_key.decrypt(encryption_key=encryption_key)

    if api_key is None:
        return None

    return ElasticSecrets(
        api_key=api_key,
    )

ElasticConnector = Connector(
    display_name="Elastic",
    id=ConnectorIdEnum.ELASTIC,
    query_target_type=ElasticTarget,
    config_cls=ElasticConnectorConfig,
    description="Elastic is a search platform that allows you to search and gather insights across your data.",
    get_secrets=_get_secrets,
    logo_path=Path(os.path.join(os.path.dirname(__file__), "elastic.svg")),
    get_tools=_get_tools,
    get_alerts=_get_alerts,
    merge_data_dictionary=_merge_dataset_descriptions,
    get_query_target_options=_get_query_target_options,
)
