from typing import TYPE_CHECKING
from typing_extensions import Self
from dataclasses import field, dataclass

from operagents.flow import Flow
from operagents import flow, director
from operagents.director import Director
from operagents.config import SceneConfig
from operagents.character import Character

from . import prepare
from .prepare import ScenePrepare

if TYPE_CHECKING:
    from operagents.timeline import Timeline


@dataclass(eq=False)
class Scene:
    name: str
    """The name of the scene."""
    description: str | None
    """The description of the scene."""
    characters: dict[str, Character]
    """The characters in the scene."""

    flow: Flow
    """The flow of the scene."""
    director: Director
    """The director of the scene."""

    prepare_actions: list[ScenePrepare] = field(default_factory=list)
    """The actions to prepare the scene."""

    @classmethod
    def from_config(cls, name: str, config: SceneConfig) -> Self:
        return cls(
            name=name,
            description=config.description,
            characters={
                name: Character.from_config(name, config)
                for name, config in config.characters.items()
            },
            flow=flow.from_config(config.flow),
            director=director.from_config(config.director),
            prepare_actions=[prepare.from_config(action) for action in config.prepare],
        )

    async def prepare(self, timeline: "Timeline") -> None:
        for action in self.prepare_actions:
            await action.prepare(timeline)

    async def next_character(self, timeline: "Timeline") -> Character:
        return await self.flow.next(timeline)
