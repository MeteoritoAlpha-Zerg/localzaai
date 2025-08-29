from pydantic import Field

from connectors.connector import ConnectorTargetInterface


class SnowflakeTarget(ConnectorTargetInterface):
    # List of Snowflake databases to target
    databases: list[str] = Field(default=[], description="List of database names to target")

    def get_dataset_paths(self) -> list[list[str]]:
        # Each database is one dataset path
        return [[db] for db in self.databases]
