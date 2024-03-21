from typing_extensions import Self, override

from noneprompt import InputPrompt, CancelledError

from operagents.prop import Prop
from operagents.log import logger
from operagents.exception import OperaFinished
from operagents.config import UserBackendConfig

from ._base import Backend, Message


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
        self, messages: list[Message], props: list["Prop"] | None = None
    ) -> str:
        try:
            return await InputPrompt("You: ").prompt_async()
        except CancelledError:
            logger.info("User cancelled input.")
            raise OperaFinished() from None
