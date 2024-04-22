from uuid import UUID
from typing_extensions import TypeVar
from typing import TYPE_CHECKING, Any, Generic, Literal, Annotated, TypeAlias

from pydantic import Field, BaseModel, ConfigDict, field_serializer

from operagents.prop import Prop
from operagents.scene import Scene
from operagents.character import Character
from operagents.exception import SceneFinished
from operagents.utils import (
    any_serializer,
    prop_serializer,
    scene_serializer,
    character_serializer,
)

if TYPE_CHECKING:
    from operagents.timeline import Timeline


P = TypeVar("P", bound=BaseModel, default=BaseModel)


class AgentEventObserve(BaseModel):
    """Other agent acts observed by an agent.

    a.k.a. Agent short term memory.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["observe"] = "observe"
    session_id: UUID
    scene: Scene
    content: str

    _serialize_scene = field_serializer("scene")(scene_serializer)


class AgentEventSessionSummary(BaseModel):
    """Summary of observed events for one whole scene session.

    a.k.a. Agent long term memory.

    Note:
        The summary must come after the session is finished.
        No more `observe` or `act` events will be added after the summary.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["session_summary"] = "session_summary"
    session_id: UUID
    scene: Scene
    content: str

    _serialize_scene = field_serializer("scene")(scene_serializer)


class AgentEventAct(BaseModel):
    """Agent self acts."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["act"] = "act"
    session_id: UUID
    scene: Scene
    character: Character
    content: str

    _serialize_scene = field_serializer("scene")(scene_serializer)
    _serialize_character = field_serializer("character")(character_serializer)


class AgentEventUseProp(BaseModel, Generic[P]):
    """Agent use prop."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["use_prop"] = "use_prop"
    session_id: UUID
    scene: Scene
    character: Character
    usage_id: str
    prop: Prop[P]
    prop_raw_params: str
    prop_params: BaseModel | None
    prop_result: Any

    _serialize_scene = field_serializer("scene")(scene_serializer)
    _serialize_character = field_serializer("character")(character_serializer)
    _serialize_prop = field_serializer("prop")(prop_serializer)
    _serialize_prop_result = field_serializer("prop_result", mode="wrap")(
        any_serializer
    )


AgentEvent: TypeAlias = Annotated[
    AgentEventObserve | AgentEventSessionSummary | AgentEventAct | AgentEventUseProp,
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
