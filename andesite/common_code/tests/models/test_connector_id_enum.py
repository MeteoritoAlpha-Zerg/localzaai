import pytest

from common.models.connector_id_enum import ConnectorIdEnum


def test_domaintools_migration():
    assert ConnectorIdEnum("domaintools") == ConnectorIdEnum.DOMAINTOOLS
    assert ConnectorIdEnum("DomainTools") == ConnectorIdEnum.DOMAINTOOLS

    # unknown enum throws
    with pytest.raises(ValueError):
        ConnectorIdEnum("unknown")


def test_auto_ids():
    assert ConnectorIdEnum("DOMAINTOOLS") == ConnectorIdEnum.DOMAINTOOLS
    assert ConnectorIdEnum("DomainTools") == ConnectorIdEnum.DOMAINTOOLS

    assert ConnectorIdEnum("sentinel_one") == ConnectorIdEnum.SENTINEL_ONE

    # unknown enum throws
    with pytest.raises(ValueError):
        ConnectorIdEnum("unknown")


def test_safe_parse():
    assert ConnectorIdEnum.safe_parse("DOMAINTOOLS") == ConnectorIdEnum.DOMAINTOOLS

    assert not ConnectorIdEnum.safe_parse("unknown")
