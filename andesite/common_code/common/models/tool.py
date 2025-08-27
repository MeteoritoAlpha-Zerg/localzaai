import asyncio
import inspect
from collections.abc import Awaitable, Callable, Coroutine
from typing import (
    Any,
    get_type_hints,
)

from opentelemetry import trace
from pydantic import BaseModel, PrivateAttr, ValidationError
from pydantic.fields import FieldInfo

from common.jsonlogging.jsonlogger import Logging
from common.models.metadata import QueryResultMetadata

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class ToolException(Exception):
    pass


SupportedToolResultValue = Any | QueryResultMetadata


class ToolResult(BaseModel):
    """
    ToolResult represent a detailed output of a Tool

    :result: is assumed to be a data structure that LLM's can easily interpret or an instance of `QueryResultMetadata` for us to reformat into a tabular view
    :additional_context: can be used to provide additional information to the llm about the tool's execution
    """

    result: SupportedToolResultValue
    additional_context: str | None = None


# Tools can return either simple types or the full ToolResult to provide extra information of their outputs
ToolReturnValue = SupportedToolResultValue | ToolResult
ToolReturn = ToolReturnValue | Coroutine[Any, Any, ToolReturnValue]
Executable = Callable[[BaseModel], ToolReturn]

"""
Private types that are internal to the library and should never be used directly
"""


class ToolOutput(BaseModel):
    """
    The final and fully processed output that will be returned to the agent.

    This model should NOT be manually constructed and will returned by any tools. This is solely internal to the agent framework.
    """

    raw_result: SupportedToolResultValue
    """
    This is the raw results we get back from running the tool and what should be returned to any 3rd parties (e.g. backend) using this connector
    """
    agent_result: Any
    """
    This is the result that we will pass to the agent and is assumed to be of a form that an LLM can easily comprehend
    """
    additional_agent_context: str = ""
    """
    This allows for the tool to pass back custom context to the agent that may be useful after a tool call.

    e.g. "This tool only returns the first 100 elements of this query."
    """


class ExecuteQuerySpecialization(BaseModel):
    query_prompt: str
    """
    An additional prompt we can provide to advise the agent how to successfully construct the expected query.

    This prompt should include helpful context for how to effectively and efficiently query w/ the associated DSL
    """
    get_schema: Callable[[], Awaitable[str]]
    """
    A function that can be used to retrieve the schema for this dataset with full associated descriptions
    """
    dataset_paths: list[list[str]]
    """
    The dataset paths of the query target the tools are scoped to
    """


type Specialization = ExecuteQuerySpecialization
"""
A specialization allows a tool to provide additional functionality that can be utilized as needed by the core engine to provide advanced functionality/workflows
"""


class Tool(BaseModel):
    """
    This base class of tool contains logic needed across all usages of tools
    """

    name: str
    connector: str
    specialization: Specialization | None = None
    _input_schema: type[BaseModel] = PrivateAttr()
    _execute_fn: Executable = PrivateAttr()
    _timeout_seconds: float | None = 60

    def _validate_parameters(self, name: str, execute_fn: Callable[[Any], ToolReturn]) -> type[BaseModel]:
        """
        Ensure execute_fn only takes single parameter that is a subclass of base model

        Returns validated parameter type
        """
        sig = inspect.signature(execute_fn)
        params = list(sig.parameters.values())

        # Ensure the function has exactly one argument
        if len(params) != 1:
            raise TypeError(f"`execute_fn` for tool {name} must have exactly one argument, but got {len(params)}.")

        param_type = get_type_hints(execute_fn).get(params[0].name)
        if not (inspect.isclass(param_type) and issubclass(param_type, BaseModel)):
            raise TypeError(
                f"`execute_fn` for tool {name} must take a single argument of type `BaseModel`, but got {param_type}."
            )

        if "extra" in param_type.model_config and param_type.model_config.get("extra") != "ignore":
            raise ValueError("extra args not allowed in tool input_schema")

        return param_type

    def __init__(
        self,
        *,
        name: str,
        # We perform our own type validation on the execute function as python isn't smart enough to handle BaseModel subclass parameters correctly
        execute_fn: Callable[[Any], ToolReturn],
        connector: str,
        specialization: Specialization | None = None,
        timeout_seconds: float | None = 60,
        **kwargs: Any,
    ):
        super().__init__(name=name, connector=connector, specialization=specialization, **kwargs)

        # Ensure the 1 argument is a subclass of BaseModel
        self._input_schema = self._validate_parameters(name=name, execute_fn=execute_fn)

        # We have performed all type checks to guarantee this cast is safe
        self._execute_fn = execute_fn
        self._timeout_seconds = timeout_seconds

    # NOTE: this conflicts with the input parameter validation, as validation forces "extra" to be "ignore"
    def allows_extra_parameters(self) -> bool:
        extra_param_config = self._input_schema.model_config.get("extra")
        return extra_param_config != "forbid"

    def get_parameters(self) -> dict[str, FieldInfo]:
        return self._input_schema.model_fields

    def get_input_json_schema(self) -> dict[str, Any]:
        return self._input_schema.model_json_schema()

    def get_input_docstring(self) -> str:
        return self._input_schema.__doc__ or f"{self.name} Tool"

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Execute the tool with the given arguments. Performs validation before calling the tool function.
        """
        try:
            # extra arguments get automatically removed since we have specified input_schema must always use default behavior of extra="ignore"
            # also model_validate handles simple conversions. for example, passing x="1" when x is defined as an int will convert automatically
            input_model = self._input_schema.model_validate(kwargs)
        except ValidationError as e:
            # Simplify the error message for the LLM to process better
            errors = e.errors()
            simplified_errors = [f"Field '{err['loc'][0]}': {err['msg']}" for err in errors]
            raise ValueError("Input error: " + "\n".join(simplified_errors)) from e

        try:
            result = self._execute_fn(input_model)
            if inspect.iscoroutine(result):
                result = await asyncio.wait_for(result, timeout=self._timeout_seconds)
        except TimeoutError as e:
            logger().warning(
                "Timed out after waiting %d seconds for tool '%s' call to return", self._timeout_seconds, self.name
            )
            raise ToolException(
                f"Tool call timed out after {self._timeout_seconds} seconds. "
                "This may be due to requesting too much data or using inefficient parameters. "
                "Consider narrowing the scope or optimizing your input to improve performance."
            ) from e
        except Exception as e:
            logger().exception("Error executing tool")
            raise e

        if not isinstance(result, ToolResult):
            result = ToolResult(result=result)

        agent_result_value = result.result
        if isinstance(agent_result_value, QueryResultMetadata):
            rows = (agent_result_value.results or []).copy()
            columns = (agent_result_value.column_headers or []).copy()
            agent_result_value = [dict(zip(columns, row, strict=False)) for row in rows]

        return ToolOutput(
            agent_result=agent_result_value,
            raw_result=result.result,
            additional_agent_context=result.additional_context or "",
        )
