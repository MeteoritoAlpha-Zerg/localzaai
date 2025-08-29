from typing import Annotated, List, Optional, TypeVar

from pydantic import Field

OptionalStr = Annotated[Optional[str], Field(default=None)]
OptionalBool = Annotated[Optional[bool], Field(default=None)]
OptionalInt = Annotated[Optional[int], Field(default=None)]

T = TypeVar("T")
OptionalList = Annotated[Optional[List[T]], Field(default_factory=list)]
U = TypeVar("U")
OptionalObj = Annotated[Optional[U], Field(default=None)]
