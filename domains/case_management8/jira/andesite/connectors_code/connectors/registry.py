from enum import StrEnum, auto
import importlib
from typing import Any

from redis.asyncio.client import Redis

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum

from connectors.config import ConnectorConfigurationManager
from connectors.connector import Connector
from connectors.cache import Cache

logger = Logging.get_logger(__name__)


class ConnectorRegistryError(StrEnum):
    not_registered = auto()
    not_available = auto()
    duplicate_registration = auto()
    invalid_token = auto()
    invalid_query_target_type = auto()


class ConnectorRegistryException(Exception):
    """
    Exception type raised by ConnectorRegistry.
    """

    def __init__(self, message: str, error_type: ConnectorRegistryError, connector_id: str):
        super().__init__(message)
        self.error_type = error_type
        self.connector_id = connector_id

class ConnectorRegistry:
    """
    The ConnectorRegistry is a global singleton mapping from connector names to their types. It also serves as the
    factory for instances of connectors.
    """

    _registry: dict[ConnectorIdEnum, Connector[Any, Any, Any]] = {}
    _cache: Cache

    @classmethod
    async def initialize(cls, cache: Redis | None = None) -> None:
        connector_ids = [connector_id_enum.value for connector_id_enum in ConnectorIdEnum]
        for connector_id in connector_ids:
            logger().info(f"Registering Connector: {connector_id}")
            try:
                module = importlib.import_module(f"connectors.{connector_id}.connector")
                connector = getattr(module, "Connector")
                if connector is None:
                    logger().warning(f"Unable to register connector missing default Connector export: {connector_id}")
                else:
                    await cls.register(connector=connector)
            except Exception:
                logger().exception(f"Failed to register connector {connector_id}. It will be unavailable for this site.")
        cls._cache = Cache(cache=cache)

    @classmethod
    async def register(
        cls,
        connector: Connector[Any, Any, Any],
    ) -> str:
        """
        Register a ConnectorInterface instance with the registry.

        :param connector_cls: The ConnectorInterface specialization type to register.
        :return: The registration name, which is the same as the Connector.id literal.
        """
        name = connector.id
        if name in cls._registry:
            raise ConnectorRegistryException(
                error_type=ConnectorRegistryError.duplicate_registration,
                connector_id=name,
                message=f"Connector with name '{name}' is already registered",
            )

        # Make sure a config entry is present in mongo for connectors we support
        await ConnectorConfigurationManager.instance().ensure_configuration_entry_present(connector=connector.id)

        cls._registry[name] = connector
        return name

    @classmethod
    async def get_connectors(
        cls, user_id: str | None, encryption_key: str
    ) -> list[Connector[Any, Any, Any]]:
        """
        Returns every connector registered and available for this user.
        """

        connectors: list[Connector[Any, Any, Any]] = []
        for connector_id in cls._registry:
            try:
                connector = await cls.get(
                    connector_id=connector_id, user_id=user_id, encryption_key=encryption_key
                )
                connectors.append(connector)
            except ConnectorRegistryException as cre:
                if cre.error_type == ConnectorRegistryError.not_available:
                    logger().info("Skipping unavailable connector: %s", connector_id)
                else:
                    raise cre
        return connectors

    @classmethod
    async def get(
        cls, connector_id: ConnectorIdEnum, user_id: str | None, encryption_key: str
    ) -> Connector[Any, Any, Any]:
        """
        Create an instance of a Connector by connector_id.
        This actually creates the connector with all the config necessary to interact with the service it's connecting to.
        """
        if connector_id not in cls._registry:
            raise ConnectorRegistryException(
                message="Unregistered connector",
                error_type=ConnectorRegistryError.not_registered,
                connector_id=connector_id,
            )
        entry = cls._registry[connector_id]

        stored_config = await ConnectorConfigurationManager.instance().get_configuration(connector=connector_id)
        connector = await entry.initialize(
            config=stored_config, cache=cls._cache, user_id=user_id, encryption_key=encryption_key
        )
        return connector
