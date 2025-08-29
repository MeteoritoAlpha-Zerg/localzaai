import inspect
from typing import Any, Callable, Coroutine, Dict, get_type_hints

from common.jsonlogging.jsonlogger import Logging
from common.models.metadata import QueryResultMetadata
from opentelemetry import trace
from pydantic import BaseModel, PrivateAttr, ValidationError
from pydantic.fields import FieldInfo


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

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


class _FinalToolOutput(BaseModel):
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


class Tool(BaseModel):
    name: str
    connector: str
    _input_schema: type[BaseModel]
    _execute_fn: Executable = PrivateAttr()

    def _verify_input_schema(self, model: type[BaseModel]) -> None:
        if (
            "extra" in model.model_config
            and model.model_config.get("extra") != "ignore"
        ):
            raise ValueError("extra args not allowed in tool input_schema")

    def __init__(
        self,
        *,
        name: str,
        connector: str,
        # We perform our own type validation on the execute function as python isn't smart enough to handle BaseModel subclass parameters correctly
        execute_fn: Callable[[Any], ToolReturn],
    ):
        super().__init__(name=name, connector=connector)

        sig = inspect.signature(execute_fn)
        params = list(sig.parameters.values())

        # Ensure the function has exactly one argument
        if len(params) != 1:
            raise TypeError(
                f"`execute_fn` for tool {name} must have exactly one argument, but got {len(params)}."
            )

        # Ensure the 1 argument is a subclass of BaseModel
        param_type = get_type_hints(execute_fn).get(params[0].name)
        if not (inspect.isclass(param_type) and issubclass(param_type, BaseModel)):
            raise TypeError(
                f"`execute_fn` for tool {name} must take a single argument of type `BaseModel`, but got {param_type}."
            )
        else:
            self._input_schema = param_type
            self._verify_input_schema(self._input_schema)

        # We have performed all type checks to guarantee this cast is safe
        self._execute_fn = execute_fn

    def allows_extra_parameters(self) -> bool:
        extra_param_config = self._input_schema.model_config.get("extra")
        return extra_param_config != "forbid"

    def get_parameters(self) -> Dict[str, FieldInfo]:
        return self._input_schema.model_fields

    async def execute(self, **kwargs: Any) -> _FinalToolOutput:
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
            simplified_errors = [
                f"Field '{err['loc'][0]}': {err['msg']}" for err in errors
            ]
            raise ValueError("Input error: " + "\n".join(simplified_errors)) from e

        result = None
        try:
            result = self._execute_fn(input_model)
            if inspect.iscoroutine(result):
                result = await result
        except Exception as e:
            logger().exception("Error executing tool")
            raise e

        if not isinstance(result, ToolResult):
            result = ToolResult(result=result)

        agent_result_value = result.result
        if isinstance(agent_result_value, QueryResultMetadata):
            rows = (agent_result_value.results or []).copy()
            columns = (agent_result_value.column_headers or []).copy()
            agent_result_value = [dict(zip(columns, row)) for row in rows]

        return _FinalToolOutput(
            agent_result=agent_result_value,
            raw_result=result.result,
            additional_agent_context=result.additional_context or "",
        )
