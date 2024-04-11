from uuid import UUID
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Annotated, TypeAlias

from pydantic import Field

from operagents.exception import SceneFinished

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.timeline import Timeline
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class AgentEventObserve:
    """Other agent acts observed by an agent.

    a.k.a. Agent short term memory.
    """

    type_: Literal["observe"] = "observe"
    session_id: UUID
    scene: "Scene"
    content: str


@dataclass(eq=False, kw_only=True)
class AgentEventSessionSummary:
    """Summary of observed events for one whole scene session.

    a.k.a. Agent long term memory.

    Note:
        The summary must come after the session is finished.
        No more `observe` or `act` events will be added after the summary.
    """

    type_: Literal["session_summary"] = "session_summary"
    session_id: UUID
    scene: "Scene"
    content: str


@dataclass(eq=False, kw_only=True)
class AgentEventAct:
    """Agent self acts."""

    type_: Literal["act"] = "act"
    session_id: UUID
    scene: "Scene"
    character: "Character"
    content: str


AgentEvent: TypeAlias = Annotated[
    AgentEventObserve | AgentEventSessionSummary | AgentEventAct,
    Field(discriminator="type_"),
]


class AgentMemory:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []
        """Memorized events of the agent."""

    def summarized(self, session_id: UUID) -> bool:
        return any(
            isinstance(event, AgentEventSessionSummary)
            and event.session_id == session_id
            for event in self.events
        )

    def remember(self, event: AgentEvent) -> None:
        """Remember an agent event."""
        if isinstance(event, AgentEventObserve | AgentEventAct) and self.summarized(
            event.session_id
        ):
            raise SceneFinished()
        self.events.append(event)

    def get_memory(self, timeline: "Timeline") -> list[AgentEvent]:
        """Get the agent memory for acting in the current scene."""

        result: list[AgentEvent] = []
        for event in self.events:
            if isinstance(event, AgentEventObserve | AgentEventAct):
                if event.session_id != timeline.current_session_id:
                    # if the event is from past session,
                    # ignore it and use the summary instead
                    continue
                result.append(event)
            elif isinstance(event, AgentEventSessionSummary):
                result.append(event)
        return result

    def get_memory_for_session(self, session_id: UUID) -> list[AgentEvent]:
        """Get the agent memory for acting in the given scene session."""
        return [event for event in self.events if event.session_id == session_id]
