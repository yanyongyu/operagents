import abc
from typing_extensions import Self
from typing import TYPE_CHECKING, ClassVar

from operagents.config import ScenePrepareConfig

if TYPE_CHECKING:
    from operagents.timeline import Timeline


class ScenePrepare(abc.ABC):
    """Scene prepare is called before the current scene starts to act."""

    type_: ClassVar[str]
    """Type of the scene prepare."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: ScenePrepareConfig) -> Self:
        """Create a scene prepare from the config."""
        raise NotImplementedError

    @abc.abstractmethod
    async def prepare(self, timeline: "Timeline"):
        """Prepare the timeline for the current scene."""
        pass
