from typing import TYPE_CHECKING
from dataclasses import field, dataclass
from typing_extensions import Self, override

from operagents import backend
from operagents.log import logger
from operagents.timeline import Timeline
from operagents.character import Character
from operagents.exception import FlowError
from operagents.utils import get_template_renderer
from operagents.config import TemplateConfig, ModelFlowConfig

from ._base import Flow

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.character import Character
    from operagents.backend import Backend, Message


@dataclass
class ModelFlow(Flow):
    type_ = "model"

    backend: "Backend" = field()

    system_template: TemplateConfig = field(kw_only=True)
    user_template: TemplateConfig = field(kw_only=True)
    allowed_characters: list[str] | None = field(default=None, kw_only=True)
    begin_character: str | None = field(default=None, kw_only=True)
    fallback_character: str | None = field(default=None, kw_only=True)

    def __post_init__(self):
        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)

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
        response = await self.backend.generate(messages)
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
