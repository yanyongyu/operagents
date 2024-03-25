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
    context_id: UUID
    scene: "Scene"
    character: "Character"
    content: str


@dataclass(eq=False, kw_only=True)
class TimelineEventSceneStart:
    type_: Literal["scene_start"] = "scene_start"
    context_id: UUID
    scene: "Scene"


@dataclass(eq=False, kw_only=True)
class TimelineEventSceneEnd:
    type_: Literal["scene_end"] = "scene_end"
    context_id: UUID
    scene: "Scene"


TimelineEvent: TypeAlias = Annotated[
    TimelineEventAct | TimelineEventSceneStart | TimelineEventSceneEnd,
    Field(discriminator="type_"),
]
