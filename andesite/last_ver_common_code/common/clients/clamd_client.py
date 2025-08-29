import io
from typing import Optional

from clamd import ClamdNetworkSocket  # type: ignore
from pydantic_settings import BaseSettings
from starlette.concurrency import run_in_threadpool


class ClamdConfig(BaseSettings):
    host: str = "clamav"
    port: int = 3310
    timeout: int = 600


class ClamdResponse(BaseSettings):
    is_virus: bool = False
    virus_name: str = ""


class ClamdClient:
    _client: Optional[ClamdNetworkSocket] = None

    @classmethod
    def initialize(cls, conf: ClamdConfig) -> None:
        cls._client = ClamdNetworkSocket(
            host=conf.host, port=conf.port, timeout=conf.timeout
        )

    @classmethod
    def instance(cls) -> "ClamdClient":
        return ClamdClient()

    @classmethod
    async def scan(cls, file_bytes: bytes) -> ClamdResponse:
        if not cls._client:
            raise Exception("ClamdClient not initialized")

        av_result = await run_in_threadpool(
            cls._client.instream, io.BytesIO(file_bytes)
        )

        if "stream" not in av_result:
            raise Exception("Error parsing antivirus scan result")

        if len(av_result["stream"]) != 2:
            raise Exception("Invalid antivirus scan result")

        if av_result["stream"][0] == "FOUND":
            return ClamdResponse(is_virus=True, virus_name=av_result["stream"][1])

        if av_result["stream"][0] != "OK":
            raise Exception("Unexpected antivirus scan result")

        return ClamdResponse(is_virus=False)
