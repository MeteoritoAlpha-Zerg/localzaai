import os
from pathlib import Path
from typing import Optional

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.models.tool import Tool
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from connectors.splunk.connector.alerts import get_splunk_alerts
from opentelemetry import trace
from pydantic import SecretStr

from connectors.connector import (
    Connector,
    ConnectorTargetInterface,
)
from connectors.connector_id_enum import ConnectorIdEnum
from common.models.alerts import (
    Alert,
    AlertFilter,
    ConnectorGenerateAlert,
)
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from connectors.splunk.connector.config import (
    SplunkConnectorConfig,
)
from connectors.splunk.connector.target import SplunkTarget
from connectors.splunk.connector.tools import SplunkConnectorTools
from connectors.splunk.database.splunk_instance import SplunkInstance

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()


def _get_instance(config: SplunkConnectorConfig, token: Optional[SecretStr]) -> SplunkInstance:
    return SplunkInstance(
        protocol=config.protocol,
        host=config.host,
        port=config.port,
        token=token,
        ssl_verification=config.ssl_verification,
        app=config.app,
        notable_index=config.notable_index,
        es=config.es,
        mtls_client_cert_path=config.mtls_client_cert_path,
        mtls_client_key_path=config.mtls_client_key_path,
        mtls_client_cert_data=config.mtls_client_cert_data,
        mtls_client_key_data=config.mtls_client_key_data,
        token_oauth_hostname=config.token_oauth_hostname,
        token_oauth_client_id=config.token_oauth_client_id,
        token_oauth_client_secret=config.token_oauth_client_secret,
        uri_add_prefix=config.uri_add_prefix,
        use_mtls=config.use_mtls,
    )

def _get_query_instance(config: SplunkConnectorConfig, token: SecretStr | None) -> SplunkInstance:
    return _get_instance(config=config, token=token)

def _get_delete_instance(config: SplunkConnectorConfig) -> SplunkInstance:
    return _get_instance(config=config, token=config.delete_token)

def _get_indexing_instance(config: SplunkConnectorConfig) -> SplunkInstance:
    return _get_instance(config=config, token=config.indexing_token)

async def _get_query_target_options(config: SplunkConnectorConfig) -> ConnectorQueryTargetOptions:
    INDEXES = "indexes"

    definitions = [ScopeTargetDefinition(name=INDEXES, multiselect=True)]
    indexes = await _get_indexing_instance(config).indexes()
    selectors = [ScopeTargetSelector(type=INDEXES, values=indexes)]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )

async def _generate_alert(config: SplunkConnectorConfig, token: SecretStr | None, alert: ConnectorGenerateAlert):
    await _get_query_instance(config=config, token=token).create_notable_alert(
        tid=alert.tid,
        title=alert.title,
        description=alert.description,
        category=alert.category,
        additional_fields=alert.additional_fields,
    )

async def _delete_generated_alerts(config: SplunkConnectorConfig) -> None:
    if not config.delete_token:
        logger().warning(
            "Delete token is not configured for Splunk connector, skipping delete_generated_alerts"
        )
        return None
    client = _get_delete_instance(config=config)
    return await client.delete_generated_notable_alerts()

async def _get_alerts(
    config: SplunkConnectorConfig, token: SecretStr | None, filter: AlertFilter
) -> list[Alert]:
    return await get_splunk_alerts(
        alert_filter=filter,
        mitre_attack_id_field_name=config.mitre_attack_id_field_name,
        splunk_instance=_get_query_instance(config=config, token=token),
        alert_summary_table_configs=config.alert_summary_table_configs,
        alert_title_format=config.alert_title_format,
        alert_description_format=config.alert_description_format,
        alert_summary_text_format=config.alert_summary_text_format
    )

def _get_tools(display_name: str, config: SplunkConnectorConfig, target: ConnectorTargetInterface, token: SecretStr | None) -> list[Tool]:
    target = SplunkTarget(**target.model_dump())

    def get_dataset_structures(dataset_target: Optional[ConnectorTargetInterface] = None):
        instance = _get_query_instance(config=config, token=token)
        return _get_dataset_structure(instance=instance, data_indexing_lookback_seconds=config.data_indexing_lookback_seconds, dataset_target=dataset_target)

    return SplunkConnectorTools(
        target, get_dataset_structures, connector_display_name=display_name
    ).get_tools()

async def _check_connection(config: SplunkConnectorConfig, token: SecretStr | None) -> bool:
    client = _get_query_instance(config=config, token=token)
    return await client.check_connection_async()

async def _get_dataset_structure(
        instance: SplunkInstance, data_indexing_lookback_seconds: int, dataset_target: Optional[ConnectorTargetInterface] = None
) -> list[DatasetStructure]:
    logger().info("Retrieving Splunk structure from Splunk instance")
    indexes = await instance.indexes()

    if dataset_target is not None:
        dataset_target = SplunkTarget(**dataset_target.model_dump())
        indexes = [index for index in indexes if index in dataset_target.indexes]

    structure: list[DatasetStructure] = []

    lookback_time_in_query = f"-{data_indexing_lookback_seconds}s"

    for index in indexes:
        fields = await instance.get_uncached_fields_for_index(
            index, lookback_time_in_query
        )

        structure.append(
            DatasetStructure(
                connector=ConnectorIdEnum.SPLUNK, dataset=index, attributes=fields
            )
        )
    logger().info("Completed retrieving Splunk structure from Splunk instance")
    return structure

async def _get_dataset_structure_to_index(
    config: SplunkConnectorConfig, dataset_target: Optional[ConnectorTargetInterface] = None
) -> list[DatasetStructure]:
    instance = _get_indexing_instance(config=config)
    return await _get_dataset_structure(instance, config.data_indexing_lookback_seconds, dataset_target)

async def _merge_data_dictionary(
    config: SplunkConnectorConfig,
    token: SecretStr | None,
    existing_dataset_descriptions: list[DatasetDescription],
    path_prefix: Optional[list[str]] = [],
) -> list[DatasetDescription]:
    data_dictionary: list[DatasetDescription] = []

    splunk_instance = _get_query_instance(config=config, token=token)
    for index in await splunk_instance.indexes():
        if path_prefix and index not in path_prefix:
            continue

        existing_index_description = next(
            (dd for dd in existing_dataset_descriptions if dd.path == [index]),
            None,
        )
        index_description = (
            existing_index_description.description
            if existing_index_description
            else ""
        )
        data_dictionary.append(
            DatasetDescription(
                connector=ConnectorIdEnum.SPLUNK,
                path=[index],
                description=index_description,
            )
        )

        fields = await splunk_instance.get_fields_for_index(
            index, f"-{config.data_indexing_lookback_seconds}s"
        )
        for field in fields:
            existing_field_description = next(
                (
                    dd
                    for dd in existing_dataset_descriptions
                    if dd.path == [index, field.field_name]
                ),
                None,
            )
            # If we have a description for this field, then use that
            field_description = (
                existing_field_description.description
                if existing_field_description
                else ""
            )
            data_dictionary.append(
                DatasetDescription(
                    connector=ConnectorIdEnum.SPLUNK,
                    path=[index, field.field_name],
                    description=field_description,
                )
            )
    return data_dictionary


def _get_does_allow_user_token_management(config: SplunkConnectorConfig) -> bool:
    return not (
            bool(config.token) or bool(config.token_oauth_hostname)
        )

SplunkConnector = Connector(
    display_name="Splunk",
    id=ConnectorIdEnum.SPLUNK,
    config_cls=SplunkConnectorConfig,
    query_target_type=SplunkTarget,
    description="Splunk is a data platform that allows you to search, monitor, and analyze machine-generated data.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "splunk.svg")),

    get_tools=_get_tools,
    get_alerts=_get_alerts,
    generate_alert=_generate_alert,
    check_connection=_check_connection,
    merge_data_dictionary=_merge_data_dictionary,
    delete_generated_alerts=_delete_generated_alerts,
    get_query_target_options=_get_query_target_options,
    get_dataset_structure_to_index=_get_dataset_structure_to_index,
    get_does_allow_user_token_management=_get_does_allow_user_token_management,
    UNSAFE_get_query_instance=_get_query_instance
)
