from typing import Any

from connectors.connector import Connector, ConnectorTargetInterface
from connectors.connector_id_enum import ConnectorIdEnum
from pydantic import BaseModel


ConnectorTarget = ConnectorTargetInterface


class ConnectorScope(BaseModel):  # pragma: no cover
    connector: ConnectorIdEnum
    target: dict[str, Any] = {}


InitializedConnector = Connector[Any, Any]


class InitializedConnectorScope:  # pragma: no cover
    connector: InitializedConnector
    target: ConnectorTargetInterface

    def __init__(
        self, connector: InitializedConnector, target: ConnectorTargetInterface
    ):
        self.connector = connector
        self.target = target
