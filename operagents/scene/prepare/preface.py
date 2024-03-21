from typing import TYPE_CHECKING
from dataclasses import dataclass
from typing_extensions import Self, override

from operagents.config import PrefaceScenePrepareConfig

from ._base import ScenePrepare

if TYPE_CHECKING:
    from operagents.timeline import Timeline


@dataclass
class PrefaceScenePrepare(ScenePrepare):
    type_ = "preface"

    character_name: str
    """The name of the character."""
    content: str
    """The content of the preface."""

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: PrefaceScenePrepareConfig
    ) -> Self:
        return cls(character_name=config.character_name, content=config.content)

    @override
    async def prepare(self, timeline: "Timeline"):
        character = timeline.current_scene.characters[self.character_name]
        timeline._current_character = character
        # do not observe if the character is the first to act
        event = await character.fake_act(
            timeline, self.content, do_observe=timeline.current_act_num != 0
        )
        timeline.events.append(event)
