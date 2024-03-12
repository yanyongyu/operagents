from typing import TYPE_CHECKING
from typing_extensions import Self
from dataclasses import field, dataclass

import structlog

from operagents import backend
from operagents.log import logger
from operagents.utils import get_template_renderer
from operagents.timeline.event import TimelineEventAct
from operagents.config import AgentConfig, TemplateConfig

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.backend import Backend, Message
    from operagents.timeline.event import TimelineEvent


@dataclass(eq=False)
class Agent:
    name: str
    """The name of the agent."""
    # style: str
    backend: "Backend"
    """The backend to use for generating text."""

    system_template: TemplateConfig = field(kw_only=True)
    """The system template to use for generating text."""
    user_template: TemplateConfig = field(kw_only=True)
    """The user template to use for generating text."""

    chat_history: list["Message"] = field(default_factory=list, kw_only=True)
    """The history of the agent self's chat messages."""

    def __post_init__(self):
        self.logger: structlog.stdlib.BoundLogger = logger.bind(agent=self)
        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)

    @classmethod
    def from_config(cls, name: str, config: AgentConfig) -> Self:
        """Create an agent from a configuration."""
        return cls(
            name=name,
            backend=backend.from_config(config.backend),
            system_template=config.system_template,
            user_template=config.user_template,
        )

    async def act(self, timeline: "Timeline") -> "TimelineEvent":
        """Make the agent act."""
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
            *self.chat_history,
            {
                "role": "user",
                "content": new_message,
            },
        ]
        await self.logger.adebug(
            "Acting", character=timeline.current_character, messages=messages
        )
        response = await self.backend.generate(messages)
        await self.logger.ainfo(response, character=timeline.current_character)

        self.chat_history.append(
            {
                "role": "user",
                "content": new_message,
            }
        )
        self.chat_history.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        return TimelineEventAct(
            character=timeline.current_character,
            scene=timeline.current_scene,
            content=response,
        )

    # TODO: Implement this
    async def observe(self, timeline: "Timeline"): ...
