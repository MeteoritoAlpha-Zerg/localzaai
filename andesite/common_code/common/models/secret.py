import base64
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, SecretStr, field_validator, model_validator

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


def get_fernet(key: str) -> Fernet:
    """
    Returns crypto instance to encrypt/decrypt data
    """
    # Key must be 32 bytes long
    return Fernet(base64.urlsafe_b64encode((key.encode() * 32)[:32]))


METAMORPH_ENCRYPTION_PREFIX = "__mm_"
"""
A prefix provided to strings so we can safely assume if we have already encrypted them or not
"""


class StorableSecret(BaseModel):
    """
    A secret that will be encrypted automatically and can be manually be decrypted
    This ensures we store our secrets encrypted.

    The following is an example of use:
    ```
    secret = StorableSecret.model_validate({"secret": already_encrypted_secret})
    secret = StorableSecret.model_validate({"secret": unencrypted_secret}, context={"encryption_key": encryption_key})

    secret_str = secret.decrypt(encryption_key=encryption_key)
    ```
    """

    secret: str

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"secret": data}
        return data

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, secret: str, info: Any) -> str:
        # If we receive a string that starts with our expected prefix, assume it is already encrypted
        if secret.startswith(METAMORPH_ENCRYPTION_PREFIX):
            return secret

        encryption_key = None
        if isinstance(info.context, dict):
            encryption_key = info.context.get("encryption_key")
        if encryption_key is None or not isinstance(encryption_key, str):
            raise ValueError("Encryption key string is required context")
        encrypted_secret = cls._encrypt(encryption_key=encryption_key, secret=secret)
        if encrypted_secret is None:
            raise ValueError("Unable to encrypt empty secret")
        return METAMORPH_ENCRYPTION_PREFIX + encrypted_secret.decode()

    @classmethod
    def _encrypt(cls, encryption_key: str, secret: str) -> "bytes | None":
        if secret == "":
            return None
        return get_fernet(encryption_key).encrypt(secret.removeprefix(METAMORPH_ENCRYPTION_PREFIX).encode())

    def decrypt(self, encryption_key: str) -> None | SecretStr:
        """
        Decrypts this secret

        NEVER store or log this token anywhere
        """
        try:
            return SecretStr(
                get_fernet(encryption_key).decrypt(self.secret.removeprefix(METAMORPH_ENCRYPTION_PREFIX)).decode()
            )
        except InvalidToken:
            logger().error("Invalid token decryption. Verify encryption key has not changed!")
            return None
        except Exception as exc:
            logger().error("Unknown error decrypting token", exc_info=exc)
            return None
