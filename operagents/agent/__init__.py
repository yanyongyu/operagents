from typing import TYPE_CHECKING
from typing_extensions import Self
from dataclasses import field, dataclass

import structlog

from operagents import backend
from operagents.log import logger
from operagents.config import AgentConfig

if TYPE_CHECKING:
    from operagents.backend import Backend
    from operagents.timeline import Timeline
    from operagents.timeline.event import TimelineEvent


@dataclass(eq=False)
class Agent:
    name: str
    """The name of the agent."""
    # style: str
    backend: "Backend"
    """The backend to use for generating text."""

    # is_user: bool = field(default=False, kw_only=True)
    # """Whether the agent is controlled by a user."""
    think_history: list = field(default_factory=list, kw_only=True)
    """The history of the agent's thoughts."""

    def __post_init__(self):
        self.logger: structlog.stdlib.BoundLogger = logger.bind(agent=self)

    @classmethod
    def from_config(cls, name: str, config: AgentConfig) -> Self:
        """Create an agent from a configuration."""
        return cls(name=name, backend=backend.from_config(config.backend))

    # TODO
    async def act(self, timeline: "Timeline") -> "TimelineEvent":
        """Make the agent act."""
