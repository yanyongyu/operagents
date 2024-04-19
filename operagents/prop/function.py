import inspect
from collections.abc import Callable, Awaitable
from typing_extensions import Self, TypeVar, override
from typing import TYPE_CHECKING, Any, ParamSpec, cast

from pydantic import BaseModel

from operagents.exception import PropError, OperagentsException
from operagents.config import TemplateConfig, FunctionPropConfig
from operagents.utils import resolve_dot_notation, get_template_renderer

from ._base import Prop

if TYPE_CHECKING:
    from operagents.timeline import Timeline

P = ParamSpec("P")
M = TypeVar("M", bound=BaseModel, default=BaseModel)
R = TypeVar("R", default=Any)
FunctionNoParams = Callable[[], Awaitable[R]]
FunctionWithParams = Callable[[M], Awaitable[R]]


class FunctionProp(Prop[M]):
    """Call custom functions with pydantic model."""

    type_ = "function"

    def __init__(
        self,
        function: FunctionNoParams[R] | FunctionWithParams[M, R],
        *,
        exception_template: TemplateConfig,
    ) -> None:
        super().__init__()

        self.function = function

        func_params = inspect.signature(function).parameters
        if func_params:
            self.params = cast(type[M], next(iter(func_params.values())).annotation)
        else:
            self.params = None

        self.exception_renderer = get_template_renderer(exception_template)

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
        return cls(
            function=resolve_dot_notation(config.function),
            exception_template=config.exception_template,
        )

    @override
    async def call(self, timeline: "Timeline", params: M | None) -> R | str:
        if self.params is None:
            return await self._call_with_catch(cast(FunctionNoParams[R], self.function))
        if params is None:
            raise PropError(
                f"Function prop {self.name} requires parameter but none provided."
            )
        return await self._call_with_catch(
            cast(FunctionWithParams[M, R], self.function), params
        )

    async def _call_with_catch(
        self, function: Callable[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs
    ) -> R | str:
        try:
            return await function(*args, **kwargs)
        except OperagentsException:
            # bypass operagents exceptions
            raise
        except Exception as e:
            return await self.exception_renderer.render_async(prop=self, exc=e)
