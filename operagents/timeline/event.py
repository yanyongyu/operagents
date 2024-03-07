from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Annotated, TypeAlias

from pydantic import Field

if TYPE_CHECKING:
    from operagents.scene import Scene
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class TimelineEventAct:
    type_: Literal["act"] = "act"
    character: "Character"
    scene: "Scene"
    content: str


TimelineEvent: TypeAlias = Annotated[TimelineEventAct, Field(discriminator="type_")]
