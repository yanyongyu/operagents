from pathlib import Path
from typing import TypedDict
from typing_extensions import Self

from operagents import hook
from operagents.hook import Hook
from operagents.log import logger
from operagents.agent import Agent
from operagents.scene import Scene
from operagents.timeline import Timeline
from operagents.utils import save_opera_state
from operagents.agent.memory import AgentEvent
from operagents.config import OperagentsConfig
from operagents.exception import OperaFinished
from operagents.timeline.event import TimelineEvent


class OperaState(TypedDict):
    timeline_events: list[TimelineEvent]
    agent_memories: dict[str, list[AgentEvent]]


class Opera:

    def __init__(
        self,
        agents: dict[str, Agent],
        scenes: dict[str, Scene],
        opening_scene: str,
        hooks: list[Hook],
    ):
        self.agents: dict[str, Agent] = agents
        self.scenes: dict[str, Scene] = scenes
        self.opening_scene: str = opening_scene
        self.hooks: list[Hook] = hooks

        self.timeline = Timeline(opera=self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"agents={self.agents}, scenes={self.scenes}, "
            f"opening_scene={self.opening_scene}, hooks={self.hooks}"
            ")"
        )

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

    @property
    def state(self) -> OperaState:
        return OperaState(
            timeline_events=self.timeline.events,
            agent_memories={
                agent.name: agent.memory.events for agent in self.agents.values()
            },
        )

    async def run(self) -> OperaState:
        logger.info("Starting opera...")
        async with self.timeline:
            try:
                while True:
                    try:
                        await self.timeline.next_time()
                    except OperaFinished:
                        break
            finally:
                # preserve state before closing
                state = self.state
        logger.info("Opera finished.")
        return state

    def save(self, path: Path):
        save_opera_state(self.state, path)
