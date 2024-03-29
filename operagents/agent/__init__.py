from types import TracebackType
from typing import TYPE_CHECKING
from typing_extensions import Self
from dataclasses import field, dataclass

from operagents import backend
from operagents.log import logger
from operagents.utils import get_template_renderer
from operagents.exception import TimelineNotStarted
from operagents.config import AgentConfig, TemplateConfig
from operagents.timeline.event import TimelineEventAct, TimelineEventSceneEnd

from .memory import AgentEvent as AgentEvent
from .memory import AgentMemory, AgentEventAct, AgentEventObserve, AgentEventSummary

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.backend import Backend, Message


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

    scene_summary_system_template: TemplateConfig = field(kw_only=True)
    """The scene summary system template to use for generating summary."""
    scene_summary_user_template: TemplateConfig = field(kw_only=True)
    """The scene summary user template to use for generating summary."""

    _memory: AgentMemory | None = field(default=None, init=False)

    def __post_init__(self):
        self.logger = logger.bind(agent=self)
        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)
        self.scene_summary_system_renderer = get_template_renderer(
            self.scene_summary_system_template
        )
        self.scene_summary_user_renderer = get_template_renderer(
            self.scene_summary_user_template
        )

    @classmethod
    def from_config(cls, name: str, config: AgentConfig) -> Self:
        """Create an agent from a configuration."""
        return cls(
            name=name,
            backend=backend.from_config(config.backend),
            system_template=config.system_template,
            user_template=config.user_template,
            scene_summary_system_template=config.scene_summary_system_template,
            scene_summary_user_template=config.scene_summary_user_template,
        )

    @property
    def memory(self) -> AgentMemory:
        """The memory of the agent."""
        if self._memory is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._memory

    async def _act_precheck(self, timeline: "Timeline") -> None:
        """Check if the agent needs to summarize the scene before acting."""
        await self.summary(timeline)

    def _memory_to_message(self, memory_event: AgentEvent) -> "Message":
        """Convert an agent memory event to a message."""
        if memory_event.type_ == "observe" or memory_event.type_ == "scene_summary":
            return {
                "role": "user",
                "content": memory_event.content,
            }
        elif memory_event.type_ == "act":
            return {
                "role": "assistant",
                "content": memory_event.content,
            }

        # This should never happen
        raise ValueError(f"Unknown memory event type: {memory_event.type_}")

    def _do_observe(self, timeline: "Timeline", message: str) -> None:
        """Make the agent observe a message."""
        self.memory.remember(
            AgentEventObserve(
                context_id=timeline.current_context_id,
                scene=timeline.current_scene,
                content=message,
            )
        )

    def _do_response(self, timeline: "Timeline", response: str) -> None:
        """Make the agent respond to a message."""
        self.logger.info(
            response, scene=timeline.current_scene, character=timeline.current_character
        )

        self.memory.remember(
            AgentEventAct(
                context_id=timeline.current_context_id,
                scene=timeline.current_scene,
                character=timeline.current_character,
                content=response,
            )
        )

    async def fake_act(
        self, timeline: "Timeline", response: str, do_observe: bool = True
    ) -> TimelineEventAct:
        """Make the agent act with a given response."""

        await self._act_precheck(timeline)

        new_message = (
            (
                await self.user_renderer.render_async(agent=self, timeline=timeline)
            ).strip()
            if do_observe
            else None
        )
        self.logger.debug(
            "Fake acting",
            scene=timeline.current_scene,
            character=timeline.current_character,
            messages=new_message,
        )

        if new_message is not None:
            self._do_observe(timeline, new_message)
        self._do_response(timeline, response)

        return TimelineEventAct(
            context_id=timeline.current_context_id,
            scene=timeline.current_scene,
            character=timeline.current_character,
            content=response,
        )

    async def act(self, timeline: "Timeline") -> TimelineEventAct:
        """Make the agent act."""

        await self._act_precheck(timeline)

        system_message = (
            await self.system_renderer.render_async(agent=self, timeline=timeline)
        ).strip()
        new_message = (
            await self.user_renderer.render_async(agent=self, timeline=timeline)
        ).strip()
        memory_events = self.memory.get_memory(timeline)
        messages: list["Message"] = [
            {
                "role": "system",
                "content": system_message,
            },
            *(self._memory_to_message(memory_event) for memory_event in memory_events),
            {
                "role": "user",
                "content": new_message,
            },
        ]

        props = timeline.current_character.props

        self.logger.debug(
            "Acting with messages: {messages}",
            scene=timeline.current_scene,
            character=timeline.current_character,
            messages=messages,
        )
        response = await self.backend.generate(messages, props)

        self._do_observe(timeline, new_message)
        self._do_response(timeline, response)

        return TimelineEventAct(
            context_id=timeline.current_context_id,
            scene=timeline.current_scene,
            character=timeline.current_character,
            content=response,
        )

    async def summary(self, timeline: "Timeline") -> None:
        """Make the agent summarize the scene contexts."""
        need_summary_contexts = self.memory.need_summary_contexts()
        ended_contexts = {
            event.context_id: event.scene
            for event in timeline.events
            if isinstance(event, TimelineEventSceneEnd)
        }
        for context_id in need_summary_contexts:
            if context_id not in ended_contexts:
                continue

            scene = ended_contexts[context_id]
            system_message = (
                await self.scene_summary_system_renderer.render_async(
                    agent=self, timeline=timeline, context_id=context_id, scene=scene
                )
            ).strip()
            summary_message = (
                await self.scene_summary_user_renderer.render_async(
                    agent=self, timeline=timeline, context_id=context_id, scene=scene
                )
            ).strip()
            messages: list["Message"] = [
                {
                    "role": "system",
                    "content": system_message,
                },
                {
                    "role": "user",
                    "content": summary_message,
                },
            ]
            self.logger.debug(
                "Summarizing with messages: {messages}",
                context_id=context_id,
                scene=scene,
                messages=messages,
            )
            response = await self.backend.generate(messages)
            self.logger.debug(
                "Summary: {response}",
                context_id=context_id,
                scene=scene,
                response=response,
            )

            self.memory.remember(
                AgentEventSummary(
                    context_id=context_id, scene=scene, content=summary_message
                )
            )

    async def __aenter__(self) -> Self:
        self._memory = AgentMemory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._memory = None
