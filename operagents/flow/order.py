from typing import TYPE_CHECKING
from typing_extensions import Self, override

from operagents.config import OrderFlowConfig

from ._base import Flow

if TYPE_CHECKING:
    from operagents.character import Character
    from operagents.timeline import Timeline


class OrderFlow(Flow):
    type_ = "order"

    def __init__(self, order: list[str] | None = None):
        self.order: list[str] | None = order

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(order={self.order})"

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: OrderFlowConfig
    ) -> Self:
        return cls(order=config.order)

    @override
    async def begin(self, timeline: "Timeline") -> "Character":
        characters = timeline.current_scene.characters
        if self.order is not None:
            return characters[self.order[0]]
        return next(iter(characters.values()))

    @override
    async def next(self, timeline: "Timeline") -> "Character":
        if self.order is None:
            character_names = list(timeline.current_scene.characters.keys())
        else:
            character_names = self.order

        # FIXME: character names may not be unique, check sequence instead
        next_character_name = character_names[
            (character_names.index(timeline.current_character.name) + 1)
            % len(character_names)
        ]
        return timeline.current_scene.characters[next_character_name]
