import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.investigations.investigation_manager import InvestigationManager
from common.managers.investigations.investigation_model import Investigation


@pytest.fixture(autouse=True)
async def investigation_manager():
    manager = InvestigationManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["investigations"]
    await manager.initialize(collection)
    return manager


@pytest.mark.asyncio
async def test_get_all_investigations_none(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    all_investigations = await investigation_manager.get_all_abbreviated_investigations_async(user_id)
    assert len(all_investigations) == 0


@pytest.mark.asyncio
async def test_upsert_and_get_investigation(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    investigation = Investigation(
        id="1234",
        title="TestInvestigation",
        user_id=user_id,
    )
    await investigation_manager.upsert_investigation_async(investigation)

    retrieved_investigation = await investigation_manager.get_investigation_async("1234", user_id)
    assert retrieved_investigation is not None
    assert retrieved_investigation.id == "1234"
    assert retrieved_investigation.title == "TestInvestigation"
    assert retrieved_investigation.user_id == user_id


@pytest.mark.asyncio
async def test_update_investigation(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    investigation = Investigation(
        id="1234",
        title="TestInvestigation",
        user_id=user_id,
    )
    await investigation_manager.upsert_investigation_async(investigation)

    # Update the investigation
    investigation.title = "UpdatedInvestigation"
    updated_investigation = await investigation_manager.upsert_investigation_async(investigation)

    assert updated_investigation.title == "UpdatedInvestigation"
    assert updated_investigation.user_id == user_id


@pytest.mark.asyncio
async def test_archive_investigation(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    investigation = Investigation(
        id="1234",
        title="TestInvestigation",
        user_id=user_id,
    )
    await investigation_manager.upsert_investigation_async(investigation)

    # Archive the investigation
    result = await investigation_manager.archive_investigation_async("1234", user_id)
    assert result is True

    # Ensure the investigation is no longer retrievable
    archived_investigation = await investigation_manager.get_investigation_async("1234", user_id)
    assert archived_investigation is None


@pytest.mark.asyncio
async def test_get_all_investigations(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    investigation1 = Investigation(
        id="1234",
        title="Investigation1",
        user_id=user_id,
    )
    investigation2 = Investigation(
        id="5678",
        title="Investigation2",
        user_id=user_id,
    )
    await investigation_manager.upsert_investigation_async(investigation1)
    await investigation_manager.upsert_investigation_async(investigation2)

    all_investigations = await investigation_manager.get_all_abbreviated_investigations_async(user_id)
    assert len(all_investigations) == 2
    assert all_investigations[0].id in ["1234", "5678"]
    assert all_investigations[1].id in ["1234", "5678"]


@pytest.mark.asyncio
async def test_archive_all_investigations(
    investigation_manager: InvestigationManager,
) -> None:
    user_id = "user123"
    investigation1 = Investigation(
        id="1234",
        title="Investigation1",
        user_id=user_id,
    )
    investigation2 = Investigation(
        id="5678",
        title="Investigation2",
        user_id=user_id,
    )
    await investigation_manager.upsert_investigation_async(investigation1)
    await investigation_manager.upsert_investigation_async(investigation2)

    # Archive all investigations for the user
    result = await investigation_manager.archive_all_investigations_async(user_id)
    assert result is True

    # Ensure all investigations are no longer retrievable
    archived_investigation1 = await investigation_manager.get_investigation_async("1234", user_id)
    archived_investigation2 = await investigation_manager.get_investigation_async("5678", user_id)
    assert archived_investigation1 is None
    assert archived_investigation2 is None
