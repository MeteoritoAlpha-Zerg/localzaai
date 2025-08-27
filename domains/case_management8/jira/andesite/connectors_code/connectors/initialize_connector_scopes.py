from typing import Any

from common.models.connectors import ConnectorScope
from opentelemetry import trace

from connectors.connector import Connector, ConnectorTargetInterface
from connectors.registry import ConnectorRegistry

tracer = trace.get_tracer("initialize_connector_scopes")


class InitializedConnectorScope:  # pragma: no cover
    connector: Connector[Any, Any, Any]
    target: ConnectorTargetInterface

    def __init__(self, connector: Connector[Any, Any, Any], target: ConnectorTargetInterface):
        self.connector = connector
        self.target = target


async def initialize_connector_scopes(
    scopes: list[ConnectorScope], user_id: str | None, encryption_key: str
) -> list[InitializedConnectorScope]:
    initialized_scopes: list[InitializedConnectorScope] = []
    for scope in scopes:
        connector = scope.connector
        target = scope.target

        connector_instance = await ConnectorRegistry.get(
            connector_id=connector, user_id=user_id, encryption_key=encryption_key
        )
        query_target = connector_instance.validate_query_target(target)

        if not query_target:
            raise Exception(
                "Invalid query target provided when initializing scope for connector %s",
                connector,
            )

        initialized_scopes.append(InitializedConnectorScope(connector=connector_instance, target=query_target))
    return initialized_scopes
