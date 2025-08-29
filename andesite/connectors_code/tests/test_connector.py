from typing import Union

from pydantic import BaseModel

from connectors.connector import _could_be_type


def test_could_be_type_helper():
    class TestClass(BaseModel):
        pass

    assert _could_be_type(str, str)
    assert _could_be_type(Union[str, int], str)
    assert _could_be_type(Union[str, int], int)
    assert _could_be_type(list[str], list[str])
    assert _could_be_type(TestClass, BaseModel)

    assert not _could_be_type(int, str)
    assert not _could_be_type(Union[str, int], float)
    assert not _could_be_type(Union[str, int], BaseModel)
    assert not _could_be_type(list[str], str)
    assert not _could_be_type(list[str], int)
    assert not _could_be_type(list[str], list[int])
    assert not _could_be_type(BaseModel, TestClass)
