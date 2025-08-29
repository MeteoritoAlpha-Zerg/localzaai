from unittest.mock import MagicMock, patch

from connectors.athena.connector.target import AthenaTarget
from connectors.athena.connector.tools import AthenaConnectorTools


@patch("connectors.athena.connector.tools.AthenaConnectorTools.list_tables")
@patch("connectors.athena.connector.tools.AthenaConnectorTools.get_athena_table_description_async")
@patch("connectors.athena.connector.tools.AthenaConnectorTools.get_athena_column_descriptions_async")
async def test_athena_schema(m1, m2, m3):
    schema = await AthenaConnectorTools(
        athena_config=MagicMock(), target=AthenaTarget(), secrets=MagicMock()
    )._get_schema()

    assert isinstance(schema, str)
