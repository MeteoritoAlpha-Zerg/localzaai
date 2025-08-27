import os
from pathlib import Path
from typing import Optional

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.models.alerts import (
    Alert,
    AlertFilter,
    ConnectorGenerateAlert,
)
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import SecretStr

from connectors.connector import (
    Cache,
    Connector,
    ConnectorTargetInterface,
)
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)
from connectors.splunk.connector.alerts import get_splunk_alerts
from connectors.splunk.connector.config import (
    SplunkConnectorConfig,
)
from connectors.splunk.connector.secrets import SplunkSecrets
from connectors.splunk.connector.target import SplunkTarget
from connectors.splunk.connector.tools import SplunkConnectorTools
from connectors.splunk.database.splunk_instance import SplunkInstance

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

def _get_instance(config: SplunkConnectorConfig,
                token: SecretStr | None,
                mtls_client_cert_data: SecretStr | None,
                mtls_client_key_data: SecretStr | None,
                token_oauth_client_id: SecretStr | None,
                token_oauth_client_secret: SecretStr | None,) -> SplunkInstance:

    return SplunkInstance(
        protocol=config.protocol,
        host=config.host,
        port=config.port,
        token=token,
        ssl_verification=config.ssl_verification,
        app=config.app,
        notable_index=config.notable_index,
        notable_write_index=config.notable_write_index,
        es=config.es,
        mtls_client_cert_path=config.mtls_client_cert_path,
        mtls_client_key_path=config.mtls_client_key_path,
        mtls_client_cert_data=mtls_client_cert_data,
        mtls_client_key_data=mtls_client_key_data,
        token_oauth_hostname=config.token_oauth_hostname,
        token_oauth_client_id=token_oauth_client_id,
        token_oauth_client_secret=token_oauth_client_secret,
        uri_add_prefix=config.uri_add_prefix,
        use_mtls=config.use_mtls,
    )



def _get_query_instance(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> SplunkInstance:
    return _get_instance(config=config, token=secrets.token, mtls_client_cert_data=secrets.mtls_client_cert_data, mtls_client_key_data=secrets.mtls_client_key_data, token_oauth_client_id=secrets.token_oauth_client_id, token_oauth_client_secret=secrets.token_oauth_client_secret)


def _get_delete_instance(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> SplunkInstance:
    return _get_instance(config=config, token=secrets.delete_token, mtls_client_cert_data=secrets.mtls_client_cert_data, mtls_client_key_data=secrets.mtls_client_key_data, token_oauth_client_id=secrets.token_oauth_client_id, token_oauth_client_secret=secrets.token_oauth_client_secret)


def _get_indexing_instance(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> SplunkInstance:
    return _get_instance(config=config, token=secrets.indexing_token, mtls_client_cert_data=secrets.mtls_client_cert_data, mtls_client_key_data=secrets.mtls_client_key_data, token_oauth_client_id=secrets.token_oauth_client_id, token_oauth_client_secret=secrets.token_oauth_client_secret)



async def _get_query_target_options(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> ConnectorQueryTargetOptions:
    INDEXES = "indexes"

    definitions = [ScopeTargetDefinition(name=INDEXES, multiselect=True)]
    indexes = await _get_indexing_instance(config, secrets).indexes()
    selectors = [ScopeTargetSelector(type=INDEXES, values=indexes)]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )


async def _generate_alert(config: SplunkConnectorConfig, secrets: SplunkSecrets, alert: ConnectorGenerateAlert):
    await _get_query_instance(config=config, secrets=secrets).create_notable_alert(
        tid=alert.tid,
        title=alert.title,
        description=alert.description,
        category=alert.category,
        additional_fields=alert.additional_fields,
    )


async def _delete_generated_alerts(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> None:
    if not config.delete_token:
        logger().warning("Delete token is not configured for Splunk connector, skipping delete_generated_alerts")
        return None
    client = _get_delete_instance(config=config, secrets=secrets)
    return await client.delete_generated_notable_alerts()


async def _get_alerts(config: SplunkConnectorConfig, secrets: SplunkSecrets, filter: AlertFilter, cache: Cache | None) -> list[Alert]:
    return await get_splunk_alerts(
        alert_filter=filter,
        mitre_attack_id_field_name=config.mitre_attack_id_field_name,
        splunk_instance=_get_query_instance(config=config, secrets=secrets),
        alert_summary_table_configs=config.alert_summary_table_configs,
        alert_title_format=config.alert_title_format,
        alert_description_format=config.alert_description_format,
        alert_summary_text_format=config.alert_summary_text_format,
    )


def _get_tools(config: SplunkConnectorConfig, target: ConnectorTargetInterface, secrets: SplunkSecrets, cache: Cache | None) -> list[Tool]:
    target = SplunkTarget(**target.model_dump())
    query_instance = _get_query_instance(config=config, secrets=secrets)

    def get_dataset_structures(dataset_target: Optional[ConnectorTargetInterface] = None):
        return _get_dataset_structure(
            instance=query_instance,
            data_indexing_lookback_seconds=config.data_indexing_lookback_seconds,
            dataset_target=dataset_target,
        )

    return SplunkConnectorTools(target, get_dataset_structures, query_instance, secrets, config).get_tools()


async def _check_connection(config: SplunkConnectorConfig, secrets: SplunkSecrets) -> bool:
    client = _get_query_instance(config=config, secrets=secrets)
    return await client.check_connection_async()


async def _get_dataset_structure(
    instance: SplunkInstance,
    data_indexing_lookback_seconds: int,
    dataset_target: Optional[ConnectorTargetInterface] = None,
) -> list[DatasetStructure]:
    logger().info("Retrieving Splunk structure from Splunk instance")
    indexes = await instance.indexes()

    if dataset_target is not None:
        dataset_target = SplunkTarget(**dataset_target.model_dump())
        indexes = [index for index in indexes if index in dataset_target.indexes]

    structure: list[DatasetStructure] = []

    lookback_time_in_query = f"-{data_indexing_lookback_seconds}s"

    for index in indexes:
        fields = await instance.get_uncached_fields_for_index(index, lookback_time_in_query)

        structure.append(DatasetStructure(connector=ConnectorIdEnum.SPLUNK, dataset=index, attributes=fields))
    logger().info("Completed retrieving Splunk structure from Splunk instance")
    return structure


async def _get_dataset_structure_to_index(
    config: SplunkConnectorConfig, secrets: SplunkSecrets, dataset_target: Optional[ConnectorTargetInterface] = None
) -> list[DatasetStructure]:
    instance = _get_indexing_instance(config=config, secrets=secrets)
    return await _get_dataset_structure(instance, config.data_indexing_lookback_seconds, dataset_target)


async def _merge_data_dictionary(
    config: SplunkConnectorConfig,
    secrets: SplunkSecrets,
    existing_dataset_descriptions: list[DatasetDescription],
    path_prefix: Optional[list[str]] = None,
) -> list[DatasetDescription]:
    if path_prefix is None:
        path_prefix = []

    data_dictionary: list[DatasetDescription] = []

    splunk_instance = _get_query_instance(config=config, secrets=secrets)
    for index in await splunk_instance.indexes():
        if path_prefix and index not in path_prefix:
            continue

        existing_index_description = next(
            (dd for dd in existing_dataset_descriptions if dd.path == [index]),
            None,
        )
        index_description = existing_index_description.description if existing_index_description else ""
        data_dictionary.append(
            DatasetDescription(
                connector=ConnectorIdEnum.SPLUNK,
                path=[index],
                description=index_description,
            )
        )

        fields = await splunk_instance.get_fields_for_index(index, f"-{config.data_indexing_lookback_seconds}s")
        for field in fields:
            existing_field_description = next(
                (dd for dd in existing_dataset_descriptions if dd.path == [index, field.field_name]),
                None,
            )
            field_description = existing_field_description.description if existing_field_description else ""
            data_dictionary.append(
                DatasetDescription(
                    connector=ConnectorIdEnum.SPLUNK,
                    path=[index, field.field_name],
                    description=field_description,
                )
            )
    return data_dictionary


def _get_does_allow_user_token_management(config: SplunkConnectorConfig) -> bool:
    return not (bool(config.token) or bool(config.token_oauth_hostname))

async def _get_secrets(config: SplunkConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> SplunkSecrets | None:
    token = user_token if user_token is not None else config.token.decrypt(encryption_key=encryption_key) if config.token else None
    delete_token = config.delete_token.decrypt(encryption_key=encryption_key) if config.delete_token else None
    indexing_token = config.indexing_token.decrypt(encryption_key=encryption_key) if config.indexing_token else None
    mtls_client_cert_data = config.mtls_client_cert_data.decrypt(encryption_key=encryption_key) if config.mtls_client_cert_data else None
    mtls_client_key_data = config.mtls_client_key_data.decrypt(encryption_key=encryption_key) if config.mtls_client_key_data else None
    token_oauth_client_id = config.token_oauth_client_id.decrypt(encryption_key=encryption_key) if config.token_oauth_client_id else None
    token_oauth_client_secret = config.token_oauth_client_secret.decrypt(encryption_key=encryption_key) if config.token_oauth_client_secret else None

    return SplunkSecrets(
        token=token,
        delete_token=delete_token,
        indexing_token=indexing_token,
        mtls_client_cert_data=mtls_client_cert_data,
        mtls_client_key_data=mtls_client_key_data,
        token_oauth_client_id=token_oauth_client_id,
        token_oauth_client_secret=token_oauth_client_secret,
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
    get_secrets=_get_secrets,
    check_connection=_check_connection,
    merge_data_dictionary=_merge_data_dictionary,
    delete_generated_alerts=_delete_generated_alerts,
    get_query_target_options=_get_query_target_options,
    get_dataset_structure_to_index=_get_dataset_structure_to_index,
    get_does_allow_user_token_management=_get_does_allow_user_token_management,
)
