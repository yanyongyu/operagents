from typing import TYPE_CHECKING
from typing_extensions import Self, override

from operagents.exception import OperaFinished
from operagents.config import NeverDirectorConfig

from ._base import Director

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline


class NeverDirector(Director):
    """A director that never finish current scene."""

    type_ = "never"

    def __init__(self, max_act_num: int | None = None) -> None:
        self.max_act_num = max_act_num

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: NeverDirectorConfig
    ) -> Self:
        return cls(max_act_num=config.max_act_num)

    @override
    async def next_scene(self, timeline: "Timeline") -> "Scene | None":
        if (
            self.max_act_num is not None
            and timeline.current_act_num >= self.max_act_num
        ):
            raise OperaFinished()
        return None
