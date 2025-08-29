import os
from pathlib import Path
from typing import Optional

import boto3
from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import DatasetDescription
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, SecretStr

from connectors.athena.connector.config import AthenaConnectorConfig
from connectors.athena.connector.target import AthenaTarget
from connectors.athena.connector.secrets import AthenaSecrets
from connectors.athena.connector.tools import AthenaConnectorTools
from connectors.connector import Connector
from connectors.cache import Cache
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
    ScopeTargetDefinition,
    ScopeTargetSelector,
)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()


class CatalogModel(BaseModel):
    CatalogName: str

    model_config = ConfigDict(
        extra="allow",
    )


class ListDataCatalogsResponse(BaseModel):
    DataCatalogsSummary: list[CatalogModel]

    model_config = ConfigDict(
        extra="allow",
    )


class DatabaseModel(BaseModel):
    Name: str

    model_config = ConfigDict(
        extra="allow",
    )


class ListDatabaseResponse(BaseModel):
    DatabaseList: list[DatabaseModel]

    model_config = ConfigDict(
        extra="allow",
    )


class ColumnModel(BaseModel):
    Name: str

    model_config = ConfigDict(
        extra="allow",
    )


class TableModel(BaseModel):
    Name: str
    Columns: list[ColumnModel]

    model_config = ConfigDict(
        extra="allow",
    )


class ListTablesResponse(BaseModel):
    TableMetadataList: list[TableModel]

    model_config = ConfigDict(
        extra="allow",
    )


class WorkGroupModel(BaseModel):
    Name: str

    model_config = ConfigDict(
        extra="allow",
    )


class ListWorkGroupsResponse(BaseModel):
    WorkGroups: list[DatabaseModel]

    model_config = ConfigDict(
        extra="allow",
    )


async def _get_query_target_options(config: AthenaConnectorConfig, secrets: AthenaSecrets) -> ConnectorQueryTargetOptions:
    CATALOG = "catalog"
    DATABASE = "database"
    TABLES = "tables"
    WORKGROUP = "workgroup"

    definitions = [
        ScopeTargetDefinition(name=CATALOG),
        ScopeTargetDefinition(
            name=DATABASE,
            depends_on=CATALOG,
        ),
        ScopeTargetDefinition(
            name=TABLES,
            multiselect=True,
            depends_on=DATABASE,
        ),
        ScopeTargetDefinition(name=WORKGROUP),
    ]

    selectors: list[ScopeTargetSelector] = []
    catalog_selector = ScopeTargetSelector(type=CATALOG, values={})

    client = boto3.client("athena", region_name=config.region)
    try:
        catalog_response = ListDataCatalogsResponse.model_validate(client.list_data_catalogs())
        catalogs: list[str] = [catalog.CatalogName for catalog in catalog_response.DataCatalogsSummary]

        for catalog in catalogs:
            catalog_selector.values[catalog] = []  # type: ignore[call-overload]
            database_selector = ScopeTargetSelector(type=DATABASE, values={})

            database_response = ListDatabaseResponse.model_validate(client.list_databases(CatalogName=catalog))
            databases = [database.Name for database in database_response.DatabaseList]

            for database in databases:
                # TODO: this type error is complaining bc values can be a list and a string cannot index into a list. However, we know this is a dict from when we define the selector initially
                database_selector.values[database] = []  # type: ignore
                table_selector = ScopeTargetSelector(type=TABLES, values=[])

                table_response = ListTablesResponse.model_validate(
                    client.list_table_metadata(CatalogName=catalog, DatabaseName=database)
                )
                table_selector.values = [table.Name for table in table_response.TableMetadataList]
                # TODO: this type error is complaining bc values can be a list and a string cannot index into a list. However, we know this is a dict from when we define the selector initially
                database_selector.values[database].append(table_selector)  # type: ignore
            catalog_selector.values[catalog].append(database_selector)  # type: ignore[call-overload]

    except Exception as e:
        logger().exception("Failed to get ScopeTargetSelector options from Athena: %s", str(e))
        raise e

    try:
        response = ListWorkGroupsResponse.model_validate(client.list_work_groups())
        workgroups = [workgroup.Name for workgroup in response.WorkGroups]
        workgroup_selector = ScopeTargetSelector(type=WORKGROUP, values=workgroups)
    except Exception as e:
        raise e

    selectors = [catalog_selector, workgroup_selector]
    return ConnectorQueryTargetOptions(
        definitions=definitions,
        selectors=selectors,
    )


def _get_tools(config: AthenaConnectorConfig, target: AthenaTarget, secrets: AthenaSecrets, cache: Cache | None) -> list[Tool]:
    athena_target = AthenaTarget(**target.model_dump())
    return AthenaConnectorTools(
        AthenaConnectorConfig(**config.model_dump()),
        athena_target,
        secrets
    ).get_tools()


async def _merge_data_dictionary(
    config: AthenaConnectorConfig,
    secrets: AthenaSecrets,
    existing_dataset_descriptions: list[DatasetDescription],
    path_prefix: Optional[list[str]] = None,
) -> list[DatasetDescription]:
    if path_prefix is None:
        path_prefix = []

    data_dictionary: list[DatasetDescription] = []
    client = boto3.client("athena", region_name=config.region)
    catalog_response = ListDataCatalogsResponse.model_validate(client.list_data_catalogs())
    catalogs: list[str] = [catalog.CatalogName for catalog in catalog_response.DataCatalogsSummary]

    for catalog in catalogs:
        if path_prefix and catalog not in path_prefix:
            continue

        existing_catalog_description = next(
            (dd for dd in existing_dataset_descriptions if dd.path == [catalog]),
            None,
        )
        catalog_description = existing_catalog_description.description if existing_catalog_description else ""
        data_dictionary.append(
            DatasetDescription(
                connector=ConnectorIdEnum.ATHENA,
                path=[catalog],
                description=catalog_description,
            )
        )

        database_response = ListDatabaseResponse.model_validate(client.list_databases(CatalogName=catalog))
        databases = [database.Name for database in database_response.DatabaseList]

        for database in databases:
            if path_prefix and database not in path_prefix:
                continue

            existing_database_description = next(
                (dd for dd in existing_dataset_descriptions if dd.path == [catalog, database]),
                None,
            )
            database_description = existing_database_description.description if existing_database_description else ""
            data_dictionary.append(
                DatasetDescription(
                    connector=ConnectorIdEnum.ATHENA,
                    path=[catalog, database],
                    description=database_description,
                )
            )

            table_response = ListTablesResponse.model_validate(
                client.list_table_metadata(CatalogName=catalog, DatabaseName=database)
            )
            tables = [table.Name for table in table_response.TableMetadataList]
            for table in tables:
                if path_prefix and table not in path_prefix:
                    continue

                existing_table_description = next(
                    (dd for dd in existing_dataset_descriptions if dd.path == [catalog, database, table]),
                    None,
                )
                table_description = existing_table_description.description if existing_table_description else ""
                data_dictionary.append(
                    DatasetDescription(
                        connector=ConnectorIdEnum.ATHENA,
                        path=[catalog, database, table],
                        description=table_description,
                    )
                )

    return data_dictionary



async def _get_secrets(config: AthenaConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> AthenaSecrets | None:
    if user_token is not None:
        raise ValueError("User token is not supported for athena at this time")

    return AthenaSecrets()

AthenaConnector = Connector(
    display_name="Athena",
    id=ConnectorIdEnum.ATHENA,
    config_cls=AthenaConnectorConfig,
    query_target_type=AthenaTarget,
    description="Amazon Athena is an interactive query service that makes it easy to analyze data in Amazon S3 using standard SQL.",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "aws.svg")),
    get_secrets=_get_secrets,
    get_tools=_get_tools,
    merge_data_dictionary=_merge_data_dictionary,
    get_query_target_options=_get_query_target_options,
)
