from typing import TYPE_CHECKING
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


class ModelDirector(Director):
    type_ = "model"

    def __init__(
        self,
        backend: "Backend",
        *,
        system_template: TemplateConfig,
        user_template: TemplateConfig,
        allowed_scenes: list[str] | None = None,
        finish_flag: str | None = None,
    ):
        self.backend: "Backend" = backend

        self.system_template = system_template
        self.user_template = user_template

        self.allowed_scenes: list[str] | None = allowed_scenes
        self.finish_flag: str | None = finish_flag

        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"backend={self.backend}, allowed_scenes={self.allowed_scenes!r}, "
            f"finish_flag={self.finish_flag!r}"
            ")"
        )

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
        response = await self.backend.generate(timeline, messages)
        logger.debug("Director response: {response}", response=response.content)

        if self.finish_flag is not None and self.finish_flag in response.content:
            raise OperaFinished()

        allowed_scenes = (
            timeline.opera.scenes
            if self.allowed_scenes is None
            else self.allowed_scenes
        )
        for scene in allowed_scenes:
            if scene in response.content:
                return timeline.opera.scenes[scene]
        return None
