import asyncio
import weakref
from types import TracebackType
from typing import TYPE_CHECKING

from operagents.log import logger

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
            raise RuntimeError("The timeline has not been started.")
        return self._events

    @property
    def current_scene(self) -> "Scene":
        """The current scene."""
        if self._current_scene is None:
            raise RuntimeError("The timeline has not been started.")
        return self._current_scene

    @property
    def current_character(self) -> "Character":
        """The current character."""
        if self._current_character is None:
            raise RuntimeError("The timeline has not been started.")
        return self._current_character

    def past_events(self, agent: "Agent") -> list[TimelineEvent]:
        """Get the events since the last time the agent acted."""
        for i in range(-1, -len(self.events) - 1, -1):
            if self.events[i].character.agent_name == agent.name:
                return self.events[i + 1 :]
        return self.events.copy()

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

    async def next_time(self) -> None:
        """Go to the next character or scene."""
        await logger.adebug(
            f"Current character {self.current_character.name} starts to act."
        )
        await self.character_act()
        if next_scene := await self.next_scene():
            # change to next scene
            await logger.ainfo("Next scene", scene=next_scene)
            self._current_scene = next_scene
            self._current_character = await self.begin_character()
        else:
            # continue current scene with next character
            self._current_character = await self.next_character()
            await logger.adebug(f"Next character {self.current_character.name}.")

    async def __aenter__(self) -> "Timeline":
        self._events = []
        self._current_scene = self.opera.scenes[self.opera.opening_scene]
        self._current_character = await self.begin_character()
        await logger.adebug(
            f"Timeline starts with opening scene {self._current_scene.name}, "
            f"begin character {self._current_character.name}."
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await asyncio.shield(asyncio.create_task(logger.adebug("Timeline ends.")))
        self._events = None
        self._current_scene = None
        self._current_character = None
