from enum import StrEnum, auto
from typing import Any, Type

from common.jsonlogging.jsonlogger import Logging
from connectors.connector import Connector, ConnectorConfig
from connectors.connector_id_enum import ConnectorIdEnum

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

class RegistryEntry:
    connector: Connector[Any, Any]
    config: ConnectorConfig

    def __init__(self, connector: Connector[Any, Any], config: ConnectorConfig):
        self.connector = connector
        self.config = config

class ConnectorRegistry:
    """
    The ConnectorRegistry is a global singleton mapping from connector names to their types. It also serves as the
    factory for instances of connectors.
    """

    _registry: dict[ConnectorIdEnum, RegistryEntry] = {}

    @classmethod
    async def initialize(cls) -> None:
        # TODO: Load initial connector configs from mongo
        from connectors.splunk.connector.connector import SplunkConnector # type: ignore
        from connectors.athena.connector.connector import AthenaConnector # type: ignore
        from connectors.domaintools.connector.connector import DomainToolsConnector # type: ignore
        from connectors.elastic.connector.connector import ElasticConnector # type: ignore
        from connectors.sentinel_one.connector.connector import SentinelOneConnector # type: ignore
        from connectors.tenable.connector.connector import TenableConnector # type: ignore
        from connectors.equinox.connector.connector import EquinoxConnector # type: ignore

    @classmethod
    def register(
        cls,
        connector: Connector[Any, Any],
        config_cls: Type[ConnectorConfig],
    ) -> str:
        """
        Register a ConnectorInterface instance with the registry.

        :param connector_cls: The ConnectorInterface specialization type to register.
        :param config: The ConnectorConfig instance used to instantiate the ConnectorInterface.
        :return: The registration name, which is the same as the Connector.id literal.
        """
        name = connector.id
        if name in cls._registry:
            raise ConnectorRegistryException(
                error_type=ConnectorRegistryError.duplicate_registration,
                connector_id=name,
                message=f"Connector with name '{name}' is already registered"
            )

        config = config_cls.create(id=connector.id)
        logger().info("Registering connector '%s'", connector.id)
        if config is None:
            logger().error(
                "Failed to initialize connector for '%s' as it is missing config variables",
                connector.id,
            )
            return name

        cls._registry[name] = RegistryEntry(connector=connector, config=config)
        return name

    @classmethod
    async def get_connectors(cls, user_id: str | None, encryption_key: str) -> list[Connector[Any, Any]]:
        """
        Returns every connector registered and available for this user.
        """

        connectors: list[Connector[Any, Any]] = []
        for connector_id in cls._registry.keys():
            try:
                connector = await cls.get(connector_id=connector_id, user_id=user_id, encryption_key=encryption_key)
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
    ) -> Connector[Any, Any]:
        """
        Create an instance of a Connector by connector_id.
        This actually creates the connector with all the config necessary to interact with the service it's connecting to.
        """
        if connector_id not in cls._registry:
            raise ConnectorRegistryException(
                message=f"Unregistered connector",
                error_type=ConnectorRegistryError.not_registered,
                connector_id=connector_id,
            )
        entry = cls._registry[connector_id]

        connector = await entry.connector.initialize(config=entry.config, user_id=user_id, encryption_key=encryption_key)
        if not connector.get_info().available:
            raise ConnectorRegistryException(
                message=f"Unavailable connector",
                error_type=ConnectorRegistryError.not_available,
                connector_id=connector_id,
            )

        return connector
