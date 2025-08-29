import pytest
from pydantic import SecretStr, ValidationError

from common.models.secret import METAMORPH_ENCRYPTION_PREFIX, StorableSecret

MOCK_ENCRYPTED_SECRET = METAMORPH_ENCRYPTION_PREFIX + "test"
MOCK_UNENCRYPTED_SECRET = "test"


def test_model_creation():
    assert StorableSecret(secret=MOCK_ENCRYPTED_SECRET).secret == MOCK_ENCRYPTED_SECRET
    assert StorableSecret.model_validate(MOCK_ENCRYPTED_SECRET).secret == MOCK_ENCRYPTED_SECRET
    assert StorableSecret.model_validate({"secret": MOCK_ENCRYPTED_SECRET}).secret == MOCK_ENCRYPTED_SECRET

    with pytest.raises(ValidationError):
        StorableSecret.model_validate(MOCK_UNENCRYPTED_SECRET)
    with pytest.raises(ValidationError):
        StorableSecret.model_validate(MOCK_UNENCRYPTED_SECRET, context={"encryption_key": 1})
    with pytest.raises(ValidationError):
        StorableSecret.model_validate("", context={"encryption_key": "dummy"})

    assert StorableSecret.model_validate(
        MOCK_UNENCRYPTED_SECRET, context={"encryption_key": "dummy key"}
    ).secret.startswith(METAMORPH_ENCRYPTION_PREFIX)

    assert (
        StorableSecret.model_validate(MOCK_UNENCRYPTED_SECRET, context={"encryption_key": "dummy key"}).decrypt(
            "different key"
        )
        is None
    )
    assert StorableSecret.model_validate(MOCK_UNENCRYPTED_SECRET, context={"encryption_key": "dummy key"}).decrypt(
        "dummy key"
    ) == SecretStr(MOCK_UNENCRYPTED_SECRET)
