from typing import TYPE_CHECKING
from typing_extensions import Self, override

from operagents.config import PrefaceScenePrepareConfig

from ._base import ScenePrepare

if TYPE_CHECKING:
    from operagents.timeline import Timeline


class PrefaceScenePrepare(ScenePrepare):
    type_ = "preface"

    def __init__(self, character_name: str, content: str):
        self.character_name = character_name
        """The name of the character."""
        self.content = content
        """The content of the preface."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"character_name={self.character_name!r}, content={self.content!r}"
            ")"
        )

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: PrefaceScenePrepareConfig
    ) -> Self:
        return cls(character_name=config.character_name, content=config.content)

    @override
    async def prepare(self, timeline: "Timeline"):
        character = timeline.current_scene.characters[self.character_name]
        await timeline._switch_character(character)
        # do not observe if the character is the first to act
        event = await character.fake_act(
            timeline, self.content, do_observe=timeline.current_act_num != 0
        )
        timeline.events.append(event)
