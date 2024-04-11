import asyncio
from typing import TYPE_CHECKING
from typing_extensions import Self

from operagents.config import SummaryHookConfig

from ._base import Hook

if TYPE_CHECKING:
    from operagents.timeline import Timeline
    from operagents.timeline.event import TimelineEventSessionEnd


class SummaryHook(Hook):
    type_ = "summary"

    def __init__(self, agent_names: list[str] | None) -> None:
        self.agent_names = agent_names

    @classmethod
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: SummaryHookConfig
    ) -> Self:
        return cls(agent_names=config.agent_names)

    async def on_timeline_session_end(
        self, timeline: "Timeline", event: "TimelineEventSessionEnd"
    ):
        agents = (
            timeline.opera.agents[character.agent_name]
            for character in event.scene.characters.values()
            if self.agent_names is None or character.agent_name in self.agent_names
        )
        await asyncio.gather(*(agent.summary(timeline, event) for agent in agents))
