from typing import TYPE_CHECKING
from typing_extensions import Self

from operagents import prop
from operagents.config import CharacterConfig

if TYPE_CHECKING:
    from operagents.prop import Prop
    from operagents.agent import Agent
    from operagents.timeline import Timeline
    from operagents.timeline.event import TimelineEventSessionAct


class Character:
    def __init__(
        self,
        name: str,
        description: str | None,
        agent_name: str,
        props: list["Prop"] | None = None,
    ):
        self.name: str = name
        """The name of the character."""
        self.description: str | None = description
        """The description of the character."""
        self.agent_name: str = agent_name
        """The name of the agent that acts as the character."""
        self.props: list["Prop"] = props or []
        """The props the character has."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, agent_name={self.agent_name!r}, props={self.props!r}"
            ")"
        )

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

    async def act(self, timeline: "Timeline") -> "TimelineEventSessionAct":
        agent = self.get_agent(timeline)
        return await agent.act(timeline)

    async def fake_act(
        self, timeline: "Timeline", response: str, do_observe: bool = True
    ) -> "TimelineEventSessionAct":
        agent = self.get_agent(timeline)
        return await agent.fake_act(timeline, response, do_observe=do_observe)
