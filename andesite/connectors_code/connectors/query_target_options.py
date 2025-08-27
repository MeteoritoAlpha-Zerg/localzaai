from typing import Optional, Union

from pydantic import BaseModel


class ScopeTargetDefinition(BaseModel):
    """
    Represents the relationships, dependencies and functionality of each selector.
    """

    name: str
    multiselect: bool = False
    depends_on: Optional[str] = None


class ScopeTargetSelector(BaseModel):
    """
    This defines the possible tree values that can be selected for a given dataset target.
    """

    type: str
    values: Union[dict[str, list["ScopeTargetSelector"]], list[str]]


class ConnectorQueryTargetOptions(BaseModel):
    definitions: list[ScopeTargetDefinition]
    selectors: list[ScopeTargetSelector]
