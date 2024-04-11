import abc
from typing_extensions import Self
from typing import TYPE_CHECKING, ClassVar

from operagents.log import logger
from operagents.config import HookConfig

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.timeline.event import (
        TimelineEvent,
        TimelineEventEnd,
        TimelineEventStart,
        TimelineEventSessionAct,
        TimelineEventSessionEnd,
        TimelineEventSessionStart,
    )


class Hook(abc.ABC):
    type_: ClassVar[str]
    """The type of the hook."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: HookConfig) -> Self:
        """Create a hook from a configuration."""
        raise NotImplementedError

    async def invoke(self, timeline: "Timeline", event: "TimelineEvent") -> None:
        event_type = event.type_
        if handler := getattr(self, f"on_timeline_{event_type}", None):
            logger.debug(
                f"Invoking timeline hook {self.__class__.__name__}.{handler.__name__}"
            )
            try:
                await handler(timeline, event)
            except Exception:
                logger.opt(exception=True).warning(
                    "Running timeline hook "
                    f"{self.__class__.__name__}.{handler.__name__} failed."
                )

    if TYPE_CHECKING:

        async def on_timeline_start(
            self, timeline: "Timeline", event: "TimelineEventStart"
        ):
            """Called when the timeline is started."""
            pass

        async def on_timeline_end(
            self, timeline: "Timeline", event: "TimelineEventEnd"
        ):
            """Called when the timeline is ended."""
            pass

        async def on_timeline_session_start(
            self, timeline: "Timeline", event: "TimelineEventSessionStart"
        ):
            """Called when a session is started."""
            pass

        async def on_timeline_session_end(
            self, timeline: "Timeline", event: "TimelineEventSessionEnd"
        ):
            """Called when a session is ended."""
            pass

        async def on_timeline_session_act(
            self, timeline: "Timeline", event: "TimelineEventSessionAct"
        ):
            """Called when a character acts in a session."""
            pass
