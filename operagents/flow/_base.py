import abc
from typing_extensions import Self
from typing import TYPE_CHECKING, ClassVar

from operagents.config import FlowConfig

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character


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
