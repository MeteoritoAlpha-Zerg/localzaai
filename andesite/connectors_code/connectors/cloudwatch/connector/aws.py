from aiobotocore.session import get_session
from connectors.cloudwatch.connector.config import CloudWatchConnectorConfig
from botocore.config import Config as BotoConfig
from aiobotocore.client import AioBaseClient

async def get_client_context(client_type: str, boto_config: BotoConfig | None = None) -> AioBaseClient:
    session = get_session()
    # NOTE: for now, our customers have a service acct for us that has the correct perms, and all these keys etc. can be None, try:
    # the default AWS auth chain will automagically work for both ECS and EKS clusters
    # later on, we may want the role to be configurable and assume role within session, but for now this will do
    return session.create_client( # type: ignore[call-overload]
        client_type,
        config=boto_config or BotoConfig()
    )
