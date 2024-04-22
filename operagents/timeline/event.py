from uuid import UUID
from typing import Literal, Annotated, TypeAlias

from pydantic import Field, BaseModel, ConfigDict, field_serializer

from operagents.scene import Scene
from operagents.character import Character
from operagents.utils import scene_serializer, character_serializer


class TimelineEventStart(BaseModel):
    """Event indicating the start of a timeline."""

    type_: Literal["start"] = "start"


class TimelineEventEnd(BaseModel):
    """Event indicating the end of a timeline."""

    type_: Literal["end"] = "end"


class TimelineSessionEvent(BaseModel):
    """Abstract class for timeline events that are associated with a session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: UUID
    scene: Scene

    _serialize_scene = field_serializer("scene")(scene_serializer)


class TimelineEventSessionAct(TimelineSessionEvent):
    """Event indicating an character act in a session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["session_act"] = "session_act"
    character: Character
    content: str

    _character_serializer = field_serializer("character")(character_serializer)


class TimelineEventSessionStart(TimelineSessionEvent):
    """Event indicating the start of a session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["session_start"] = "session_start"
    session_id: UUID
    scene: Scene

    _serialize_scene = field_serializer("scene")(scene_serializer)


class TimelineEventSessionEnd(TimelineSessionEvent):
    """Event indicating the end of a session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type_: Literal["session_end"] = "session_end"
    session_id: UUID
    scene: Scene

    _serialize_scene = field_serializer("scene")(scene_serializer)


TimelineEvent: TypeAlias = Annotated[
    TimelineEventStart
    | TimelineEventEnd
    | TimelineEventSessionAct
    | TimelineEventSessionStart
    | TimelineEventSessionEnd,
    Field(discriminator="type_"),
]
