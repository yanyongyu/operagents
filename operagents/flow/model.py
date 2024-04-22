from typing import TYPE_CHECKING
from typing_extensions import Self, override

from operagents import backend
from operagents.log import logger
from operagents.exception import FlowError
from operagents.utils import get_template_renderer
from operagents.config import TemplateConfig, ModelFlowConfig

from ._base import Flow

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character
    from operagents.backend import Backend, Message


class ModelFlow(Flow):
    type_ = "model"

    def __init__(
        self,
        backend: "Backend",
        *,
        system_template: TemplateConfig,
        user_template: TemplateConfig,
        allowed_characters: list[str] | None = None,
        begin_character: str | None = None,
        fallback_character: str | None = None,
    ):
        self.backend: "Backend" = backend

        self.system_template = system_template
        self.user_template = user_template

        self.allowed_characters: list[str] | None = allowed_characters
        self.begin_character: str | None = begin_character
        self.fallback_character: str | None = fallback_character

        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"backend={self.backend}, allowed_characters={self.allowed_characters}, "
            f"begin_character={self.begin_character!r}, "
            f"fallback_character={self.fallback_character!r}"
            ")"
        )

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: ModelFlowConfig
    ) -> Self:
        return cls(
            backend=backend.from_config(config.backend),
            system_template=config.system_template,
            user_template=config.user_template,
            allowed_characters=config.allowed_characters,
            begin_character=config.begin_character,
        )

    async def _choose_character(self, timeline: "Timeline") -> "Character":
        system_message = (
            await self.system_renderer.render_async(agent=self, timeline=timeline)
        ).strip()
        new_message = (
            await self.user_renderer.render_async(agent=self, timeline=timeline)
        ).strip()
        messages: list["Message"] = [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": new_message,
            },
        ]
        logger.debug(
            "Choosing next character with messages: {messages}", messages=messages
        )
        response = await self.backend.generate(timeline, messages)
        logger.debug("Flow response: {response}", response=response)

        allowed_characters = (
            list(timeline.current_scene.characters)
            if self.allowed_characters is None
            else self.allowed_characters
        )
        for character in allowed_characters:
            if character in response:
                return timeline.current_scene.characters[character]
        if self.fallback_character is not None:
            return timeline.current_scene.characters[self.fallback_character]
        raise FlowError(
            "The model flow failed to choose the next character. "
            "No fallback character was provided."
        )

    @override
    async def begin(self, timeline: "Timeline") -> "Character":
        if self.begin_character is not None:
            return timeline.current_scene.characters[self.begin_character]

        return await self._choose_character(timeline)

    @override
    async def next(self, timeline: "Timeline") -> "Character":
        return await self._choose_character(timeline)
