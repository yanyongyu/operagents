import weakref
from types import TracebackType
from typing import TYPE_CHECKING

from operagents.log import logger

from .event import TimelineEvent

if TYPE_CHECKING:
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

    # TODO
    async def scene_finished(self) -> bool:
        """Check if the current scene has finished."""
        return False

    # TODO
    async def next_scene(self) -> "Scene":
        """Get the next scene."""
        return self.current_scene

    async def next_time(self) -> None:
        """Go to the next character or scene."""
        await self.character_act()
        if await self.scene_finished():
            self._current_scene = await self.next_scene()
            self._current_character = await self.begin_character()
        else:
            self._current_character = await self.next_character()

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
        await logger.adebug("Timeline ends.")
        self._events = None
        self._current_scene = None
        self._current_character = None
