from typing_extensions import Self, override
from typing import TYPE_CHECKING, Literal, ClassVar

from noneprompt import Choice, ListPrompt

from operagents.timeline import Timeline
from operagents.character import Character
from operagents.config import UserFlowConfig

from ._base import Flow

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character


class UserFlow(Flow):
    type_: ClassVar[Literal["user"]] = "user"

    @classmethod
    @override
    def from_config(cls, config: UserFlowConfig) -> Self:
        return cls()

    @override
    async def begin(self, timeline: "Timeline") -> "Character":
        characters: list[Choice["Character"]] = [
            Choice(character_name, character)
            for character_name, character in timeline.current_scene.characters.items()
        ]
        choice = await ListPrompt(
            "Please select the begin character to act", characters
        ).prompt_async()
        return choice.data

    @override
    async def next(self, timeline: "Timeline") -> "Character":
        characters: list[Choice["Character"]] = [
            Choice(character_name, character)
            for character_name, character in timeline.current_scene.characters.items()
        ]
        choice = await ListPrompt(
            "Please select the next character to act", characters
        ).prompt_async()
        return choice.data
