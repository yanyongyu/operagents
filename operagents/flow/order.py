from typing import TYPE_CHECKING
from typing_extensions import override

from ._base import Flow

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character


class OrderFlow(Flow):
    type_ = "order"

    @override
    async def begin(self, timeline: "Timeline") -> "Character":
        return next(iter(timeline.current_scene.characters.values()))

    @override
    async def next(self, timeline: "Timeline") -> "Character":
        character_names = list(timeline.current_scene.characters.keys())
        next_character_name = character_names[
            (character_names.index(timeline.current_character.name) + 1)
            % len(character_names)
        ]
        return timeline.current_scene.characters[next_character_name]
