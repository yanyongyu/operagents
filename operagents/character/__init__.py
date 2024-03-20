from typing import TYPE_CHECKING
from typing_extensions import Self
from dataclasses import field, dataclass

from operagents import prop
from operagents.config import CharacterConfig

if TYPE_CHECKING:
    from operagents.prop import Prop
    from operagents.agent import Agent
    from operagents.timeline import Timeline
    from operagents.timeline.event import TimelineEvent


@dataclass(eq=False)
class Character:
    name: str
    """The name of the character."""
    description: str | None
    """The description of the character."""
    agent_name: str
    """The name of the agent that acts as the character."""
    props: list["Prop"] = field(default_factory=list, kw_only=True)
    """The props the character has."""

    @classmethod
    def from_config(cls, name: str, config: CharacterConfig) -> Self:
        return cls(
            name=name,
            description=config.description,
            agent_name=config.agent_name,
            props=[prop.from_config(prop_config) for prop_config in config.props],
        )

    def get_agent(self, timeline: "Timeline") -> "Agent":
        return timeline.opera.agents[self.agent_name]

    async def act(self, timeline: "Timeline") -> "TimelineEvent":
        agent = self.get_agent(timeline)
        return await agent.act(timeline)

    async def fake_act(
        self, timeline: "Timeline", response: str, do_observe: bool = True
    ) -> "TimelineEvent":
        agent = self.get_agent(timeline)
        return await agent.fake_act(timeline, response, do_observe=do_observe)
