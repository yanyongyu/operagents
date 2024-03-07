import inspect
from typing import TypeVar, cast
from typing_extensions import override
from collections.abc import Callable, Awaitable

from pydantic import BaseModel

from operagents.utils import resolve_dot_notation

from ._base import Prop

P = TypeVar("P", bound=BaseModel)
R = TypeVar("R")


class FunctionProp(Prop[P, R]):
    """Call custom functions."""

    type_ = "function"

    def __init__(self, function: Callable[[P], Awaitable[R]] | str) -> None:
        super().__init__()

        if isinstance(function, str):
            function = cast(Callable[[P], Awaitable[R]], resolve_dot_notation(function))

        self.function = function

        func_params = inspect.signature(function).parameters
        self.params = cast(type[P], next(iter(func_params.values())).annotation)

    @property
    @override
    def name(self) -> str:
        return self.function.__name__

    @property
    @override
    def description(self) -> str:
        return self.function.__doc__ or ""

    @override
    async def use(self, params: P) -> R:
        return await self.function(params)
