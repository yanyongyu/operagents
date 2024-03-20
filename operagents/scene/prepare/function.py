from dataclasses import dataclass
from collections.abc import Callable
from typing_extensions import Self, override
from typing import TYPE_CHECKING, Any, Literal, ClassVar

from operagents.utils import resolve_dot_notation
from operagents.config import FunctionScenePrepareConfig

from ._base import ScenePrepare

if TYPE_CHECKING:
    from operagents.timeline import Timeline


@dataclass
class FunctionScenePrepare(ScenePrepare):
    type_: ClassVar[Literal["function"]] = "function"

    function: Callable[["Timeline"], Any]

    @classmethod
    @override
    def from_config(cls, config: FunctionScenePrepareConfig) -> Self:
        return cls(function=resolve_dot_notation(config.function))

    @override
    async def prepare(self, timeline: "Timeline"):
        await self.function(timeline)
