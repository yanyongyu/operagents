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
from .event import (
    TimelineEventEnd,
    TimelineEventStart,
    TimelineSessionEvent,
    TimelineEventSessionAct,
    TimelineEventSessionEnd,
    TimelineEventSessionStart,
)

if TYPE_CHECKING:
    from operagents.agent import Agent
    from operagents.opera import Opera
    from operagents.scene import Scene
    from operagents.character import Character


@dataclass(eq=False, kw_only=True)
class SceneSession:
    """A session with a unique identifier indicating the current scene and character."""

    id_: UUID
    """Unique identifier for the session."""
    scene: "Scene"
    """Scene in the session."""
    character: "Character | None"
    """Character in the session."""


class Timeline:
    def __init__(self, opera: "Opera") -> None:
        self._opera_ref = weakref.ref(opera)

        self._events: list[TimelineEvent] | None = None
        self._exit_stack: AsyncExitStack | None = None

        self._current_session: SceneSession | None = None

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

    async def encounter_event(self, event: TimelineEvent) -> None:
        """Encounter an event."""
        self.events.append(event)
        # invoke hooks sequentially
        for hook in self.opera.hooks:
            await hook.invoke(self, event)

    @property
    def current_session(self) -> SceneSession:
        """The current session."""
        if self._current_session is None:
            raise TimelineNotStarted("The timeline has not been started.")
        return self._current_session

    @property
    def current_session_id(self) -> UUID:
        """The current session's ID."""
        return self.current_session.id_

    @property
    def current_scene(self) -> "Scene":
        """The current scene."""
        return self.current_session.scene

    @property
    def current_character(self) -> "Character":
        """The current character."""
        if (character := self.current_session.character) is None:
            raise SceneNotPrepared("The scene has not been prepared.")
        return character

    def session_events(self, session_id: UUID) -> list[TimelineEvent]:
        """Get the events in the scene session."""
        return [
            event
            for event in self.events
            if isinstance(event, TimelineSessionEvent)
            and event.session_id == session_id
        ]

    @property
    def current_events(self) -> list[TimelineEvent]:
        """The events in the current scene session."""
        return self.session_events(self.current_session_id)

    def session_act_num(self, session_id: UUID) -> int:
        """Get the number of acts in the scene session."""
        return sum(
            1
            for event in self.session_events(session_id)
            if isinstance(event, TimelineEventSessionAct)
        )

    @property
    def current_act_num(self) -> int:
        """The number of acts in the current scene session."""
        return self.session_act_num(self.current_session_id)

    def session_past_events(
        self, agent: "Agent", session_id: UUID
    ) -> list[TimelineEvent]:
        """Events since the last time the agent acted in the scene session."""
        session_events = self.session_events(session_id)
        for i in range(-1, -len(session_events) - 1, -1):
            if (
                isinstance(event := session_events[i], TimelineEventSessionAct)
                and event.character.agent_name == agent.name
            ):
                return session_events[i + 1 :]
        return session_events

    def past_events(self, agent: "Agent") -> list[TimelineEvent]:
        """Events since the last time the agent acted in current scene session."""
        return self.session_past_events(agent, self.current_session_id)

    async def _begin_character(self) -> "Character":
        """Get the first character to act in the scene."""
        return await self.current_scene.flow.begin(self)

    async def _next_character(self) -> "Character":
        """Get the next character to act in the scene."""
        return await self.current_scene.flow.next(self)

    async def _character_act(self) -> None:
        """Make the current character act in the scene."""
        event = await self.current_character.act(self)
        await self.encounter_event(event)

    async def _next_scene(self) -> "Scene | None":
        """Get the next scene."""
        return await self.current_scene.director.next_scene(self)

    async def _prepare_scene(self) -> None:
        """Prepare the current scene."""
        await self.current_scene.prepare(self)

    async def _switch_scene(self, scene: "Scene") -> None:
        """Switch to the specified scene session."""
        if self._current_session is not None:
            await self.encounter_event(
                TimelineEventSessionEnd(
                    session_id=self.current_session_id, scene=self.current_scene
                )
            )
        self._current_session = SceneSession(id_=uuid4(), scene=scene, character=None)
        await self.encounter_event(
            TimelineEventSessionStart(session_id=self.current_session_id, scene=scene)
        )
        await self._prepare_scene()

    async def _switch_character(self, character: "Character") -> None:
        """Switch to the specified character in the scene session."""
        self.current_session.character = character

    async def next_time(self) -> None:
        """Go to the next character or scene."""
        logger.debug(
            "Current character {current_character.name} starts to act.",
            scene=self.current_scene,
            current_character=self.current_character,
        )
        # OperationFinished may be raise here by props
        await self._character_act()
        # OperationFinished may be raise here by director
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

        await self.encounter_event(TimelineEventStart())

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
            try:
                await self.encounter_event(TimelineEventEnd())
            finally:
                if self._exit_stack is not None:
                    await self._exit_stack.aclose()
        finally:
            self._events = None
            self._exit_stack = None
            self._current_session = None
