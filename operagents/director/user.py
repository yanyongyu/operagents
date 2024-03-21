from typing import TYPE_CHECKING
from typing_extensions import Self, override

from noneprompt import Choice, ListPrompt

from operagents.exception import OperaFinished
from operagents.config import UserDirectorConfig

from ._base import Director

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline


class UserDirector(Director):
    type_ = "user"

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: UserDirectorConfig
    ) -> Self:
        return cls()

    @override
    async def next_scene(self, timeline: "Timeline") -> "Scene | None":
        scenes: list[Choice["Scene | OperaFinished | None"]] = [
            Choice("Continue current scene", None),
            *(
                Choice(scene_name, scene)
                for scene_name, scene in timeline.opera.scenes.items()
            ),
            Choice("Finish opera", OperaFinished()),
        ]
        choice = await ListPrompt("Please select next scene", scenes).prompt_async()
        if isinstance(choice.data, OperaFinished):
            raise choice.data
        return choice.data
