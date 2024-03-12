from dataclasses import dataclass
from typing_extensions import Self

from operagents.log import logger
from operagents.agent import Agent
from operagents.scene import Scene
from operagents.timeline import Timeline
from operagents.config import OperagentsConfig
from operagents.exception import OperaFinished


@dataclass(eq=False)
class Opera:
    agents: dict[str, Agent]
    scenes: dict[str, Scene]
    opening_scene: str

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
        )

    async def run(self):
        await logger.ainfo("Starting opera...")
        async with self.timeline:
            while True:
                try:
                    await self.timeline.next_time()
                except OperaFinished:
                    break
        await logger.ainfo("Opera finished.")
