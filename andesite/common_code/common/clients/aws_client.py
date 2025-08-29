import boto3
from botocore.client import BaseClient
from pydantic import SecretStr
from pydantic_settings import BaseSettings

"""
This module is responsible for managing the AWS clients used by the application.
It provides a way to initialize the clients with the appropriate configuration.
"""


class AWSLocalConfig(BaseSettings):
    aws_local_endpoint: str | None = None
    aws_local_access_key_id: SecretStr | None = None
    aws_local_secret_access_key: SecretStr | None = None
    aws_local_region_name: str | None = None


class AWSClient:
    _s3_client: BaseClient | None = None

    @classmethod
    def initialize(cls, cfg: AWSLocalConfig):
        if cfg.aws_local_endpoint:
            client_params = {
                "endpoint_url": cfg.aws_local_endpoint,
                "aws_access_key_id": cfg.aws_local_access_key_id.get_secret_value()
                if cfg.aws_local_access_key_id
                else "",
                "aws_secret_access_key": cfg.aws_local_secret_access_key.get_secret_value()
                if cfg.aws_local_secret_access_key
                else "",
                "region_name": cfg.aws_local_region_name,
            }

            cls._s3_client = boto3.client("s3", **client_params)  # type: ignore[call-overload]
        else:
            cls._s3_client = boto3.client("s3")

    @classmethod
    def get_s3_client(cls) -> BaseClient:
        if not cls._s3_client:
            raise ValueError("AWSClients is not initialized.")

        return cls._s3_client
