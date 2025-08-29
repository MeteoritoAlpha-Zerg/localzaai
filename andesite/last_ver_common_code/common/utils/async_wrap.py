import asyncio
from functools import partial, wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")


def async_wrap(
    func: Callable[TParams, TReturn],
) -> Callable[TParams, Coroutine[None, Any, TReturn]]:
    @wraps(func)
    async def run(*args: TParams.args, **kwargs: TParams.kwargs) -> TReturn:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, pfunc)

    return run
