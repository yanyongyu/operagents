from uuid import UUID
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Annotated, TypeAlias

from pydantic import Field

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class TimelineEventAct:
    type_: Literal["act"] = "act"
    session_id: UUID
    scene: "Scene"
    character: "Character"
    content: str


@dataclass(eq=False, kw_only=True)
class TimelineEventSessionStart:
    type_: Literal["session_start"] = "session_start"
    session_id: UUID
    scene: "Scene"


@dataclass(eq=False, kw_only=True)
class TimelineEventSessionEnd:
    type_: Literal["session_end"] = "session_end"
    session_id: UUID
    scene: "Scene"


TimelineEvent: TypeAlias = Annotated[
    TimelineEventAct | TimelineEventSessionStart | TimelineEventSessionEnd,
    Field(discriminator="type_"),
]
