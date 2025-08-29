from unittest.mock import MagicMock, patch

from common.models.connector_id_enum import ConnectorIdEnum
from common.models.secret import StorableSecret
from pydantic import SecretStr

from connectors.snowflake.connector.config import SnowflakeConnectorConfig
from connectors.snowflake.connector.secrets import SnowflakeSecrets
from connectors.snowflake.connector.target import SnowflakeTarget
from connectors.snowflake.connector.tools import GetSnowflakeTablesInput, SnowflakeConnectorTools

secrets = SnowflakeSecrets(password=SecretStr("test"))


def test_snowflake_target():
    target = SnowflakeTarget(databases=["foo", "bar"])
    assert target.get_dataset_paths() == [["foo"], ["bar"]]


def test_snowflake_connector_tools():
    config = SnowflakeConnectorConfig(
        id=ConnectorIdEnum.SNOWFLAKE,
        account_id="test_account",
        user="test_user",
        password=StorableSecret.model_validate("test_secret", context={"encryption_key": "mock"}),
    )
    target = SnowflakeTarget(databases=["foo", "bar"])

    tools = SnowflakeConnectorTools(config, target, secrets).get_tools()

    assert len(tools) == 3
    assert tools[0].name == "list_snowflake_databases"
    assert tools[1].name == "list_snowflake_tables"
    assert tools[2].name == "execute_snowflake_query"


async def test_list_snowflake_databases():
    with patch("connectors.snowflake.connector.tools.snowflake.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the return from the SHOW DATABASES query
        mock_cursor.fetchall.return_value = [
            # created_on, name, is_current, comment, owner, origin
            ("2025-04-28", "foo", True, "Test database", "owner1", "origin1"),
            ("2025-04-28", "bar", False, "Another database", "owner2", "origin2"),
            ("2025-04-28", "baz", True, "Yet another database", "owner3", "origin3"),
        ]

        config = SnowflakeConnectorConfig(
            id=ConnectorIdEnum.SNOWFLAKE,
            account_id="test_account",
            user="test_user",
            password=StorableSecret.model_validate("test_secret", context={"encryption_key": "mock"}),
        )
        target = SnowflakeTarget(databases=["foo", "bar"])

        tools = SnowflakeConnectorTools(config, target, secrets)
        result = await tools.list_snowflake_databases_async(None)

        assert len(result.result) == 2
        assert result.result[0]["name"] == "foo"
        assert result.result[1]["name"] == "bar"
        assert "baz" not in [db["name"] for db in result.result]


async def test_list_snowflake_tables():
    with patch("connectors.snowflake.connector.tools.snowflake.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the return from the SHOW TABLES query
        mock_cursor.fetchall.return_value = [
            # created_on, name, database, schema, table_type, comment, _, row_count, bytes, owner
            ("2025-04-28", "foo", "db1", "schema1", "type1", "Test db1", "nothing", 10, 1000, "owner1"),
            ("2025-04-28", "bar", "db1", "schema1", "type2", "Another database", "nothing", 5, 500, "owner2"),
            ("2025-04-28", "baz", "db2", "schema2", "type3", "Yet another database", "nothing", 20, 2000, "owner3"),
        ]

        config = SnowflakeConnectorConfig(
            id=ConnectorIdEnum.SNOWFLAKE,
            account_id="test_account",
            user="test_user",
            password=StorableSecret.model_validate("test_secret", context={"encryption_key": "mock"}),
        )
        target = SnowflakeTarget(databases=["db1"])

        tools = SnowflakeConnectorTools(config, target, secrets)
        result = await tools.list_snowflake_tables_async(GetSnowflakeTablesInput.model_validate({"database": "db1"}))

        assert len(result.result) == 2
        assert result.result[0]["name"] == "foo"
        assert result.result[1]["name"] == "bar"
        assert "baz" not in [db["name"] for db in result.result]
