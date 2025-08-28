import base64
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum

logger = Logging.get_logger(__name__)


def get_fernet(key: str) -> Fernet:
    """
    Returns crypto instance to encrypt/decrypt data
    """
    # Key must be 32 bytes long
    return Fernet(base64.urlsafe_b64encode((key.encode() * 32)[:32]))


class TokenInterface(BaseModel):
    model_config = ConfigDict(extra="allow")


class Tokens(TokenInterface):
    @staticmethod
    def encrypt_token(encryption_key: str, token: str) -> str | None:
        if token == "":
            return None
        return get_fernet(encryption_key).encrypt(token.encode()).decode()

    def decrypt_token(self, encryption_key: str, token_name: ConnectorIdEnum) -> None | SecretStr:
        """
        Decrypts the user's splunk token

        NEVER store or log this token anywhere
        """
        try:
            token = getattr(self, str(token_name))
        except AttributeError:
            logger().error(f"Token {token_name} not found in user tokens")
            return None

        try:
            return SecretStr(get_fernet(encryption_key).decrypt(token).decode())
        except InvalidToken:
            logger().error("Invalid token decryption, verify encryption key has not changed!")
            return None
        except Exception as exc:
            logger().error("Unknown error decrypting token", exc_info=exc)
            return None


class User(BaseModel):  # pragma: no cover
    id: str
    email: str
    theme_preference: str = "default"
    timezone_preference: str = "UTC"
    tokens: Tokens = Field(
        default_factory=lambda: Tokens(),
        description=("User specific connector tokens. A connector's global tokens should NOT be stored here."),
    )

    @staticmethod
    def from_mongo(user: Any) -> "User | None":
        if user is not None:
            user_info = dict(user)
            user_info["id"] = str(
                user_info.pop(
                    "_id",
                )
            )
            tokens = Tokens.model_validate(user_info.pop("tokens", {}))
            return User(tokens=tokens, **user_info)

        return None

    def to_mongo(self) -> Any:
        user = self.model_dump()
        user["_id"] = str(user.pop("id", None))

        return user
