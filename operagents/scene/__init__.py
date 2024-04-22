from typing import TYPE_CHECKING
from typing_extensions import Self

from operagents.flow import Flow
from operagents import flow, director
from operagents.director import Director
from operagents.config import SceneConfig
from operagents.character import Character

from . import prepare
from .prepare import ScenePrepare

if TYPE_CHECKING:
    from operagents.timeline import Timeline


class Scene:
    def __init__(
        self,
        name: str,
        description: str | None,
        characters: dict[str, Character],
        flow: Flow,
        director: Director,
        prepare_actions: list[ScenePrepare] | None = None,
    ):
        self.name: str = name
        """The name of the scene."""
        self.description: str | None = description
        """The description of the scene."""
        self.characters: dict[str, Character] = characters
        """The characters in the scene."""

        self.flow: Flow = flow
        """The flow of the scene."""
        self.director: Director = director
        """The director of the scene."""

        self.prepare_actions: list[ScenePrepare] = prepare_actions or []
        """The actions to prepare the scene."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, characters={self.characters}, "
            f"flow={self.flow}, director={self.director}, "
            f"prepare_actions={self.prepare_actions}"
            ")"
        )

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
