import weakref
from types import TracebackType
from typing import TYPE_CHECKING

from operagents.log import logger
from operagents.exception import TimelineNotStarted

from .event import TimelineEvent

if TYPE_CHECKING:
    from operagents.agent import Agent
    from operagents.opera import Opera
    from operagents.scene import Scene
    from operagents.character import Character


class Timeline:

    def __init__(self, opera: "Opera") -> None:
        self._opera_ref = weakref.ref(opera)

        self._events: list[TimelineEvent] | None = None
        self._current_scene: "Scene | None" = None
        self._current_character: "Character | None" = None

    @property
    def opera(self) -> "Opera":
        """The opera this timeline belongs to."""
        opera = self._opera_ref()
        if opera is None:
            raise RuntimeError("The opera this timeline belongs to has been destroyed.")
        return opera

    @property
    def events(self) -> list[TimelineEvent]:
        """The timeline's event history."""
        if self._events is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._events

    @property
    def current_scene(self) -> "Scene":
        """The current scene."""
        if self._current_scene is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._current_scene

    @property
    def current_character(self) -> "Character":
        """The current character."""
        if self._current_character is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._current_character

    @property
    def current_act_num(self) -> int:
        """The number of acts in the current scene."""
        return self.act_num_in_scene(self.current_scene)

    def scene_events(self, scene: "Scene") -> list[TimelineEvent]:
        """Get the events in the scene."""
        return [event for event in self.events if event.scene.name == scene.name]

    def act_num_in_scene(self, scene: "Scene") -> int:
        """Get the number of acts in the scene."""
        return sum(1 for event in self.scene_events(scene) if event.type_ == "act")

    def past_events(self, agent: "Agent") -> list[TimelineEvent]:
        """Get the events since the last time the agent acted in current scene."""
        return self.past_events_in_scene(agent, self.current_scene)

    def past_events_in_scene(
        self, agent: "Agent", scene: "Scene"
    ) -> list[TimelineEvent]:
        """Get the events since the last time the agent acted in the scene."""
        scene_events = [
            event for event in self.events if event.scene.name == scene.name
        ]
        for i in range(-1, -len(scene_events) - 1, -1):
            if scene_events[i].character.agent_name == agent.name:
                return scene_events[i + 1 :]
        return scene_events

    async def begin_character(self) -> "Character":
        """Get the first character to act in the scene."""
        return await self.current_scene.flow.begin(self)

    async def next_character(self) -> "Character":
        """Get the next character to act in the scene."""
        return await self.current_scene.flow.next(self)

    async def character_act(self) -> None:
        """Make the current character act in the scene."""
        event = await self.current_character.act(self)
        self.events.append(event)

    async def next_scene(self) -> "Scene | None":
        """Get the next scene."""
        return await self.current_scene.director.next_scene(self)

    async def prepare_scene(self) -> None:
        """Prepare the current scene."""
        await self.current_scene.prepare(self)

    async def next_time(self) -> None:
        """Go to the next character or scene."""
        logger.debug(
            "Current character {current_character.name} starts to act.",
            scene=self.current_scene,
            current_character=self.current_character,
        )
        await self.character_act()
        if next_scene := await self.next_scene():
            # change to next scene
            logger.info(
                "Next scene: {next_scene}",
                scene=self.current_scene,
                next_scene=next_scene,
            )
            self._current_scene = next_scene
            await self.prepare_scene()

            self._current_character = await self.begin_character()
        else:
            # continue current scene with next character
            self._current_character = await self.next_character()
            logger.debug(
                "Next character: {next_character.name}",
                scene=self.current_scene,
                next_character=self.current_character,
            )

    async def __aenter__(self) -> "Timeline":
        self._events = []

        self._current_scene = self.opera.scenes[self.opera.opening_scene]
        logger.debug(
            "Timeline starts with opening scene {opening_scene.name}.",
            opening_scene=self.current_scene,
        )
        await self.prepare_scene()

        self._current_character = await self.begin_character()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        logger.debug("Timeline ends.")
        self._events = None
        self._current_scene = None
        self._current_character = None
