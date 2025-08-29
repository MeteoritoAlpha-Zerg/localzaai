import logging
from pathlib import Path

from pydantic import SecretStr

from common.clients.azure_embed_client import AzureConfig, AzureEmbedClient
from common.clients.milvus_vdb_client import MilvusConfig, MilvusVecDBClient
from common.clients.mongodb_client import MongoDbClient, MongoDbConfig
from common.clients.redis_client import RedisClient, RedisConfig
from common.managers.alert_attributes.alert_attribute_manager import (
    AlertAttributeManager,
)
from common.managers.alert_enrichments.alert_enrichment_manager import (
    AlertEnrichmentManager,
)
from common.managers.alert_groups.alert_group_manager import AlertGroupManager
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.managers.document_storage.document_storage_manager import (
    DocumentStorageManager,
)
from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)
from common.managers.instance_configuration.instance_configuration_manager import (
    InstanceConfigurationManager,
)
from common.managers.investigations.investigation_manager import InvestigationManager
from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleManager,
)
from common.managers.task_metadata.task_metadata_manager import (
    TaskMetadataManager,
)
from common.managers.user.user_manager import UsersManager, UsersManagerConfig


async def initialize_common_dependencies(
    logger: logging.Logger,
    mongodb_url: str,
    mongodb_database: str,
    redis_host: str,
    redis_port: int,
    redis_tls: bool,
    milvus_url: str | None = None,
    milvus_token: SecretStr | None = None,
    embed_model_url: str | None = None,
    embed_model_token: SecretStr | None = None,
    embed_model_api_version: str | None = None,
    data_dictionary_path: Path | None = None,
    perform_migrations: bool = False,  # Only one live service should call this to avoid multiple database migrations running at the same time
) -> None:
    """Set up any and all dependencies that must be initialized for metamorph to function across services.

    These dependencies are requirements for the basic usage of the connector and core libraries

    We do NOT initialize any celery, aws, LLM clients (LLMModelLoader) in these common deps
    """
    logger.info("Connecting to MongoDB")
    mongo_db = MongoDbClient()
    await mongo_db.initialize(MongoDbConfig(url=mongodb_url))

    logger.info("Initializing Dataset Description Manager")
    ddm = DatasetDescriptionManager.instance()
    if data_dictionary_path:
        logger.info(f"Customer data dictionary provided at {data_dictionary_path}; syncing to mongo")
        await ddm.load_initial_descriptions_async(data_dictionary_path)
    await ddm.initialize(mongo_db.get_collection(mongodb_database, "dataset_descriptions"))

    logger.info("Initializing Dataset Structure Manager")
    dsm = DatasetStructureManager.instance()
    await dsm.initialize(mongo_db.get_collection(mongodb_database, "dataset_structures"))

    logger.info("Initializing Document Storage Manager")
    document_storage_manager = DocumentStorageManager.instance()
    await document_storage_manager.initialize(mongo_db.get_collection(mongodb_database, "documents"))

    logger.info("Initializing Investigation Manager")
    investigation_manager = InvestigationManager.instance()
    await investigation_manager.initialize(mongo_db.get_collection(mongodb_database, "investigations"))

    logger.info("Initializing Task Metadata Manager")
    tmm = TaskMetadataManager.instance()
    await tmm.initialize(mongo_db.get_collection(mongodb_database, "task_metadatas"))

    logger.info("Initializing Alert Enrichment Manager")
    aem = AlertEnrichmentManager.instance()
    await aem.initialize(mongo_db.get_collection(mongodb_database, "alert_enrichments"))

    logger.info("Initializing Alert Group Manager")
    agm = AlertGroupManager.instance()
    await agm.initialize(mongo_db.get_collection(mongodb_database, "alert_groups"))
    if perform_migrations:
        logger.info("Performing Alert Group Migration, if necesssary")
        await agm.migrate()

    logger.info("Initializing Attribute Manager")
    aam = AlertAttributeManager.instance()
    await aam.initialize(mongo_db.get_collection(mongodb_database, "alert_attributes"))

    logger.info("Initializing Prioritization Rule Manager")
    prm = PrioritizationRuleManager.instance()
    await prm.initialize(mongo_db.get_collection(mongodb_database, "prioritization_rules"))

    logger.info("Initializing Enterprise Technique Manager")
    etm = EnterpriseTechniqueManager.instance()
    await etm.initialize(
        mongo_db.get_collection(mongodb_database, "mitre_enterprise_tactics"),
    )

    logger.info("Initializing Users DAO")
    UsersManager.initialize(UsersManagerConfig(mongodb_database=mongodb_database))

    logger.info("Initializing Instance Configuration Manager")
    instance_configuration_manager = InstanceConfigurationManager.instance()
    await instance_configuration_manager.initialize(mongo_db.get_collection(mongodb_database, "instance_configuration"))

    logger.info("Initializing Redis client")
    redis = RedisClient()
    redis_cfg = RedisConfig(host=redis_host, port=redis_port, tls=redis_tls)
    await redis.initialize(redis_cfg)

    if milvus_url and milvus_token:
        logger.info("Initializing Milvus vector database client")
        milvus = MilvusVecDBClient()
        milvus_cfg = MilvusConfig(vecdb_milvus_url=milvus_url, vecdb_milvus_token=milvus_token)
        await milvus.initialize(config=milvus_cfg)
        if await milvus.has_connection():
            logger.info("Milvus connection verified.")
    else:
        logger.warning("Milvus credentials not provided; skipping vector DB setup")

    if embed_model_url and embed_model_token and embed_model_api_version:
        logger.info("Initializing Embedding model client")
        await AzureEmbedClient.initialize(
            config=AzureConfig(
                url=embed_model_url,
                token=embed_model_token,
                api_version=embed_model_api_version,
            ),
        )
    else:
        logger.warning("Embedding model credentials not provided; skipping embedding model setup")
