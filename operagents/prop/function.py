import inspect
from typing import Any, cast
from collections.abc import Callable, Awaitable
from typing_extensions import Self, TypeVar, override

from pydantic import BaseModel

from operagents.exception import PropError
from operagents.config import FunctionPropConfig
from operagents.utils import resolve_dot_notation

from ._base import Prop

P = TypeVar("P", bound=BaseModel, default=BaseModel)
R = TypeVar("R", default=Any)
FunctionNoParams = Callable[[], Awaitable[R]]
FunctionWithParams = Callable[[P], Awaitable[R]]


class FunctionProp(Prop[P, R]):
    """Call custom functions."""

    type_ = "function"

    def __init__(
        self, function: FunctionNoParams[R] | FunctionWithParams[P, R]
    ) -> None:
        super().__init__()

        self.function = function

        func_params = inspect.signature(function).parameters
        if func_params:
            self.params = cast(type[P], next(iter(func_params.values())).annotation)
        else:
            self.params = None

    @property
    @override
    def name(self) -> str:
        return self.function.__name__

    @property
    @override
    def description(self) -> str:
        return self.function.__doc__ or ""

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: FunctionPropConfig
    ) -> Self:
        return cls(function=resolve_dot_notation(config.function))

    @override
    async def call(self, params: P | None) -> R:
        if self.params is None:
            return await cast(FunctionNoParams[R], self.function)()
        if params is None:
            raise PropError(
                f"Function prop {self.name} requires parameter but none provided."
            )
        return await cast(FunctionWithParams[P, R], self.function)(params)
