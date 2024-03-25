import weakref
from uuid import UUID, uuid4
from types import TracebackType
from typing import TYPE_CHECKING
from dataclasses import dataclass
from typing_extensions import Self
from contextlib import AsyncExitStack

from operagents.log import logger
from operagents.exception import SceneNotPrepared, TimelineNotStarted

from .event import TimelineEvent as TimelineEvent
from .event import TimelineEventAct, TimelineEventSceneEnd, TimelineEventSceneStart

if TYPE_CHECKING:
    from operagents.agent import Agent
    from operagents.opera import Opera
    from operagents.scene import Scene
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class TimelineContext:
    id_: UUID
    """Unique identifier for the context."""
    scene: "Scene"
    """Scene in the context."""
    character: "Character | None"
    """Character in the context."""


class Timeline:

    def __init__(self, opera: "Opera") -> None:
        self._opera_ref = weakref.ref(opera)

        self._events: list[TimelineEvent] | None = None
        self._exit_stack: AsyncExitStack | None = None

        self._current_context: TimelineContext | None = None

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
    def current_context(self) -> TimelineContext:
        """The current context."""
        if self._current_context is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._current_context

    @property
    def current_context_id(self) -> UUID:
        """The current context's ID."""
        return self.current_context.id_

    @property
    def current_scene(self) -> "Scene":
        """The current scene."""
        return self.current_context.scene

    @property
    def current_character(self) -> "Character":
        """The current character."""
        if (character := self.current_context.character) is None:
            raise SceneNotPrepared("The scene has not been prepared.")
        return character

    @property
    def current_act_num(self) -> int:
        """The number of acts in the current scene context."""
        return self.act_num_in_context(self.current_context_id)

    def context_events(self, context_id: UUID) -> list[TimelineEvent]:
        """Get the events in the scene context."""
        return [event for event in self.events if event.context_id == context_id]

    def act_num_in_context(self, context_id: UUID) -> int:
        """Get the number of acts in the scene context."""
        return sum(
            1 for event in self.context_events(context_id) if event.type_ == "act"
        )

    def past_events(self, agent: "Agent") -> list[TimelineEvent]:
        """Events since the last time the agent acted in current scene context."""
        return self.past_events_in_context(agent, self.current_context_id)

    def past_events_in_context(
        self, agent: "Agent", context_id: UUID
    ) -> list[TimelineEvent]:
        """Events since the last time the agent acted in the scene context."""
        context_events = self.context_events(context_id)
        for i in range(-1, -len(context_events) - 1, -1):
            if (
                isinstance(event := context_events[i], TimelineEventAct)
                and event.character.agent_name == agent.name
            ):
                return context_events[i + 1 :]
        return context_events

    async def _begin_character(self) -> "Character":
        """Get the first character to act in the scene."""
        return await self.current_scene.flow.begin(self)

    async def _next_character(self) -> "Character":
        """Get the next character to act in the scene."""
        return await self.current_scene.flow.next(self)

    async def _character_act(self) -> None:
        """Make the current character act in the scene."""
        event = await self.current_character.act(self)
        self.events.append(event)

    async def _next_scene(self) -> "Scene | None":
        """Get the next scene."""
        return await self.current_scene.director.next_scene(self)

    async def _prepare_scene(self) -> None:
        """Prepare the current scene."""
        await self.current_scene.prepare(self)

    async def _switch_scene(self, scene: "Scene") -> None:
        """Switch to the specified scene context."""
        if self._current_context is not None:
            self.events.append(
                TimelineEventSceneEnd(
                    context_id=self.current_context_id, scene=self.current_scene
                )
            )
        self._current_context = TimelineContext(
            id_=uuid4(), scene=scene, character=None
        )
        self.events.append(
            TimelineEventSceneStart(context_id=self.current_context_id, scene=scene)
        )
        await self._prepare_scene()

    async def _switch_character(self, character: "Character") -> None:
        """Switch to the specified character in the scene context."""
        self.current_context.character = character

    async def next_time(self) -> None:
        """Go to the next character or scene."""
        logger.debug(
            "Current character {current_character.name} starts to act.",
            scene=self.current_scene,
            current_character=self.current_character,
        )
        await self._character_act()
        if next_scene := await self._next_scene():
            # change to next scene
            logger.info(
                "Next scene: {next_scene}.",
                scene=self.current_scene,
                next_scene=next_scene,
            )
            await self._switch_scene(next_scene)

            await self._switch_character(await self._begin_character())
        else:
            # continue current scene with next character
            await self._switch_character(await self._next_character())
            logger.debug(
                "Next character: {next_character.name}",
                scene=self.current_scene,
                next_character=self.current_character,
            )

    async def __aenter__(self) -> Self:
        self._events = []
        self._exit_stack = AsyncExitStack()

        for agent in self.opera.agents.values():
            await self._exit_stack.enter_async_context(agent)

        opening_scene = self.opera.scenes[self.opera.opening_scene]
        logger.debug(
            "Timeline starts with opening scene {opening_scene.name}.",
            opening_scene=opening_scene,
        )
        await self._switch_scene(opening_scene)
        await self._switch_character(await self._begin_character())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        logger.debug("Timeline ends.")

        try:
            if self._exit_stack is not None:
                await self._exit_stack.aclose()
        finally:
            self._events = None
            self._exit_stack = None
            self._current_scene = None
            self._current_character = None
