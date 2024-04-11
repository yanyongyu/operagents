from typing import TypedDict
from dataclasses import dataclass
from typing_extensions import Self

from operagents import hook
from operagents.hook import Hook
from operagents.log import logger
from operagents.scene import Scene
from operagents.agent import Agent, AgentEvent
from operagents.config import OperagentsConfig
from operagents.exception import OperaFinished
from operagents.timeline import Timeline, TimelineEvent


class OperaResult(TypedDict):
    timeline_events: list[TimelineEvent]
    agent_memories: dict[str, list[AgentEvent]]


@dataclass(eq=False)
class Opera:
    agents: dict[str, Agent]
    scenes: dict[str, Scene]
    opening_scene: str
    hooks: list[Hook]

    def __post_init__(self):
        self.timeline = Timeline(opera=self)

    @classmethod
    def from_config(cls, config: OperagentsConfig) -> Self:
        return cls(
            agents={
                name: Agent.from_config(name, agent_config)
                for name, agent_config in config.agents.items()
            },
            scenes={
                name: Scene.from_config(name, scene_config)
                for name, scene_config in config.scenes.items()
            },
            opening_scene=config.opening_scene,
            hooks=[hook.from_config(hook_config) for hook_config in config.hooks],
        )

    async def run(self) -> OperaResult:
        logger.info("Starting opera...")
        async with self.timeline:
            try:
                while True:
                    try:
                        await self.timeline.next_time()
                    except OperaFinished:
                        break
            finally:
                timeline_events = self.timeline.events
                agent_memories = {
                    agent.name: agent.memory.events for agent in self.agents.values()
                }
        logger.info("Opera finished.")
        return OperaResult(
            timeline_events=timeline_events, agent_memories=agent_memories
        )
