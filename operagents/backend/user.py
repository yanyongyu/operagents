from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from typing_extensions import Self, override

from noneprompt import CancelledError, InputPrompt

from operagents.config import UserBackendConfig
from operagents.exception import OperaFinished
from operagents.log import logger
from operagents.prop import Prop

from ._base import Backend, GenerateResponse, Message

if TYPE_CHECKING:
    from operagents.timeline import Timeline


class UserBackend(Backend):
    type_ = "user"

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: UserBackendConfig
    ) -> Self:
        return cls()

    @override
    async def generate(
        self,
        timeline: "Timeline",
        messages: list[Message],
        props: list["Prop"] | None = None,
    ) -> AsyncGenerator[GenerateResponse, None]:
        try:
            yield GenerateResponse(content=await InputPrompt("You: ").prompt_async())
        except CancelledError:
            logger.info("User cancelled input.")
            raise OperaFinished() from None
