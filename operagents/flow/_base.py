import abc
from typing import TYPE_CHECKING, ClassVar
from typing_extensions import Self

from operagents.config import FlowConfig

if TYPE_CHECKING:
    from operagents.character import Character
    from operagents.timeline import Timeline


class Flow(abc.ABC):
    """A flow for controlling the characters in a scene."""

    type_: ClassVar[str]
    """The type of flow."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: FlowConfig) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    async def begin(self, timeline: "Timeline") -> "Character":
        """Get the first character to act in the scene."""
        raise NotImplementedError

    @abc.abstractmethod
    async def next(self, timeline: "Timeline") -> "Character":
        """Get the next character to act in the scene."""
        raise NotImplementedError
