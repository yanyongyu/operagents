from typing import TYPE_CHECKING
from dataclasses import field, dataclass
from typing_extensions import Self, override

from operagents import backend
from operagents.log import logger
from operagents.exception import OperaFinished
from operagents.utils import get_template_renderer
from operagents.config import TemplateConfig, ModelDirectorConfig

from ._base import Director

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline
    from operagents.backend import Backend, Message


@dataclass
class ModelDirector(Director):
    type_ = "model"

    backend: "Backend" = field()

    system_template: TemplateConfig = field(kw_only=True)
    user_template: TemplateConfig = field(kw_only=True)
    allowed_scenes: list[str] | None = field(default=None, kw_only=True)
    finish_flag: str | None = field(default=None, kw_only=True)

    def __post_init__(self):
        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: ModelDirectorConfig
    ) -> Self:
        return cls(
            backend=backend.from_config(config.backend),
            system_template=config.system_template,
            user_template=config.user_template,
            allowed_scenes=config.allowed_scenes,
            finish_flag=config.finish_flag,
        )

    @override
    async def next_scene(self, timeline: "Timeline") -> "Scene | None":
        """Return the next scene to be executed."""
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
        logger.debug("Choosing next scene with messages: {messages}", messages=messages)
        response = await self.backend.generate(messages)
        logger.debug("Director response: {response}", response=response)

        if self.finish_flag is not None and self.finish_flag in response:
            raise OperaFinished()

        allowed_scenes = (
            timeline.opera.scenes
            if self.allowed_scenes is None
            else self.allowed_scenes
        )
        for scene in allowed_scenes:
            if scene in response:
                return timeline.opera.scenes[scene]
        return None
