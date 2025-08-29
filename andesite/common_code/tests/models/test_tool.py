import pytest
from pydantic import BaseModel, ConfigDict

from common.models.tool import Tool


def test_tool_forbids_extra_config():
    # Test case 1: Valid input schema (default config)
    class ValidSchema(BaseModel):
        x: int
        y: int

    def dummy_function(input: ValidSchema) -> str:
        return ""

    # This should work fine
    _ = Tool(
        name="test",
        execute_fn=dummy_function,
        connector="test",
    )

    # Test case 2: Invalid input schema (extra=allow)
    class InvalidSchema(BaseModel):
        model_config = ConfigDict(extra="allow")
        x: int
        y: int

    def dummy_function_fail(input: InvalidSchema) -> str:
        return ""

    # This should raise ValueError
    with pytest.raises(ValueError):
        _ = Tool(
            name="test",
            execute_fn=dummy_function_fail,
            connector="test",
        )

    # Test case 3: Invalid input schema (extra=forbid)
    class InvalidSchema2(BaseModel):
        model_config = ConfigDict(extra="forbid")
        x: int
        y: int

    def dummy_function_fail2(input: InvalidSchema2) -> str:
        return ""

    # This should raise ValueError
    with pytest.raises(ValueError):
        _ = Tool(
            name="test",
            execute_fn=dummy_function_fail2,
            connector="test",
        )

    # This should work fine
    _ = Tool(
        name="test",
        execute_fn=dummy_function,
        connector="test",
    )


def test_tool_allows_only_one_base_model_arg():
    # Test case 1: Valid input schema (default config)
    class ValidSchema(BaseModel):
        x: int
        y: int

    def dummy_function_with_extra_arg(input: ValidSchema, test: str):
        pass

    with pytest.raises(TypeError):
        _ = Tool(
            name="test",
            execute_fn=dummy_function_with_extra_arg,  # type: ignore
            connector="test",
        )

    def dummy_function_without_base_model_arg(input: str):
        pass

    with pytest.raises(TypeError):
        _ = Tool(
            name="test",
            execute_fn=dummy_function_without_base_model_arg,
            connector="test",
        )


async def test_tool_execute_fn_signature():
    class InputSchema(BaseModel):
        x: int

    async def fn(input: InputSchema) -> str:
        return str(input.x * input.x)

    tool = Tool(
        name="square_a_number",
        connector="test",
        execute_fn=fn,
    )

    # Test case 1: Valid input
    result = await tool._execute_fn(InputSchema(x=2))
    assert result == "4"

    # Test case 2: Invalid input (missing required argument)
    with pytest.raises(ValueError):
        await tool._execute_fn(InputSchema())

    # Test case 3: Invalid input (wrong type)
    with pytest.raises(ValueError):
        await tool._execute_fn(InputSchema(x="2.1"))
