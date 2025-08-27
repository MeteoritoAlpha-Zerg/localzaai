
from common.clients.mongodb_client import MongoDbClient
from common.clients.redis_client import RedisClient
from common.jsonlogging.jsonlogger import Logging
from connectors.config import ConnectorConfigurationManager
from connectors.registry import ConnectorRegistry


logger = Logging.get_logger(__name__)

async def initialize_connector_dependencies(mongodb_database: str):
    logger().info("Initializing connector registry")
    await ConnectorConfigurationManager.instance().initialize(storage_collection=MongoDbClient().get_collection(mongodb_database, "connector_configurations"))
    await ConnectorRegistry.initialize(cache=RedisClient().get_client())
