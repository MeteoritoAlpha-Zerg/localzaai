import pytest

from common.clients.celery_client import CeleryClient, CeleryException


@pytest.mark.asyncio
async def test_disallow_message_attributes() -> None:
    celery_client = CeleryClient()

    with pytest.raises(CeleryException):
        await celery_client.instance().send_task("test", {"message_attributes": {}})
