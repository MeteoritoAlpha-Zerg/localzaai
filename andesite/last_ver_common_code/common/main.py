import logging
from pathlib import Path
from typing import Optional


from common.managers.instance_configuration.instance_configuration_manager import (
    InstanceConfigurationManager,
)


from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
from common.clients.redis_client import RedisClient, RedisConfig
from common.managers.document_storage.document_storage_manager import (
    DocumentStorageManager,
)
from common.managers.task_metadata.task_metadata_manager import (
    TaskMetadataManager,
)
from common.managers.alert_enrichments.alert_enrichment_manager import (
    AlertEnrichmentManager,
)
from common.managers.alert_groups.alert_group_manager import AlertGroupManager
from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleManager,
)
from common.managers.user.user_manager import UsersManager, UsersManagerConfig
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)

from connectors.registry import ConnectorRegistry
from core.llms.model_loader import LLMModelLoader


async def initialize_common_dependencies(
    logger: logging.Logger,
    mongodb_url: str,
    mongodb_database: str,
    redis_host: str,
    redis_port: int,
    redis_tls: bool,
    data_dictionary_path: Optional[Path] = None,
    perform_migrations: bool = False,  # Only one live service should call this to avoid multiple database migrations running at the same time
) -> None:
    """
    Responsible for setting up any and all dependencies that must be initialized for metamorph to function across services.

    These dependencies are requirements for the basic usage of the connector and core libraries

    We do NOT initialize any celery or aws clients in these common deps
    """
    logger.info("Connecting to MongoDB")
    mongo_db = MongoDbClient()
    await mongo_db.initialize(MongoDbConfig(url=mongodb_url))

    logger.info("Initializing Dataset Description Manager")
    ddm = DatasetDescriptionManager.instance()
    if data_dictionary_path:
        logger.info(
            f"Customer data dictionary provided at {data_dictionary_path}; syncing to mongo"
        )
        await ddm.load_initial_descriptions_async(data_dictionary_path)
    await ddm.initialize(
        mongo_db.get_collection(mongodb_database, "dataset_descriptions")
    )

    logger.info("Initializing Dataset Structure Manager")
    dsm = DatasetStructureManager.instance()
    await dsm.initialize(
        mongo_db.get_collection(mongodb_database, "dataset_structures")
    )

    logger.info("Initializing Document Storage Manager")
    document_storage_manager = DocumentStorageManager.instance()
    await document_storage_manager.initialize(
        mongo_db.get_collection(mongodb_database, "documents")
    )

    if perform_migrations:
        logger.info("Performing Document Migration, if necesssary")
        await document_storage_manager.migrate_exploratory_searches()

    logger.info("Initializing Task Metadata Manager")
    tmm = TaskMetadataManager.instance()
    await tmm.initialize(mongo_db.get_collection(mongodb_database, "task_metadatas"))

    logger.info("Initializing Alert Enrichment Manager")
    aem = AlertEnrichmentManager.instance()
    await aem.initialize(mongo_db.get_collection(mongodb_database, "alert_enrichments"))

    logger.info("Initializing Alert Group Manager")
    agm = AlertGroupManager.instance()
    await agm.initialize(mongo_db.get_collection(mongodb_database, "alert_groups"))

    logger.info("Initializing Prioritization Rule Manager")
    prm = PrioritizationRuleManager.instance()
    await prm.initialize(
        mongo_db.get_collection(mongodb_database, "prioritization_rules")
    )

    logger.info("Initializing Enterprise Technique Manager")
    etm = EnterpriseTechniqueManager.instance()
    await etm.initialize(
        MongoDbClient().get_collection(mongodb_database, "mitre_enterprise_tactics"),
    )

    logger.info("Initializing Users DAO")
    UsersManager.initialize(UsersManagerConfig(mongodb_database=mongodb_database))

    logger.info("Initializing Instance Configuration Manager")
    instance_configuration_manager = InstanceConfigurationManager.instance()
    await instance_configuration_manager.initialize(
        mongo_db.get_collection(mongodb_database, "instance_configuration")
    )

    logger.info("Initializing connector registry")
    await ConnectorRegistry.initialize()

    logger.info("Initializing Redis client")
    redis = RedisClient()
    redis_cfg = RedisConfig(host=redis_host, port=redis_port, tls=redis_tls)
    await redis.initialize(redis_cfg)

    logger.info("Initializing LLM model loader")
    model_loader = LLMModelLoader()
    model_loader.initialize()
