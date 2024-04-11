from uuid import UUID
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Annotated, TypeAlias

from pydantic import Field

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class TimelineEventStart:
    """Event indicating the start of a timeline."""

    type_: Literal["start"] = "start"


@dataclass(eq=False, kw_only=True)
class TimelineEventEnd:
    """Event indicating the end of a timeline."""

    type_: Literal["end"] = "end"


@dataclass(init=False, eq=False, kw_only=True)
class TimelineSessionEvent:
    """Abstract class for timeline events that are associated with a session."""

    session_id: UUID
    scene: "Scene"


@dataclass(eq=False, kw_only=True)
class TimelineEventSessionAct(TimelineSessionEvent):
    """Event indicating an character act in a session."""

    type_: Literal["session_act"] = "session_act"
    character: "Character"
    content: str


@dataclass(eq=False, kw_only=True)
class TimelineEventSessionStart(TimelineSessionEvent):
    """Event indicating the start of a session."""

    type_: Literal["session_start"] = "session_start"
    session_id: UUID
    scene: "Scene"


@dataclass(eq=False, kw_only=True)
class TimelineEventSessionEnd(TimelineSessionEvent):
    """Event indicating the end of a session."""

    type_: Literal["session_end"] = "session_end"
    session_id: UUID
    scene: "Scene"


TimelineEvent: TypeAlias = Annotated[
    TimelineEventStart
    | TimelineEventEnd
    | TimelineEventSessionAct
    | TimelineEventSessionStart
    | TimelineEventSessionEnd,
    Field(discriminator="type_"),
]
