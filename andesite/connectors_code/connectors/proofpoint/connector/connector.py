import asyncio
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
from typing import Optional

from common.models.connector_id_enum import ConnectorIdEnum
from common.models.tool import Tool
from pydantic import SecretStr

from connectors.connector import Connector, ConnectorTargetInterface
from connectors.cache import Cache
from connectors.proofpoint.client.proofpoint_instance import Interval, ProofpointInstance, SegmentTimeUnit, _segment_interval_by_unit
from connectors.proofpoint.connector.config import ProofpointConnectorConfig
from connectors.proofpoint.connector.target import ProofpointTarget
from connectors.proofpoint.connector.secrets import ProofpointSecrets
from connectors.proofpoint.connector.tools import ProofpointConnectorTools
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure


async def _check_connection(config: ProofpointConnectorConfig, secrets: ProofpointSecrets) -> bool:
    instance = ProofpointInstance(
        api_host=config.api_host,
        principal=config.principal,
        token=secrets.token,
        request_timeout=config.request_timeout,
        max_retries=config.max_retries,
    )
    return await instance.check_connection_async()


def _get_tools(config: ProofpointConnectorConfig, target: ProofpointTarget, secrets: ProofpointSecrets, cache: Cache | None) -> list[Tool]:
    return ProofpointConnectorTools(target, config, secrets, cache).get_tools()



async def _get_secrets(config: ProofpointConnectorConfig, encryption_key: str, user_token: SecretStr | None) -> ProofpointSecrets | None:
    token = user_token if user_token is not None else config.token.decrypt(encryption_key=encryption_key)

    if token is None:
        return None

    return ProofpointSecrets(token=token)

async def _index_campaigns(config: ProofpointConnectorConfig, secrets: ProofpointSecrets) -> list[DatasetStructure]:
    instance = ProofpointInstance(
        api_host=config.api_host,
        principal=config.principal,
        token=secrets.token,
        request_timeout=config.request_timeout,
        max_retries=config.max_retries,
    )
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=30)
    interval = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    dataset_keys = _segment_interval_by_unit(interval, SegmentTimeUnit.DAY)
    existing_datasets = await DatasetStructureManager.instance().get_all_dataset_structures_async(ConnectorIdEnum.PROOFPOINT)
    structure: list[DatasetStructure] = []

    # Check each day interval to see if we already have data for that day
    for day_key in dataset_keys:
        day_interval = Interval(interval=day_key)

        # Check if any existing dataset overlaps with this day
        has_existing_data = any([day_interval.overlaps_with(Interval(interval=existing_dataset.dataset)) for existing_dataset in existing_datasets])

        # Only fetch data if we don't already have data for this day
        if not has_existing_data:
            uncached_data = await instance._get_campaign_ids_unsafe(interval=day_key, size=200)
            structure.append(
                DatasetStructure(
                    connector=ConnectorIdEnum.PROOFPOINT,
                    dataset=day_key,
                    attributes= {"campaigns": [c.model_dump() for c in uncached_data.campaigns]}
                )
            )

    return structure


async def _get_dataset_structure_to_index(
    config: ProofpointConnectorConfig, secrets: ProofpointSecrets, dataset_target: Optional[ConnectorTargetInterface] = None
) -> list[DatasetStructure]:
    return await _index_campaigns(config, secrets)



ProofpointConnector = Connector(
    display_name="Proofpoint Threat Intelligence",
    beta=True,
    id=ConnectorIdEnum.PROOFPOINT,
    config_cls=ProofpointConnectorConfig,
    query_target_type=ProofpointTarget,
    get_secrets=_get_secrets,
    description="Connector for Proofpoint Threat Intelligence",
    logo_path=Path(os.path.join(os.path.dirname(__file__), "proofpoint.svg")),
    get_tools=_get_tools,
    check_connection=_check_connection,
    get_dataset_structure_to_index=_get_dataset_structure_to_index,
)
