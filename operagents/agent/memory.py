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

    a.k.a. Agent short time memory.
    """

    type_: Literal["observe"] = "observe"
    scene: "Scene"
    content: str


@dataclass(eq=False, kw_only=True)
class AgentEventSummary:
    """Summary of observed events for one whole scene.

    a.k.a. Agent long time memory.

    Note:
        The summary must come after the scene is finished.
        No more `observe` or `act` events will be added after the summary.
    """

    type_: Literal["scene_summary"] = "scene_summary"
    scene: "Scene"
    content: str


@dataclass(eq=False, kw_only=True)
class AgentEventAct:
    """Agent self acts."""

    type_: Literal["act"] = "act"
    scene: "Scene"
    character: "Character"
    content: str


AgentEvent: TypeAlias = Annotated[
    AgentEventObserve | AgentEventSummary | AgentEventAct, Field(discriminator="type_")
]


class AgentMemory:
    def __init__(self) -> None:
        self.memory: list[AgentEvent] = []
        """The memory of the agent."""

    def last_remembered_scene(self) -> "Scene | None":
        """Get the last remembered scene."""
        return self.memory[-1].scene if self.memory else None

    def need_summary_scenes(self) -> list["Scene"]:
        """Get the scenes that need a summary."""
        result: dict[str, "Scene"] = {}
        for event in self.memory:
            if event.type_ == "observe" or event.type_ == "act":
                result[event.scene.name] = event.scene
            elif event.type_ == "scene_summary":
                result.pop(event.scene.name, None)
        return list(result.values())

    def summarized(self, scene: "Scene") -> bool:
        return any(
            event.type_ == "scene_summary" and event.scene.name == scene.name
            for event in self.memory
        )

    def remember(self, event: AgentEvent) -> None:
        """Remember an agent event."""
        if (event.type_ == "observe" or event.type_ == "act") and self.summarized(
            event.scene
        ):
            raise SceneFinished()
        self.memory.append(event)

    def get_memory(self, timeline: "Timeline") -> list[AgentEvent]:
        """Get the agent memory for acting in the current scene."""

        result: list[AgentEvent] = []
        for event in self.memory:
            if event.type_ == "observe" or event.type_ == "act":
                if event.scene.name != timeline.current_scene.name:
                    # if the event is from past scene,
                    # ignore it and use the summary instead
                    continue
                result.append(event)
            elif event.type_ == "scene_summary":
                result.append(event)
        return result

    def get_memory_for_scene(self, scene: "Scene") -> list[AgentEvent]:
        """Get the agent memory for acting in the given scene."""
        return [event for event in self.memory if event.scene.name == scene.name]
