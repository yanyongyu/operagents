from typing import TYPE_CHECKING
from typing_extensions import Self, override

from operagents.config import NeverDirectorConfig

from ._base import Director

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline


class NeverDirector(Director):
    """A director that never finish current scene."""

    type_ = "never"

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: NeverDirectorConfig
    ) -> Self:
        return cls()

    @override
    async def next_scene(self, timeline: "Timeline") -> "Scene | None":
        return None
