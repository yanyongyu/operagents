from types import TracebackType
from typing import TYPE_CHECKING
from typing_extensions import Self

from operagents import backend
from operagents.log import logger
from operagents.utils import get_template_renderer
from operagents.exception import TimelineNotStarted
from operagents.config import AgentConfig, TemplateConfig
from operagents.timeline.event import TimelineEventSessionAct, TimelineEventSessionEnd

from .memory import AgentEvent as AgentEvent
from .memory import (
    AgentMemory,
    AgentEventAct,
    AgentEventObserve,
    AgentEventUseProp,
    AgentEventSessionSummary,
)

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.backend import Backend, Message, PropMessage


class Agent:
    def __init__(
        self,
        name: str,
        backend: "Backend",
        *,
        system_template: TemplateConfig,
        user_template: TemplateConfig,
        session_summary_system_template: TemplateConfig,
        session_summary_user_template: TemplateConfig,
    ):
        self.name: str = name
        """The name of the agent."""
        self.backend: "Backend" = backend
        """The backend to use for generating text."""

        self.system_template = system_template
        """The system template to use for generating text."""
        self.user_template = user_template
        """The user template to use for generating text."""

        self.session_summary_system_template = session_summary_system_template
        """The scene summary system template to use for generating summary."""
        self.session_summary_user_template = session_summary_user_template
        """The scene summary user template to use for generating summary."""

        self._memory: AgentMemory | None = None

        self.logger = logger.bind(agent=self)
        self.system_renderer = get_template_renderer(self.system_template)
        self.user_renderer = get_template_renderer(self.user_template)
        self.session_summary_system_renderer = get_template_renderer(
            self.session_summary_system_template
        )
        self.session_summary_user_renderer = get_template_renderer(
            self.session_summary_user_template
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name!r}, backend={self.backend!r})"
        )

    @classmethod
    def from_config(cls, name: str, config: AgentConfig) -> Self:
        """Create an agent from a configuration."""
        return cls(
            name=name,
            backend=backend.from_config(config.backend),
            system_template=config.system_template,
            user_template=config.user_template,
            session_summary_system_template=config.session_summary_system_template,
            session_summary_user_template=config.session_summary_user_template,
        )

    @property
    def memory(self) -> AgentMemory:
        """The memory of the agent."""
        if self._memory is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._memory

    def _memory_to_message(self, memory_event: AgentEvent) -> "Message":
        """Convert an agent memory event to a message."""
        if isinstance(memory_event, AgentEventObserve | AgentEventSessionSummary):
            return {
                "role": "user",
                "content": memory_event.content,
            }
        elif isinstance(memory_event, AgentEventAct):
            return {
                "role": "assistant",
                "content": memory_event.content,
            }
        elif isinstance(memory_event, AgentEventUseProp):
            return {
                "role": "prop",
                "usage_id": memory_event.usage_id,
                "prop": memory_event.prop,
                "raw_params": memory_event.prop_raw_params,
                "params": memory_event.prop_params,
                "result": memory_event.prop_result,
            }

        # This should never happen
        raise ValueError(f"Unknown memory event type: {memory_event.type_}")

    def _do_observe(self, timeline: "Timeline", message: str) -> None:
        """Make the agent observe a message."""
        self.memory.remember(
            AgentEventObserve(
                session_id=timeline.current_session_id,
                scene=timeline.current_scene,
                content=message,
            )
        )

    def _do_response(
        self, timeline: "Timeline", response: str, prop_usages: list["PropMessage"]
    ) -> None:
        """Make the agent respond to a message."""
        self.logger.info(
            "{response}",
            response=response,
            scene=timeline.current_scene,
            character=timeline.current_character,
        )

        for prop_message in prop_usages:
            self.memory.remember(
                AgentEventUseProp(
                    session_id=timeline.current_session_id,
                    scene=timeline.current_scene,
                    character=timeline.current_character,
                    usage_id=prop_message["usage_id"],
                    prop=prop_message["prop"],
                    prop_raw_params=prop_message["raw_params"],
                    prop_params=prop_message["params"],
                    prop_result=prop_message["result"],
                )
            )

        self.memory.remember(
            AgentEventAct(
                session_id=timeline.current_session_id,
                scene=timeline.current_scene,
                character=timeline.current_character,
                content=response,
            )
        )

    async def fake_act(
        self, timeline: "Timeline", response: str, do_observe: bool = True
    ) -> TimelineEventSessionAct:
        """Make the agent act with a given response."""

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
        self._do_response(timeline, response, [])

        return TimelineEventSessionAct(
            session_id=timeline.current_session_id,
            scene=timeline.current_scene,
            character=timeline.current_character,
            content=response,
        )

    async def act(self, timeline: "Timeline") -> TimelineEventSessionAct:
        """Make the agent act."""

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
            "Acting with {prop_count} props and messages: {messages}",
            scene=timeline.current_scene,
            character=timeline.current_character,
            props=props,
            prop_count=len(props),
            messages=messages,
        )
        response = await self.backend.generate(timeline, messages, props)

        self._do_observe(timeline, new_message)
        self._do_response(timeline, response.content, response.prop_usage)

        return TimelineEventSessionAct(
            session_id=timeline.current_session_id,
            scene=timeline.current_scene,
            character=timeline.current_character,
            content=response.content,
        )

    async def summary(
        self, timeline: "Timeline", event: TimelineEventSessionEnd
    ) -> None:
        """Make the agent summarize the scene session when it ends"""

        session_id = event.session_id
        scene = event.scene

        if self.memory.summarized(session_id):
            return

        system_message = (
            await self.session_summary_system_renderer.render_async(
                agent=self, timeline=timeline, session_id=session_id, scene=scene
            )
        ).strip()
        summary_message = (
            await self.session_summary_user_renderer.render_async(
                agent=self, timeline=timeline, session_id=session_id, scene=scene
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
            session_id=session_id,
            scene=scene,
            messages=messages,
        )
        response = await self.backend.generate(timeline, messages)
        self.logger.debug(
            "Summary: {response}",
            session_id=session_id,
            scene=scene,
            response=response.content,
        )

        self.memory.remember(
            AgentEventSessionSummary(
                session_id=session_id, scene=scene, content=response.content
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
