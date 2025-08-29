import asyncio
from collections.abc import Callable, Coroutine
from functools import partial, wraps
from typing import Any, ParamSpec, TypeVar

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


async def run_sync_in_executor(
    func: Callable[TParams, TReturn], *args: TParams.args, **kwargs: TParams.kwargs
) -> TReturn:
    return await async_wrap(func)(*args, **kwargs)
