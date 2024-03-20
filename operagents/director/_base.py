import abc
from typing_extensions import Self
from typing import TYPE_CHECKING, ClassVar

from operagents.config import DirectorConfig

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline


class Director(abc.ABC):
    """A director for controlling the scene."""

    type_: ClassVar[str]
    """The type of director."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: DirectorConfig) -> Self:
        """Create a director from a config."""
        raise NotImplementedError

    @abc.abstractmethod
    async def next_scene(self, timeline: "Timeline") -> "Scene | None":
        """Get the next scene."""
        raise NotImplementedError
