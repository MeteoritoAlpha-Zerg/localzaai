from pydantic import BaseModel

from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    Serialize JSON keys with lower camel-case names.

    I.E. some_key will resolve to someKey in its JSON representation.
    """

    class Config:
        alias_generator = to_camel
        populate_by_name = True
