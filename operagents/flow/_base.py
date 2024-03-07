import abc
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character


class Flow(abc.ABC):
    type_: ClassVar[str]
    """The type of flow."""

    @abc.abstractmethod
    async def begin(self, timeline: "Timeline") -> "Character":
        """Get the first character to act in the scene."""
        raise NotImplementedError

    @abc.abstractmethod
    async def next(self, timeline: "Timeline") -> "Character":
        """Get the next character to act in the scene."""
        raise NotImplementedError
